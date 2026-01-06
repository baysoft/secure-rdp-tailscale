# ============================================
# HARDEN RDP + TAILSCALE ONLY ACCESS
# FULLY INSTRUMENTED VERSION WITH COMMENTS
# ============================================

# Pre-flight checks
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Output "ERROR: This script must be run as Administrator"
    exit 1
}

if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Output "ERROR: PowerShell 5.1 or higher required"
    exit 1
}

# Change this to your desired RDP port
$NewRdpPort = 3390

# Validate port number
if ($NewRdpPort -lt 1024 -or $NewRdpPort -gt 65535) {
    Write-Output "ERROR: Invalid RDP port number. Must be between 1024-65535"
    exit 1
}

# Check if port is already in use
$existingService = Get-NetTCPConnection -LocalPort $NewRdpPort -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Output "ERROR: Port $NewRdpPort is already in use"
    exit 1
}

# Track status for summary and automation
$Status = @{
    Tailscale = "UNKNOWN"
    RDP = "UNKNOWN"
    NLA = "UNKNOWN"
    Port = "UNKNOWN"
    Firewall = "UNKNOWN"
    RebootRequired = $false
}

# Helper function for consistent output formatting
function Report($msg, $ok) {
    if ($ok) {
        Write-Output "[OK] $msg"
    } else {
        Write-Output "[FAIL] $msg"
    }
}

# --------------------------------------------
# CHECK / INSTALL TAILSCALE
# --------------------------------------------
$tailscalePath = "C:\Program Files\Tailscale\tailscale.exe"

if (Test-Path $tailscalePath) {
    Report "Tailscale already installed" $true
    $Status.Tailscale = "OK"
} else {
    Report "Tailscale not found, installing..." $true
    try {
        $installer = "$env:TEMP\tailscale.msi"
        Invoke-WebRequest -Uri "https://pkgs.tailscale.com/stable/tailscale-setup-latest.msi" -OutFile $installer -ErrorAction Stop
        Start-Process msiexec.exe -ArgumentList "/i `"$installer`" /qn" -Wait
        $Status.Tailscale = "OK"
        Report "Tailscale installed successfully" $true
    } catch {
        $Status.Tailscale = "ERROR"
        Report "Failed to install Tailscale" $false
    }
}

# --------------------------------------------
# ENABLE RDP
# --------------------------------------------
try {
    # fDenyTSConnections = 0 means RDP enabled
    Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" `
        -Name "fDenyTSConnections" -Value 0
    $Status.RDP = "OK"
    Report "RDP enabled" $true
} catch {
    $Status.RDP = "ERROR"
    Report "Failed to enable RDP" $false
}

# --------------------------------------------
# ENABLE NETWORK LEVEL AUTHENTICATION (NLA)
# --------------------------------------------
try {
    Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
        -Name "UserAuthentication" -Value 1
    $Status.NLA = "OK"
    Report "NLA enabled" $true
} catch {
    $Status.NLA = "ERROR"
    Report "Failed to enable NLA" $false
}

# --------------------------------------------
# CHANGE RDP PORT
# --------------------------------------------
$currentPort = (Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp").PortNumber

if ($currentPort -ne $NewRdpPort) {
    try {
        Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
            -Name "PortNumber" -Value $NewRdpPort
        $Status.Port = "CHANGED"
        $Status.RebootRequired = $true
        Report "RDP port changed from $currentPort to $NewRdpPort" $true
    } catch {
        $Status.Port = "ERROR"
        Report "Failed to change RDP port" $false
    }
} else {
    $Status.Port = "UNCHANGED"
    Report "RDP port already set to $NewRdpPort" $true
}

# --------------------------------------------
# FIREWALL RULES
# --------------------------------------------
try {
    # Remove old rules to avoid duplicates
    Get-NetFirewallRule -DisplayName "*RDP over Tailscale*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    Get-NetFirewallRule -DisplayName "*Block RDP on Public/Private*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue

    # Allow RDP only on Tailscale interface
    New-NetFirewallRule `
        -DisplayName "RDP over Tailscale Only" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $NewRdpPort `
        -InterfaceAlias "Tailscale*" `
        -Action Allow

    # Block RDP everywhere else
    New-NetFirewallRule `
        -DisplayName "Block RDP on Public/Private" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $NewRdpPort `
        -Action Block `
        -Profile Public,Private

    $Status.Firewall = "OK"
    Report "Firewall rules applied" $true
} catch {
    $Status.Firewall = "ERROR"
    Report "Failed to apply firewall rules" $false
}

# --------------------------------------------
# SUMMARY OUTPUT
# --------------------------------------------
Write-Output ""
Write-Output "===== SUMMARY ====="
$Status.GetEnumerator() | ForEach-Object { Write-Output "$($_.Key): $($_.Value)" }

Write-Output ""
Write-Output "===== MACHINE READABLE ====="
# Check only string status values (exclude RebootRequired boolean)
$hasError = ($Status.Tailscale -eq 'ERROR') -or ($Status.RDP -eq 'ERROR') -or ($Status.NLA -eq 'ERROR') -or ($Status.Port -eq 'ERROR') -or ($Status.Firewall -eq 'ERROR')
$result = if ($hasError) { 'FAIL' } else { 'SUCCESS' }
Write-Output "RESULT=$result"
Write-Output "PORT=$NewRdpPort"
$rebootValue = if ($Status.RebootRequired) { 1 } else { 0 }
Write-Output "REBOOT_REQUIRED=$rebootValue"

exit 0