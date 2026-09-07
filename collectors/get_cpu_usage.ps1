<#
.SYNOPSIS
    Collects CPU usage from a remote Windows server.
.DESCRIPTION
    Uses WMI/Performance Counters to gather CPU metrics.
    Returns JSON output suitable for the win-srv-monitor API.
.PARAMETER ComputerName
    The hostname or IP of the target server.
.EXAMPLE
    .\get_cpu_usage.ps1 -ComputerName WS-PROD-01
.NOTES
    Demo Corp IT Operations - Acme Manufacturing
    Updated: 2026-09-07
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName
)

try {
    # Query CPU usage via WMI
    $cpu = Get-CimInstance -ClassName Win32_Processor -ComputerName $ComputerName |
        Measure-Object -Property LoadPercentage -Average |
        Select-Object -ExpandProperty Average

    $cores = (Get-CimInstance -ClassName Win32_Processor -ComputerName $ComputerName).Count

    # Get load averages (approximated from current usage)
    $load1m  = [math]::Round($cpu / 100 * $cores * 0.95, 2)
    $load5m  = [math]::Round($cpu / 100 * $cores * 0.90, 2)
    $load15m = [math]::Round($cpu / 100 * $cores * 0.88, 2)

    $result = @{
        usage_percent = [math]::Round($cpu, 1)
        core_count    = $cores
        load_1m       = $load1m
        load_5m       = $load5m
        load_15m      = $load15m
    }

    $result | ConvertTo-Json -Compress
}
catch {
    Write-Error "Failed to collect CPU data from ${ComputerName}: $_"
    exit 1
}
