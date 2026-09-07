<#
.SYNOPSIS
    Collects network interface statistics from a remote server.
.DESCRIPTION
    Queries network adapter performance counters.
    Returns JSON with bytes/packets sent and received per second.
.PARAMETER ComputerName
    The hostname or IP of the target server.
.EXAMPLE
    .\get_network_stats.ps1 -ComputerName WS-PROD-01
.NOTES
    Demo Corp IT Operations - Acme Manufacturing
    Updated: 2026-09-07
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName
)

try {
    $adapters = Get-CimInstance -ClassName Win32_PerfFormattedData_Tcpip_NetworkInterface `
        -ComputerName $ComputerName |
        Select-Object -First 3

    $result = @()
    foreach ($adapter in $adapters) {
        $result += @{
            interface            = $adapter.Name
            bytes_sent_per_sec   = [long]$adapter.BytesSentPersec
            bytes_recv_per_sec   = [long]$adapter.BytesReceivedPersec
            packets_sent_per_sec = [long]$adapter.PacketsSentPersec
            packets_recv_per_sec = [long]$adapter.PacketsReceivedPersec
        }
    }

    @{ network = $result } | ConvertTo-Json -Compress -Depth 3
}
catch {
    Write-Error "Failed to collect network data from ${ComputerName}: $_"
    exit 1
}
