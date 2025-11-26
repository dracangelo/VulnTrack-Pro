# OpenVAS Fix Instructions

It appears that the OpenVAS (GVM) service is **not running** on your system, which is why the scanner cannot connect.

Since I cannot run `sudo` commands on your behalf, you need to execute the following steps in your terminal:

## 1. Diagnose the Issue
Run the setup checker to identify any missing components or configuration errors:
```bash
sudo gvm-check-setup
```

## 2. Start the Service
If the check passes or tells you to start the service, run:
```bash
sudo gvm-start
```
*Note: It may take a minute for the service to fully start.*

## 3. Verify the Socket
Check if the socket file exists after starting the service:
```bash
ls -l /var/run/gvmd/gvmd.sock
```

## 4. Verify Permissions
You are already in the `_gvm` group, so once the socket exists, you should have access.
If you still get "Permission denied", try logging out and logging back in to refresh your group membership.

## 5. Test Connection
Once the service is running, you can test the connection via the API:
```bash
curl http://localhost:5000/api/openvas/test-connection
```

## Troubleshooting
If `gvm-start` fails, check the logs:
```bash
sudo tail -f /var/log/gvm/gvmd.log
```
