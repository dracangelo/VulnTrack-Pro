# OpenVAS Configuration Fix

## Issues Found and Fixed

### 1. ✅ Code Issue - FIXED
**Problem**: The `openvas_scanner.py` file had duplicate `get_scan_configs()` methods. The second broken version was overriding the working one, causing empty results.

**Solution**: Removed the duplicate broken method. The code is now fixed.

### 2. ⚠️ Permission Issue - NEEDS YOUR ACTION
**Problem**: The GVM socket (`/var/run/gvmd/gvmd.sock`) is owned by the `_gvm` group, but your user is not in that group.

**Current socket permissions**:
```bash
srw-rw---- 1 _gvm _gvm 0 Nov 25 11:53 /var/run/gvmd/gvmd.sock
```

**Solution**: Add your user to the `_gvm` group by running:

```bash
sudo usermod -a -G _gvm $USER
```

**Important**: After running this command, you MUST log out and log back in (or reboot) for the group membership to take effect.

## Testing the Fix

After adding yourself to the `_gvm` group and logging back in:

### 1. Verify group membership:
```bash
groups
# You should see "_gvm" in the list
```

### 2. Test the connection:
```bash
curl http://localhost:5000/api/openvas/test-connection
```

Expected response:
```json
{
  "success": true,
  "message": "Connected to GVM successfully"
}
```

### 3. Fetch scan configurations:
```bash
curl http://localhost:5000/api/openvas/configs
```

Expected response (example):
```json
[
  {
    "id": "daba56c8-73ec-11df-a475-002264764cea",
    "name": "Full and fast"
  },
  {
    "id": "698f691e-7489-11df-9d8c-002264764cea",
    "name": "Full and fast ultimate"
  }
]
```

## Quick Fix Commands

Run these commands in order:

```bash
# 1. Add yourself to the _gvm group
sudo usermod -a -G _gvm $USER

# 2. Verify the command worked
getent group _gvm

# 3. Log out and log back in (or reboot)
# You can also try: newgrp _gvm (but a full logout is more reliable)

# 4. After logging back in, verify group membership
groups | grep _gvm

# 5. Test the connection
curl http://localhost:5000/api/openvas/test-connection

# 6. Fetch configs
curl http://localhost:5000/api/openvas/configs
```

## Alternative: Run Flask with sudo (NOT RECOMMENDED)

If you don't want to add yourself to the `_gvm` group, you could run the Flask app with sudo, but this is **not recommended** for security reasons:

```bash
# NOT RECOMMENDED - only for testing
sudo ./venv/bin/python run.py
```

## Summary

- ✅ **Code fixed**: Removed duplicate broken method
- ⚠️ **Action needed**: Add yourself to `_gvm` group and log out/in
- 🔄 **Server restarted**: Flask is running with the fixed code

Once you complete the permission fix, OpenVAS configs should load properly!
