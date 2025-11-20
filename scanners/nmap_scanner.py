# scanners/nmap_scanner.py

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
import subprocess
from typing import Dict, List, Any


class NmapScanner:
    """
    Async Nmap wrapper.
    Produces normalized vulnerability-like objects for storage.
    """

    @staticmethod
    async def run_nmap(target: str, arguments: str = "-sV -T4 --open") -> Dict[str, Any]:
        """
        Runs nmap asynchronously and returns parsed results.
        """
        cmd = ["nmap"] + arguments.split() + ["-oX", "-", target]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if stderr and b"Failed" in stderr:
            raise RuntimeError(f"Nmap error: {stderr.decode()}")

        xml_output = stdout.decode()
        return NmapScanner.parse_xml(xml_output)

    @staticmethod
    def parse_xml(xml_data: str) -> Dict[str, Any]:
        """
        Parse Nmap XML and normalize results.
        Maps to:
        - open ports
        - detected services
        - simple vuln structure (banner vulnerabilities)
        """

        root = ET.fromstring(xml_data)

        scan_results = {
            "target": None,
            "host_status": "unknown",
            "ports": [],
            "vulnerabilities": []
        }

        for host in root.findall("host"):

            # host up/down status
            status = host.find("status")
            if status is not None:
                scan_results["host_status"] = status.get("state")

            # IP address
            address_tag = host.find("address")
            if address_tag is not None:
                scan_results["target"] = address_tag.get("addr")

            ports_tag = host.find("ports")
            if ports_tag is None:
                continue

            for port in ports_tag.findall("port"):
                port_id = port.get("portid")
                protocol = port.get("protocol")

                state_tag = port.find("state")
                service_tag = port.find("service")

                state = state_tag.get("state") if state_tag is not None else "unknown"
                service = service_tag.get("name") if service_tag is not None else "unknown"
                version = service_tag.get("version") if service_tag is not None else None

                port_record = {
                    "port": int(port_id),
                    "protocol": protocol,
                    "state": state,
                    "service": service,
                    "version": version,
                }

                scan_results["ports"].append(port_record)

                # --- SIMPLE BANNER VULN DETECTION ---
                # This is characteristically used for demo-VMs like Metasploitable
                if version:
                    if "vulnerable" in version.lower() or "old" in version.lower():
                        scan_results["vulnerabilities"].append({
                            "name": f"{service} outdated service",
                            "severity": "Medium",
                            "description": f"The service {service} on port {port_id} exposes an outdated version: {version}",
                            "evidence": version,
                            "port": int(port_id),
                            "protocol": protocol,
                        })

        return scan_results
