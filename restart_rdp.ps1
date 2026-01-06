# ============================================
# RESTART TERMINAL SERVICES (RDP)
# ============================================

Write-Output "Restarting Terminal Services to apply port change..."

try {
    # Restart TermService
    Restart-Service -Name TermService -Force
    Write-Output "[OK] Terminal Services restarted successfully"

    # Wait a moment for service to start
    Start-Sleep -Seconds 3

    # Check if service is running
    $service = Get-Service -Name TermService
    if ($service.Status -eq 'Running') {
        Write-Output "[OK] Terminal Services is running"
    } else {
        Write-Output "[WARN] Terminal Services status: $($service.Status)"
    }

    # Verify port is now listening
    $rdpPort = (Get-ItemProperty "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp").PortNumber
    $listening = Get-NetTCPConnection -LocalPort $rdpPort -State Listen -ErrorAction SilentlyContinue

    if ($listening) {
        Write-Output "[OK] Port $rdpPort is now listening"
    } else {
        Write-Output "[WARN] Port $rdpPort is still not listening - reboot may be required"
    }

    Write-Output "RESULT=SUCCESS"
} catch {
    Write-Output "[FAIL] Failed to restart Terminal Services: $($_.Exception.Message)"
    Write-Output "RESULT=FAIL"
    exit 1
}

exit 0
