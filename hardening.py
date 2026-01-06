import winrm
import re
import argparse
import sys
import os
import base64

def validate_config(host, username, password):
    """Validate configuration parameters"""
    if host == "your-windows-server-ip":
        print("ERROR: Please configure WINDOWS_HOST with your actual server IP/address")
        return False
    if username == "Administrator":
        print("WARNING: Using default username. Make sure this is correct for your server.")
    if password == "YourPassword":
        print("ERROR: Please configure PASSWORD with your actual password")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='RDP Hardening Tool - Secure RDP with Tailscale VPN')
    parser.add_argument('--host', required=True, help='Windows server hostname or IP')
    parser.add_argument('--username', default='Administrator', help='Administrator username')
    parser.add_argument('--password', required=True, help='Administrator password')
    parser.add_argument('--script', default='harden_rdp.ps1', help='Path to PowerShell script')

    args = parser.parse_args()

    # Validate configuration
    if not validate_config(args.host, args.username, args.password):
        sys.exit(1)

    # Check if PowerShell script exists
    if not os.path.isfile(args.script):
        print(f"ERROR: PowerShell script '{args.script}' not found")
        sys.exit(1)

    print(f"Connecting to {args.host} as {args.username}...")

    # ---------------------------------------------
    # CONNECT TO WINRM
    # ---------------------------------------------
    try:
        # NTLM transport works for most Windows Server 2016 setups
        session = winrm.Session(
            args.host,
            auth=(args.username, args.password),
            transport='ntlm',
            server_cert_validation='ignore'  # For self-signed certificates
        )
        print("Connected to WinRM successfully.")
    except Exception as e:
        print(f"Failed to connect to WinRM: {e}")
        print("Troubleshooting tips:")
        print("- Ensure WinRM is enabled: winrm quickconfig")
        print("- Check firewall: netsh advfirewall firewall add rule name='WinRM' dir=in action=allow protocol=TCP localport=5985")
        print("- Verify credentials and network connectivity")
        sys.exit(1)

    print("Executing remote hardening script...")

    # ---------------------------------------------
    # LOAD AND EXECUTE POWERSHELL SCRIPT REMOTELY
    # ---------------------------------------------
    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            ps_script = f.read()
    except Exception as e:
        print(f"Failed to read PowerShell script: {e}")
        sys.exit(1)

    # Upload the script to a temporary file on the remote machine
    remote_script_path = r'C:\Temp\hardening_script.ps1'
    try:
        # Create the temp directory if it doesn't exist
        session.run_cmd(f'powershell -Command "if (-not (Test-Path \'C:\\Temp\')) {{ New-Item -ItemType Directory -Path \'C:\\Temp\' }}"')

        # Encode the script as Base64 to avoid escaping issues
        script_bytes = ps_script.encode('utf-8')
        script_b64 = base64.b64encode(script_bytes).decode('ascii')

        # Decode Base64 on the remote machine and write to file
        decode_cmd = f'powershell -Command "[System.IO.File]::WriteAllBytes(\'{remote_script_path}\', [System.Convert]::FromBase64String(\'{script_b64}\'))"'
        session.run_cmd(decode_cmd)
    except Exception as e:
        print(f"Failed to upload PowerShell script to remote machine: {e}")
        sys.exit(1)

    try:
        # Execute the uploaded script
        result = session.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{remote_script_path}"')
    except Exception as e:
        print(f"Failed to execute PowerShell script remotely: {e}")
        sys.exit(1)

    stdout = result.std_out.decode('utf-8', errors='ignore')
    stderr = result.std_err.decode('utf-8', errors='ignore')

    print("\n=== RAW OUTPUT ===")
    print(stdout)

    if stderr.strip():
        print("=== ERRORS ===")
        print(stderr)

    # ---------------------------------------------
    # PARSE MACHINE-READABLE OUTPUT
    # ---------------------------------------------
    parsed = {}
    for line in stdout.splitlines():
        if "=" in line and line.count("=") == 1:
            key, val = line.split("=", 1)
            parsed[key.strip()] = val.strip()

    print("\n=== PARSED RESULT ===")
    for k, v in parsed.items():
        print(f"{k}: {v}")

    # ---------------------------------------------
    # VALIDATE RESULTS
    # ---------------------------------------------
    if not parsed:
        print("\nWARNING: No machine-readable output found. Check script execution.")
        sys.exit(1)

    result_status = parsed.get("RESULT")
    if result_status == "SUCCESS":
        print("\n[SUCCESS] All good. Server hardened successfully.")
        if parsed.get("REBOOT_REQUIRED") == "1":
            print("[WARNING] REBOOT REQUIRED: Please restart the server to apply port changes.")
    else:
        print("\n[FAILED] Some steps failed. Review the output above.")
        print("Common issues:")
        print("- Check internet connectivity for Tailscale download")
        print("- Verify administrative privileges")
        print("- Ensure Windows Firewall service is running")
        sys.exit(1)

if __name__ == "__main__":
    main()