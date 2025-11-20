# core/models.py
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Float,
    Enum,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

# Simple user model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class TargetGroup(Base):
    __tablename__ = "target_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    targets = relationship("Target", back_populates="group_obj")


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=True)
    address = Column(String(128), nullable=False, index=True)  # IP or hostname
    group_id = Column(Integer, ForeignKey("target_groups.id"), nullable=True)
    tags = Column(String(255), nullable=True)
    os_detected = Column(String(120), nullable=True)
    last_scanned = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group_obj = relationship("TargetGroup", back_populates="targets")
    scans = relationship("Scan", back_populates="target")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("target_groups.id"), nullable=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    scan_type = Column(String(50))  # nmap/openvas/custom
    status = Column(String(30), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    target = relationship("Target", back_populates="scans")
    results = relationship("VulnerabilityInstance", back_populates="scan")


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(Integer, primary_key=True)
    unique_key = Column(String(255), unique=True, index=True)  # CVE or engine+id
    name = Column(String(255))
    description = Column(Text)
    severity = Column(String(20))
    cvss_base = Column(Float, nullable=True)
    references = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    instances = relationship("VulnerabilityInstance", back_populates="vulnerability")


class VulnerabilityInstance(Base):
    __tablename__ = "vulnerability_instances"

    id = Column(Integer, primary_key=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    scan_id = Column(Integer, ForeignKey("scans.id"))
    port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    evidence = Column(Text, nullable=True)
    status = Column(String(30), default="open")  # open, in_progress, fixed, false_positive
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    vulnerability = relationship("Vulnerability", back_populates="instances")
    scan = relationship("Scan", back_populates="results")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    vuln_instance_id = Column(Integer, ForeignKey("vulnerability_instances.id"), nullable=True)
    external_id = Column(String(255), nullable=True)
    status = Column(String(30), default="open")
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
