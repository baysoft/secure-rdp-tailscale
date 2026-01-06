import winrm
import argparse
import sys
import os
import base64

def main():
    parser = argparse.ArgumentParser(description='Restart RDP Service')
    parser.add_argument('--host', required=True, help='Windows server hostname or IP')
    parser.add_argument('--username', default='Administrator', help='Administrator username')
    parser.add_argument('--password', required=True, help='Administrator password')
    parser.add_argument('--script', default='restart_rdp.ps1', help='Path to restart PowerShell script')

    args = parser.parse_args()

    if not os.path.isfile(args.script):
        print(f"ERROR: PowerShell script '{args.script}' not found")
        sys.exit(1)

    print(f"Connecting to {args.host}...")

    try:
        session = winrm.Session(
            args.host,
            auth=(args.username, args.password),
            transport='ntlm',
            server_cert_validation='ignore'
        )
        print("Connected successfully.\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    try:
        with open(args.script, 'r', encoding='utf-8') as f:
            ps_script = f.read()
    except Exception as e:
        print(f"Failed to read script: {e}")
        sys.exit(1)

    remote_script_path = r'C:\Temp\restart_rdp.ps1'
    try:
        session.run_cmd(f'powershell -Command "if (-not (Test-Path \'C:\\Temp\')) {{ New-Item -ItemType Directory -Path \'C:\\Temp\' }}"')

        script_bytes = ps_script.encode('utf-8')
        script_b64 = base64.b64encode(script_bytes).decode('ascii')

        decode_cmd = f'powershell -Command "[System.IO.File]::WriteAllBytes(\'{remote_script_path}\', [System.Convert]::FromBase64String(\'{script_b64}\'))"'
        session.run_cmd(decode_cmd)
    except Exception as e:
        print(f"Failed to upload script: {e}")
        sys.exit(1)

    print("Restarting Terminal Services...\n")
    try:
        result = session.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{remote_script_path}"')
    except Exception as e:
        print(f"Failed to execute script: {e}")
        sys.exit(1)

    stdout = result.std_out.decode('utf-8', errors='ignore')
    stderr = result.std_err.decode('utf-8', errors='ignore')

    print(stdout)

    if stderr.strip():
        print("\n=== ERRORS ===")
        print(stderr)

    if "RESULT=SUCCESS" in stdout:
        print("\n[SUCCESS] RDP service restarted. Run verify.py again to confirm.")
    else:
        print("\n[FAILED] Could not restart RDP service. A reboot may be required.")
        sys.exit(1)

if __name__ == "__main__":
    main()
