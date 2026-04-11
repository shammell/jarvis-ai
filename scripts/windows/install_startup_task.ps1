# ============================================================================
# JARVIS v11.0 - Windows Task Scheduler Installation Script
# ============================================================================
# Creates a Task Scheduler task that triggers on user logon to auto-start JARVIS
# ============================================================================

param(
    [string]$TaskName = "JARVIS Voice-First Assistant",
    [string]$BatFilePath = "C:/Users/AK/jarvis_project/start_jarvis.bat",
    [string]$WorkingDirectory = "C:/Users/AK/jarvis_project/",
    [string]$LogFilePath = "C:/Users/AK/jarvis_project/logs/task_install.log"
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

    # Create logs directory if it doesn't exist
    $logDir = Split-Path $LogFilePath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    # Write to file
    Add-Content -Path $LogFilePath -Value $logEntry

    # Also write to console
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

Write-Log "=== JARVIS Startup Task Installation Started ==="

# Check for admin rights
if (-not (Test-HaveAdminRights)) {
    Write-Log "WARNING: Script not running as Administrator. Task creation may fail." -Level "WARN"
}

# Validate batch file exists
if (-not (Test-Path $BatFilePath)) {
    Write-Log "ERROR: Batch file not found at $BatFilePath" -Level "ERROR"
    exit 1
}
Write-Log "Batch file verified: $BatFilePath"

# Validate working directory
if (-not (Test-Path $WorkingDirectory)) {
    Write-Log "ERROR: Working directory not found at $WorkingDirectory" -Level "ERROR"
    exit 1
}
Write-Log "Working directory verified: $WorkingDirectory"

# Check for existing task and remove it (idempotency)
Write-Log "Checking for existing task: $TaskName"
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Log "Found existing task '$TaskName'. Removing it first..." -Level "WARN"
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Log "Existing task removed successfully" -Level "SUCCESS"
    }
    catch {
        Write-Log "WARNING: Could not remove existing task: $_" -Level "WARN"
    }
}

# Define trigger - User logon (not pre-login)
Write-Log "Creating logon trigger..."
$trigger = New-ScheduledTaskTrigger -AtLogOn

# Add a small delay to ensure user profile is fully loaded
$delayTrigger = New-ScheduledTaskTrigger -AtLogOn -DelayedExecutionTimeSpan ([TimeSpan]::FromSeconds(15))

# Define action
Write-Log "Configuring task action..."
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -Command `"$BatFilePath`"" -WorkingDirectory $WorkingDirectory

# Define principal - Run as currently logged-in user with highest privileges
Write-Log "Configuring task principal..."
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest

# Define settings
Write-Log "Configuring task settings..."
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartIntervalMinute 5 `
    -ExecutionTimeLimit (New-TimeSpan -Hours 24)

# Register the new task
Write-Log "Registering scheduled task: $TaskName"
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Trigger $delayTrigger `
        -Action $action `
        -Principal $principal `
        -Settings $settings `
        -Description "JARVIS Voice-First Assistant - Auto-starts on user logon" `
        -Force

    Write-Log "Task created successfully: $TaskName" -Level "SUCCESS"

    # Verify the task was created
    $newTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Write-Log "Task verification:" -Level "SUCCESS"
    Write-Log "  Task Name: $($newTask.TaskName)"
    Write-Log "  State: $($newTask.State)"
    Write-Log "  Last Run Time: $($newTask.LastRunTime)"
    Write-Log "  Next Run Time: N/A (has not run yet)"

    # Get task details
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Log "  Created: $($taskInfo.CreationTime)"
    Write-Log "  Last Modification: $($taskInfo.LastModificationTime)"

    Write-Log "=== JARVIS Startup Task Installation Complete ===" -Level "SUCCESS"
    Write-Log ""
    Write-Log "Summary:"
    Write-Log "  - Task Name: $TaskName"
    Write-Log "  - Trigger: User Logon (15 second delay)"
    Write-Log "  - Action: $BatFilePath"
    Write-Log "  - Working Directory: $WorkingDirectory"
    Write-Log "  - Run Level: Highest Privileges"
    Write-Log ""
    Write-Log "The task will run automatically the next time you log on."
    Write-Log "To test manually: schtasks /run /tn `"$TaskName`""

    exit 0
}
catch {
    Write-Log "ERROR: Failed to create task: $_" -Level "ERROR"
    exit 1
}
