<#
.SYNOPSIS
    Collects Windows service status from a remote server.
.DESCRIPTION
    Queries service information via WMI.
    Returns JSON with service name, status, and start type.
.PARAMETER ComputerName
    The hostname or IP of the target server.
.EXAMPLE
    .\get_service_status.ps1 -ComputerName WS-WEB-03
.NOTES
    Demo Corp IT Operations - Acme Manufacturing
    Updated: 2026-09-07
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName
)

try {
    $services = Get-CimInstance -ClassName Win32_Service -ComputerName $ComputerName |
        Where-Object { $_.StartMode -ne 'Disabled' } |
        Select-Object -First 20

    $result = @()
    foreach ($svc in $services) {
        $result += @{
            name         = $svc.Name
            display_name = $svc.DisplayName
            status       = $svc.State
            start_type   = $svc.StartMode
        }
    }

    @{ services = $result } | ConvertTo-Json -Compress -Depth 3
}
catch {
    Write-Error "Failed to collect service data from ${ComputerName}: $_"
    exit 1
}
