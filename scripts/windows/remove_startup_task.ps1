# ============================================================================
# JARVIS v11.0 - Windows Task Scheduler Removal Script
# ============================================================================
# Removes the Task Scheduler task that auto-starts JARVIS on user logon
# ============================================================================

param(
    [string]$TaskName = "JARVIS Voice-First Assistant",
    [string]$LogFilePath = "C:/Users/AK/jarvis_project/logs/task_install.log",
    [switch]$Force
)

# ============================================================================
# Utility Functions
# ============================================================================

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"

    # Log directory is already created by install script
    if (Test-Path (Split-Path $LogFilePath -Parent)) {
        Add-Content -Path $LogFilePath -Value $logEntry
    }

    # Write to console
    switch ($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARN" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        default { Write-Host $logEntry -ForegroundColor Cyan }
    }
}

function Test-HaveAdminRights {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ============================================================================
# Main Script Execution
# ============================================================================

Write-Log "=== JARVIS Startup Task Removal Started ==="

# Check for admin rights
if (-not (Test-HaveAdminRights)) {
    Write-Log "WARNING: Script not running as Administrator. Task removal may fail." -Level "WARN"
}

# Check if task exists
Write-Log "Checking for task: $TaskName"
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $existingTask) {
    Write-Log "Task '$TaskName' does not exist. Nothing to remove." -Level "WARN"
    Write-Log "=== JARVIS Startup Task Removal Complete (No Action Needed) ===" -Level "SUCCESS"
    exit 0
}

Write-Log "Found existing task. Details:"
Write-Log "  Task Name: $($existingTask.TaskName)"
Write-Log "  State: $($existingTask.State)"
Write-Log "  Last Run Time: $($existingTask.LastRunTime)"
Write-Log "  Next Run Time: N/A (has not run yet)"

# Confirm before removal (unless -Force is specified)
if (-not $Force) {
    Write-Log ""
    Write-Log "WARNING: This will remove the scheduled task."
    Write-Log "Task: $TaskName"
    Write-Log ""
    $response = Read-Host "Do you want to continue? (Y/N)"

    if ($response -ne "Y" -and $response -ne "y") {
        Write-Log "Removal cancelled by user." -Level "WARN"
        exit 1
    }
}

# Stop the task if it's currently running
Write-Log "Stopping task if currently running..."
try {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Write-Log "Task stopped (if running)" -Level "SUCCESS"
}
catch {
    Write-Log "WARNING: Could not stop task: $_" -Level "WARN"
}

# Unregister the task
Write-Log "Removing scheduled task: $TaskName"
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false

    Write-Log "Task removed successfully" -Level "SUCCESS"

    # Verify removal
    $remainingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $remainingTask) {
        Write-Log "Verification: Task no longer exists" -Level "SUCCESS"
        Write-Log "=== JARVIS Startup Task Removal Complete ===" -Level "SUCCESS"
        exit 0
    }
    else {
        Write-Log "ERROR: Task still exists after removal attempt" -Level "ERROR"
        exit 1
    }
}
catch {
    Write-Log "ERROR: Failed to remove task: $_" -Level "ERROR"
    exit 1
}
