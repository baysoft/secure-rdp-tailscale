#!/usr/bin/env python3
"""
RDP Hardening Tool - Prerequisites Test Script
Tests all requirements before running the main hardening script.
"""

import sys
import platform
import subprocess
import socket
import argparse

def check_python_version():
    """Check Python version compatibility"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 6:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.6+")
        return False

def check_pywinrm():
    """Check if pywinrm is installed"""
    print("Checking pywinrm installation...")
    try:
        import winrm
        print(f"✓ pywinrm {winrm.__version__} - OK")
        return True
    except ImportError:
        print("✗ pywinrm not found - Install with: pip install pywinrm")
        return False

def check_powershell_script(script_path):
    """Check if PowerShell script exists and is readable"""
    print(f"Checking PowerShell script: {script_path}")
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 100:  # Basic check for substantial content
                print(f"✓ PowerShell script found ({len(content)} characters)")
                return True
            else:
                print("✗ PowerShell script appears to be empty or too small")
                return False
    except FileNotFoundError:
        print(f"✗ PowerShell script not found: {script_path}")
        return False
    except Exception as e:
        print(f"✗ Error reading PowerShell script: {e}")
        return False

def check_network_connectivity(host):
    """Check basic network connectivity to target host"""
    print(f"Checking network connectivity to {host}...")
    try:
        # Try to resolve hostname
        ip = socket.gethostbyname(host)
        print(f"✓ DNS resolution: {host} -> {ip}")

        # Try ping (works on Windows)
        if platform.system() == "Windows":
            result = subprocess.run(['ping', '-n', '1', '-w', '2000', host],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ Ping successful")
                return True
            else:
                print("⚠ Ping failed - host may be unreachable or blocking ICMP")
                return True  # Don't fail on ping, just warn
        else:
            print("✓ Host resolution successful (ping check skipped on non-Windows)")
            return True

    except socket.gaierror:
        print(f"✗ DNS resolution failed for {host}")
        return False
    except subprocess.TimeoutExpired:
        print("⚠ Ping timeout - host may be slow to respond")
        return True
    except Exception as e:
        print(f"⚠ Network check error: {e}")
        return True

def check_winrm_port(host):
    """Check if WinRM port is open"""
    print(f"Checking WinRM port (5985) on {host}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, 5985))
        sock.close()

        if result == 0:
            print("✓ WinRM port 5985 is open")
            return True
        else:
            print("⚠ WinRM port 5985 is closed or filtered")
            print("  Make sure WinRM is enabled on the target server:")
            print("  winrm quickconfig")
            print("  winrm set winrm/config/service/auth '@{Basic=\"true\"}'")
            return False
    except Exception as e:
        print(f"⚠ Port check error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test prerequisites for RDP Hardening Tool')
    parser.add_argument('--host', required=True, help='Target Windows server hostname or IP')
    parser.add_argument('--script', default='harden_rdp.ps1', help='Path to PowerShell script')

    args = parser.parse_args()

    print("=== RDP Hardening Tool - Prerequisites Check ===\n")

    checks = [
        check_python_version,
        check_pywinrm,
        lambda: check_powershell_script(args.script),
        lambda: check_network_connectivity(args.host),
        lambda: check_winrm_port(args.host),
    ]

    passed = 0
    total = len(checks)

    for check in checks:
        if check():
            passed += 1
        print()

    print(f"=== Results: {passed}/{total} checks passed ===")

    if passed == total:
        print("🎉 All prerequisites met! Ready to run hardening script.")
        print(f"Run: python hardening.py --host {args.host} --password <your-password>")
        return 0
    elif passed >= total - 1:  # Allow one failure (usually WinRM port)
        print("⚠️ Most prerequisites met. Check warnings above before proceeding.")
        return 0
    else:
        print("❌ Critical prerequisites missing. Fix issues above before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())