# ============================================
# VERIFY RDP + TAILSCALE CONFIGURATION
# ============================================

$Results = @{
    TailscaleRunning = $false
    TailscaleIP = ""
    RDPEnabled = $false
    RDPPort = 0
    FirewallTailscaleRule = $false
    FirewallBlockRule = $false
    PortListening = $false
}

Write-Output "===== TAILSCALE STATUS ====="

# Check if Tailscale is installed and running
$tailscalePath = "C:\Program Files\Tailscale\tailscale.exe"
if (Test-Path $tailscalePath) {
    Write-Output "[OK] Tailscale is installed"

    try {
        # Get Tailscale status
        $tsStatus = & $tailscalePath status --json 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Output "[OK] Tailscale is running"
            $Results.TailscaleRunning = $true

            # Parse JSON to get IP
            $statusObj = $tsStatus | ConvertFrom-Json
            if ($statusObj.Self.TailscaleIPs) {
                $Results.TailscaleIP = $statusObj.Self.TailscaleIPs[0]
                Write-Output "[OK] Tailscale IP: $($Results.TailscaleIP)"
            }
        } else {
            Write-Output "[FAIL] Tailscale is not running"
        }
    } catch {
        Write-Output "[FAIL] Failed to get Tailscale status: $($_.Exception.Message)"
    }
} else {
    Write-Output "[FAIL] Tailscale is not installed"
}

Write-Output ""
Write-Output "===== RDP CONFIGURATION ====="

# Check if RDP is enabled
try {
    $rdpEnabled = Get-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections"
    if ($rdpEnabled.fDenyTSConnections -eq 0) {
        Write-Output "[OK] RDP is enabled"
        $Results.RDPEnabled = $true
    } else {
        Write-Output "[FAIL] RDP is disabled"
    }
} catch {
    Write-Output "[FAIL] Could not check RDP status"
}

# Check RDP port
try {
    $rdpPort = (Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp").PortNumber
    $Results.RDPPort = $rdpPort
    Write-Output "[OK] RDP Port: $rdpPort"
} catch {
    Write-Output "[FAIL] Could not get RDP port"
}

Write-Output ""
Write-Output "===== FIREWALL RULES ====="

# Check Tailscale allow rule
try {
    $tsRule = Get-NetFirewallRule -DisplayName "RDP over Tailscale Only" -ErrorAction SilentlyContinue
    if ($tsRule) {
        Write-Output "[OK] Tailscale RDP allow rule exists"
        Write-Output "    Action: $($tsRule.Action), Enabled: $($tsRule.Enabled)"
        $Results.FirewallTailscaleRule = $true
    } else {
        Write-Output "[FAIL] Tailscale RDP allow rule not found"
    }
} catch {
    Write-Output "[FAIL] Could not check Tailscale firewall rule"
}

# Check block rule
try {
    $blockRule = Get-NetFirewallRule -DisplayName "Block RDP on Public/Private" -ErrorAction SilentlyContinue
    if ($blockRule) {
        Write-Output "[OK] RDP block rule exists"
        Write-Output "    Action: $($blockRule.Action), Enabled: $($blockRule.Enabled), Profile: $($blockRule.Profile)"
        $Results.FirewallBlockRule = $true
    } else {
        Write-Output "[FAIL] RDP block rule not found"
    }
} catch {
    Write-Output "[FAIL] Could not check block firewall rule"
}

Write-Output ""
Write-Output "===== PORT LISTENING ====="

# Check if RDP port is listening
try {
    $listening = Get-NetTCPConnection -LocalPort $Results.RDPPort -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Output "[OK] Port $($Results.RDPPort) is listening"
        $Results.PortListening = $true
    } else {
        Write-Output "[FAIL] Port $($Results.RDPPort) is not listening"
    }
} catch {
    Write-Output "[FAIL] Could not check listening ports"
}

Write-Output ""
Write-Output "===== NETWORK INTERFACES ====="

# Show Tailscale interface
try {
    Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Tailscale*" } | ForEach-Object {
        Write-Output "[INFO] Tailscale Interface: $($_.Name)"
        Write-Output "       Status: $($_.Status)"
        Write-Output "       Speed: $($_.LinkSpeed)"
    }
} catch {
    Write-Output "[WARN] Could not get network adapter info"
}

Write-Output ""
Write-Output "===== SUMMARY ====="
Write-Output "Tailscale Running: $($Results.TailscaleRunning)"
Write-Output "Tailscale IP: $($Results.TailscaleIP)"
Write-Output "RDP Enabled: $($Results.RDPEnabled)"
Write-Output "RDP Port: $($Results.RDPPort)"
Write-Output "Firewall Allow Rule: $($Results.FirewallTailscaleRule)"
Write-Output "Firewall Block Rule: $($Results.FirewallBlockRule)"
Write-Output "Port Listening: $($Results.PortListening)"

Write-Output ""
Write-Output "===== MACHINE READABLE ====="
$allGood = $Results.TailscaleRunning -and $Results.RDPEnabled -and $Results.FirewallTailscaleRule -and $Results.FirewallBlockRule -and $Results.PortListening
$result = if ($allGood) { 'SUCCESS' } else { 'FAIL' }
Write-Output "RESULT=$result"
Write-Output "TAILSCALE_IP=$($Results.TailscaleIP)"
Write-Output "RDP_PORT=$($Results.RDPPort)"
Write-Output "TAILSCALE_RUNNING=$($Results.TailscaleRunning)"
Write-Output "RDP_ENABLED=$($Results.RDPEnabled)"

exit 0
