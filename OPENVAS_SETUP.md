# OpenVAS Setup Guide for VulnTrack Pro

## What is OpenVAS?
OpenVAS (Open Vulnerability Assessment System) is an advanced vulnerability scanner that provides comprehensive security testing. It's **optional** for VulnTrack Pro - the application works fine with just Nmap scanning.

## Do I Need OpenVAS?
**No, it's optional!** VulnTrack Pro works perfectly with just Nmap for:
- Port scanning
- Service detection
- Basic vulnerability detection

OpenVAS adds:
- Deep vulnerability scanning
- CVE detection
- Compliance checking
- Detailed vulnerability reports

## Installing OpenVAS (Ubuntu/Debian)

### Option 1: Using GVM (Greenbone Vulnerability Manager)
```bash
# Add the repository
sudo add-apt-repository ppa:mrazavi/gvm
sudo apt update

# Install GVM
sudo apt install gvm

# Setup GVM
sudo gvm-setup

# Start the services
sudo gvm-start
```

### Option 2: Using Docker (Recommended for Development)
```bash
# Pull the Greenbone Community Edition container
docker pull greenbone/openvas-scanner

# Run OpenVAS container
docker run -d -p 9390:9390 --name openvas greenbone/openvas-scanner

# Wait for initialization (takes 5-10 minutes)
docker logs -f openvas
```

## Configuration

### 1. Create a `.env` file in the project root:
```bash
cd /home/vng370/Documents/coding/python/vulnhub
nano .env
```

### 2. Add OpenVAS credentials:
```env
# OpenVAS Configuration
OPENVAS_HOST=localhost
OPENVAS_PORT=9390
OPENVAS_USERNAME=admin
OPENVAS_PASSWORD=your_password_here

# Other settings
MAX_CONCURRENT_SCANS=3
SECRET_KEY=your-secret-key-here
```

### 3. Get your OpenVAS credentials:
```bash
# If using GVM
sudo gvm-cli --gmp-username admin --gmp-password admin socket --socketpath /run/gvmd/gvmd.sock --xml "<get_version/>"

# Default credentials are usually:
# Username: admin
# Password: admin (or set during gvm-setup)
```

## Testing the Connection

### Using the VulnTrack UI:
1. Navigate to http://localhost:5000
2. Click "New Scan"
3. Select "OpenVAS" as scan type
4. If configured correctly, you'll see scan configuration options

### Using curl:
```bash
curl http://localhost:5000/api/openvas/test-connection
```

## Troubleshooting

### "Failed to connect to OpenVAS"
This is **normal** if you haven't installed OpenVAS. The error just means:
- OpenVAS is not installed, OR
- OpenVAS is not running, OR
- Credentials in `.env` are incorrect

**Solution**: Either install OpenVAS following the steps above, or simply use Nmap scanning (which works without OpenVAS).

### OpenVAS service not starting:
```bash
# Check if OpenVAS is running
sudo systemctl status openvas-scanner
sudo systemctl status gvmd

# Restart services
sudo systemctl restart openvas-scanner
sudo systemctl restart gvmd
```

### Port already in use:
```bash
# Check what's using port 9390
sudo lsof -i :9390

# Kill the process if needed
sudo kill -9 <PID>
```

## Using VulnTrack Without OpenVAS

**You can use VulnTrack Pro perfectly fine without OpenVAS!**

Simply:
1. Ignore the OpenVAS connection error
2. Use "Nmap" as the scan type when creating scans
3. Nmap provides excellent port scanning and service detection

The OpenVAS option will simply be unavailable in the UI if it's not configured.

## Summary

- ✅ **OpenVAS is optional** - VulnTrack works great with just Nmap
- ✅ **No setup required** if you only want Nmap scanning
- ✅ **Easy to add later** if you want advanced vulnerability scanning
- ✅ **Docker option** makes installation easier for development

For most use cases, **Nmap scanning is sufficient**!
