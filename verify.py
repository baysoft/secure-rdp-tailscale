import winrm
import argparse
import sys
import os
import base64
import socket

def test_rdp_connection(host, port):
    """Test if RDP port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"[WARN] Could not test RDP connection: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Verify RDP + Tailscale Configuration')
    parser.add_argument('--host', required=True, help='Windows server hostname or IP')
    parser.add_argument('--username', default='Administrator', help='Administrator username')
    parser.add_argument('--password', required=True, help='Administrator password')
    parser.add_argument('--script', default='verify_rdp.ps1', help='Path to verification PowerShell script')
    parser.add_argument('--test-rdp', action='store_true', help='Test RDP connection from client')

    args = parser.parse_args()

    # Check if PowerShell script exists
    if not os.path.isfile(args.script):
        print(f"ERROR: PowerShell script '{args.script}' not found")
        sys.exit(1)

    print(f"Connecting to {args.host} as {args.username}...")

    # Connect to WinRM
    try:
        session = winrm.Session(
            args.host,
            auth=(args.username, args.password),
            transport='ntlm',
            server_cert_validation='ignore'
        )
        print("Connected to WinRM successfully.\n")
    except Exception as e:
        print(f"Failed to connect to WinRM: {e}")
        sys.exit(1)

    # Load PowerShell script
    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            ps_script = f.read()
    except Exception as e:
        print(f"Failed to read PowerShell script: {e}")
        sys.exit(1)

    # Upload script to remote machine
    remote_script_path = r'C:\Temp\verify_rdp.ps1'
    try:
        # Create temp directory
        session.run_cmd(f'powershell -Command "if (-not (Test-Path \'C:\\Temp\')) {{ New-Item -ItemType Directory -Path \'C:\\Temp\' }}"')

        # Encode as Base64 to avoid escaping issues
        script_bytes = ps_script.encode('utf-8')
        script_b64 = base64.b64encode(script_bytes).decode('ascii')

        # Decode and write on remote machine
        decode_cmd = f'powershell -Command "[System.IO.File]::WriteAllBytes(\'{remote_script_path}\', [System.Convert]::FromBase64String(\'{script_b64}\'))"'
        session.run_cmd(decode_cmd)
    except Exception as e:
        print(f"Failed to upload verification script: {e}")
        sys.exit(1)

    # Execute verification script
    print("Running verification checks...\n")
    try:
        result = session.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{remote_script_path}"')
    except Exception as e:
        print(f"Failed to execute verification script: {e}")
        sys.exit(1)

    stdout = result.std_out.decode('utf-8', errors='ignore')
    stderr = result.std_err.decode('utf-8', errors='ignore')

    print(stdout)

    if stderr.strip():
        print("\n=== WARNINGS/ERRORS ===")
        print(stderr)

    # Parse machine-readable output
    parsed = {}
    for line in stdout.splitlines():
        if "=" in line and line.count("=") == 1:
            key, val = line.split("=", 1)
            parsed[key.strip()] = val.strip()

    # Test RDP connection from client if requested
    if args.test_rdp and parsed.get("TAILSCALE_IP"):
        tailscale_ip = parsed.get("TAILSCALE_IP")
        rdp_port = int(parsed.get("RDP_PORT", 3390))

        print(f"\n=== CLIENT-SIDE RDP TEST ===")
        print(f"Testing RDP connection to {tailscale_ip}:{rdp_port}...")

        if test_rdp_connection(tailscale_ip, rdp_port):
            print(f"[OK] RDP port {rdp_port} is accessible on Tailscale IP")
        else:
            print(f"[FAIL] Cannot connect to RDP port {rdp_port} on Tailscale IP")
            print("Make sure:")
            print("  - This client is connected to Tailscale")
            print("  - The server has rebooted if port was changed")

    # Final summary
    print("\n" + "="*50)
    result_status = parsed.get("RESULT")
    if result_status == "SUCCESS":
        print("[SUCCESS] All checks passed!")
        if parsed.get("TAILSCALE_IP"):
            print(f"\nConnect via RDP using:")
            print(f"  mstsc /v:{parsed.get('TAILSCALE_IP')}:{parsed.get('RDP_PORT')}")
    else:
        print("[FAILED] Some checks failed. Review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
