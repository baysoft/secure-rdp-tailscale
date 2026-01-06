# RDP Hardening Tool

A comprehensive security solution for hardening Remote Desktop Protocol (RDP) access on Windows servers through automated configuration and Tailscale VPN integration.

## Overview

This tool automates the process of securing RDP access by:
- Installing and configuring Tailscale VPN for secure remote access
- Enabling RDP with Network Level Authentication (NLA)
- Changing the default RDP port (3389) to a custom port
- Configuring Windows Firewall to restrict RDP access to Tailscale interface only
- Verifying configuration and connectivity
- Providing machine-readable output for automation and monitoring

## Features

- **Automated Hardening**: One-click RDP security configuration
- **Tailscale Integration**: Secure VPN-based remote access
- **Port Customization**: Change RDP from default port 3389
- **Firewall Lockdown**: Restrict RDP to Tailscale interface only
- **Remote Execution**: Execute hardening via WinRM from any machine
- **Configuration Verification**: Comprehensive checks for Tailscale and RDP setup
- **Service Management**: Restart RDP service without full reboot
- **Status Monitoring**: Detailed success/failure reporting
- **Reboot Detection**: Identifies when system restart is required
- **Alpine Linux Support**: Optimized for running from Alpine Linux environments

## Prerequisites

### System Requirements
- Windows Server 2016 or later
- PowerShell 5.1 or higher
- Administrative privileges
- Internet access for Tailscale installation

### Dependencies
- Python 3.6+
- `pywinrm` package for remote execution
- WinRM enabled on target Windows server

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/baysoft/secure-rdp-tailscale.git
   cd secure-rdp-tailscale
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   pip install pywinrm
   ```

3. Test prerequisites (recommended):
   ```bash
   python test_prerequisites.py --host your-server-ip
   ```

4. Ensure WinRM is configured on your target Windows server:
   ```powershell
   # Run on target server as Administrator
   winrm quickconfig
   winrm set winrm/config/service/auth '@{Basic="true"}'
   winrm set winrm/config/service '@{AllowUnencrypted="true"}'
   ```

## Quick Start

Complete workflow from hardening to verification:

```bash
# 1. Harden the server
python hardening.py --host 192.168.1.100 --username Administrator --password YourPassword

# 2. If port isn't listening, restart RDP service
python restart_rdp.py --host 192.168.1.100 --username Administrator --password YourPassword

# 3. Verify everything is working
python verify.py --host 192.168.1.100 --username Administrator --password YourPassword --test-rdp

# 4. Connect via Tailscale
mstsc /v:100.x.x.x:3390
```

## Configuration

### Python Script Configuration (`hardening.py`)

Edit the configuration section at the top of `hardening.py`:

```python
# Target Windows server details
WINDOWS_HOST = "your-windows-server-ip"
USERNAME = "Administrator"
PASSWORD = "YourPassword"
```

### PowerShell Script Configuration (`harden_rdp.ps1`)

Modify the RDP port in `harden_rdp.ps1`:

```powershell
$NewRdpPort = 3390  # Change to your desired port
```

## Usage

### Basic Execution

1. Configure your connection details
2. Run the hardening script:
   ```bash
   python hardening.py --host your-server-ip --password YourAdminPassword
   ```

### Command Line Options

```
usage: hardening.py [-h] --host HOST [--username USERNAME] --password PASSWORD [--script SCRIPT]

RDP Hardening Tool - Secure RDP with Tailscale VPN

options:
  -h, --help           show this help message and exit
  --host HOST          Windows server hostname or IP (required)
  --username USERNAME  Administrator username (default: Administrator)
  --password PASSWORD  Administrator password (required)
  --script SCRIPT      Path to PowerShell script (default: harden_rdp.ps1)
```

### Example

```bash
python hardening.py --host 192.168.1.100 --username Administrator --password MySecurePass123
```

## Verification

After hardening, verify the configuration is working correctly:

### Configuration Verification

```bash
python verify.py --host 192.168.1.100 --username Administrator --password MySecurePass123
```

This checks:
- ✓ Tailscale installation and running status
- ✓ Tailscale IP address assignment
- ✓ RDP service enabled
- ✓ RDP port configuration (3390)
- ✓ Firewall rules (allow on Tailscale, block on public/private)
- ✓ Port listening status
- ✓ Network interface status

### With Client-Side RDP Test

```bash
python verify.py --host 192.168.1.100 --username Administrator --password MySecurePass123 --test-rdp
```

This additionally tests RDP connectivity from your client machine (requires Tailscale on client).

### Command Line Options

```
usage: verify.py [-h] --host HOST [--username USERNAME] --password PASSWORD [--script SCRIPT] [--test-rdp]

Verify RDP + Tailscale Configuration

options:
  -h, --help           show this help message and exit
  --host HOST          Windows server hostname or IP (required)
  --username USERNAME  Administrator username (default: Administrator)
  --password PASSWORD  Administrator password (required)
  --script SCRIPT      Path to PowerShell script (default: verify_rdp.ps1)
  --test-rdp           Test RDP connection from client (optional)
```

### Example Verification Output

```
===== TAILSCALE STATUS =====
[OK] Tailscale is installed
[OK] Tailscale is running
[OK] Tailscale IP: 100.127.251.35

===== RDP CONFIGURATION =====
[OK] RDP is enabled
[OK] RDP Port: 3390

===== FIREWALL RULES =====
[OK] Tailscale RDP allow rule exists
    Action: Allow, Enabled: True

===== PORT LISTENING =====
[OK] Port 3390 is listening

RESULT=SUCCESS
TAILSCALE_IP=100.127.251.35
RDP_PORT=3390
```

**Note**: The verification script checks for the Allow rule on Tailscale interface. Block rules are not needed as Windows Firewall's default behavior blocks all other interfaces.

## Service Management

If the RDP port isn't listening after hardening, restart the Terminal Services:

### Restart RDP Service (Without Reboot)

```bash
python restart_rdp.py --host 192.168.1.100 --username Administrator --password MySecurePass123
```

This restarts the Terminal Services to apply port changes without requiring a full system reboot.

### Command Line Options

```
usage: restart_rdp.py [-h] --host HOST [--username USERNAME] --password PASSWORD [--script SCRIPT]

Restart RDP Service

options:
  -h, --help           show this help message and exit
  --host HOST          Windows server hostname or IP (required)
  --username USERNAME  Administrator username (default: Administrator)
  --password PASSWORD  Administrator password (required)
  --script SCRIPT      Path to PowerShell script (default: restart_rdp.ps1)
```

**Note**: If the restart doesn't work, a full reboot may be required:

```bash
python -c "import winrm; s=winrm.Session('192.168.1.100', auth=('Administrator','YourPassword'), transport='ntlm', server_cert_validation='ignore'); s.run_cmd('shutdown /r /t 30')"
```

## Testing

Before running the hardening script in production, use the prerequisite test script to validate your environment:

### Prerequisites Test

```bash
python test_prerequisites.py --host your-server-ip
```

This script checks:
- Python version compatibility (3.6+)
- pywinrm package installation
- PowerShell script file existence
- Network connectivity to target server
- WinRM port accessibility (TCP 5985)

### Example Test Output

```
=== RDP Hardening Tool - Prerequisites Check ===

Checking Python version...
✓ Python 3.9.7 - OK

Checking pywinrm installation...
✓ pywinrm 0.4.3 - OK

Checking PowerShell script: harden_rdp.ps1
✓ PowerShell script found (15432 characters)

Checking network connectivity to 192.168.1.100...
✓ DNS resolution: 192.168.1.100 -> 192.168.1.100
✓ Ping successful

Checking WinRM port (5985) on 192.168.1.100...
✓ WinRM port 5985 is open

=== Results: 5/5 checks passed ===
🎉 All prerequisites met! Ready to run hardening script.
Run: python hardening.py --host 192.168.1.100 --password <your-password>
```

### Manual Testing Steps

1. **Test WinRM Configuration**:
   ```powershell
   # On target server
   winrm quickconfig
   winrm set winrm/config/service/auth '@{Basic="true"}'
   winrm set winrm/config/service '@{AllowUnencrypted="true"}'
   ```

2. **Test Connectivity**:
   ```bash
   # From your machine
   python -c "import winrm; s = winrm.Session('your-server-ip', auth=('Administrator', 'password')); print('Connection OK')"
   ```

3. **Dry Run Test**:
   ```bash
   # Test with invalid credentials (should fail gracefully)
   python hardening.py --host your-server-ip --password wrongpassword
   ```

The script will display:
- Real-time execution status
- Success/failure indicators for each hardening step
- Parsed results in machine-readable format
- Reboot requirements

### Sample Output

```
Executing remote hardening script...
=== RAW OUTPUT ===
[OK] Tailscale already installed
[OK] RDP enabled
[OK] NLA enabled
[OK] RDP port changed from 3389 to 3390
[OK] Firewall rules applied

===== SUMMARY =====
Tailscale: OK
RDP: OK
NLA: OK
Port: CHANGED
Firewall: OK
RebootRequired: True

===== MACHINE READABLE =====
RESULT=SUCCESS
PORT=3390
REBOOT_REQUIRED=1

=== PARSED RESULT ===
RESULT: SUCCESS
PORT: 3390
REBOOT_REQUIRED: 1

All good. Server hardened successfully.
```

## Security Benefits

- **VPN-Only Access**: RDP traffic only flows through encrypted Tailscale VPN
- **Non-Standard Port**: Reduces automated scanning attempts
- **NLA Enforcement**: Requires authentication before full RDP session
- **Interface-Specific Firewall**: RDP only allowed on Tailscale interface, all other interfaces implicitly blocked
- **Zero-Trust Model**: Access restricted to authorized Tailscale nodes
- **Simplified Rules**: Single Allow rule prevents conflicts and ensures reliable connectivity

## Post-Hardening Steps

1. **Service Restart**: If port isn't listening, run `restart_rdp.py` or reboot if `REBOOT_REQUIRED=1`
2. **Verify Configuration**: Run `verify.py` to confirm all settings are correct
3. **Tailscale Authentication**: Complete Tailscale login on the server if needed
4. **Client Configuration**: Connect to Tailscale network from client machines
5. **Test RDP Access**: Use `verify.py --test-rdp` to confirm connectivity
6. **Connect**: Use the Tailscale IP with `mstsc /v:100.x.x.x:3390`

## Troubleshooting

### Common Issues

- **WinRM Connection Failed**: Verify WinRM configuration and firewall rules
- **Tailscale Installation Failed**: Check internet connectivity and administrative privileges
- **Firewall Rules Not Applied**: Ensure Windows Firewall service is running
- **Port Change Failed**: Confirm no other services are using the target port
- **Port Not Listening**: Run `restart_rdp.py` to restart Terminal Services or reboot the server
- **Verification Fails**: Check Tailscale is running with `tailscale status` on the server
- **Can't Connect via Tailscale**: Ensure both client and server are authenticated to Tailscale network
  - Verify client shows server in `tailscale status`
  - Check `Test-NetConnection -ComputerName <tailscale-ip> -Port 3390` from client
  - Ensure using Tailscale IP (100.x.x.x), not public IP
- **Connection Times Out (Error 0x204)**: You're likely connecting to public IP instead of Tailscale IP, or client not on Tailscale network

### Debug Mode

Enable verbose output by modifying the PowerShell script's error handling sections.

## Technical Details

### Script Upload Method

The tool uses **Base64 encoding** to upload PowerShell scripts to the remote server, avoiding complex quote escaping issues that occur with line-by-line uploads. This ensures reliable script transmission over WinRM.

### PowerShell Compatibility

- **Minimum Version**: PowerShell 5.1 (included in Windows Server 2016+)
- **Compatibility Fix**: Ternary operators replaced with if-else statements for PS 5.1 compatibility
- **Error Handling**: Explicit error checking for each hardening step

### Firewall Strategy

The tool uses a **simplified, single-rule approach**:

- **Single Allow Rule**: Creates one firewall rule allowing RDP only on the Tailscale interface
- **No Block Rules**: Relies on Windows Firewall's default-deny behavior for other interfaces
- **Why This Works**: Interface-specific Allow rules are more reliable than combining Allow + Block rules
- **Security**: Port 3390 is only accessible via Tailscale; all other interfaces are implicitly blocked

**Previous Approach (Problematic)**: Earlier versions created both Allow and Block rules, but Windows Firewall's rule precedence caused Block rules to interfere with the Allow rule, preventing connections even through Tailscale.

**Current Approach (Optimal)**: Single Allow rule on Tailscale interface provides the same security with better reliability.

### Files Overview

| File | Purpose |
|------|---------|
| `hardening.py` | Main Python script for remote hardening execution |
| `harden_rdp.ps1` | PowerShell script that performs RDP hardening |
| `verify.py` | Python script for configuration verification |
| `verify_rdp.ps1` | PowerShell script that checks Tailscale and RDP status |
| `restart_rdp.py` | Python script to restart Terminal Services |
| `restart_rdp.ps1` | PowerShell script that restarts RDP service |
| `test_prerequisites.py` | Pre-flight checks for environment validation |

## Architecture

```
┌─────────────────┐    WinRM    ┌─────────────────┐
│  Client Machine │ ──────────► │ Windows Server  │
│  (Python Script)│             │ (PowerShell)    │
└─────────────────┘             └─────────────────┘
                                      │
                                      ▼
                               ┌─────────────────┐
                               │   Tailscale VPN │
                               │   + RDP Service │
                               └─────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool modifies system security settings. Use at your own risk and ensure you have proper backups before execution. Test in a non-production environment first.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review WinRM and Tailscale documentation