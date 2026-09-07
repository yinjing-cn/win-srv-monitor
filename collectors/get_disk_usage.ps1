<#
.SYNOPSIS
    Collects disk usage from a remote Windows server.
.DESCRIPTION
    Queries logical disk information via WMI.
    Returns JSON with partition-level usage data.
.PARAMETER ComputerName
    The hostname or IP of the target server.
.EXAMPLE
    .\get_disk_usage.ps1 -ComputerName WS-DB-02
.NOTES
    Demo Corp IT Operations - Acme Manufacturing
    Updated: 2026-09-07
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ComputerName
)

try {
    $disks = Get-CimInstance -ClassName Win32_LogicalDisk -ComputerName $ComputerName |
        Where-Object { $_.DriveType -eq 3 }

    $result = @()
    foreach ($disk in $disks) {
        $totalGB = [math]::Round($disk.Size / 1GB, 1)
        $freeGB  = [math]::Round($disk.FreeSpace / 1GB, 1)
        $usedGB  = [math]::Round(($disk.Size - $disk.FreeSpace) / 1GB, 1)
        $pct     = if ($totalGB -gt 0) { [math]::Round(($totalGB - $freeGB) / $totalGB * 100, 1) } else { 0 }

        $result += @{
            letter        = $disk.DeviceID
            label         = $disk.VolumeName
            total_gb      = $totalGB
            used_gb       = $usedGB
            free_gb       = $freeGB
            usage_percent = $pct
        }
    }

    @{ disks = $result } | ConvertTo-Json -Compress -Depth 3
}
catch {
    Write-Error "Failed to collect disk data from ${ComputerName}: $_"
    exit 1
}
