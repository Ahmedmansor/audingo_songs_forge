# Creates Windows desktop and project shortcuts for Audingo Songs Forge with custom logo icon
$WshShell = New-Object -ComObject WScript.Shell
$desktopPath = [Environment]::GetFolderPath("Desktop")
$projectDir = Split-Path -Parent $PSScriptRoot
if (-not $projectDir) { $projectDir = (Get-Item .).FullName }

$batPath = Join-Path $projectDir "launch_app.bat"
$icoPath = Join-Path $projectDir "assets\audingo_logo.ico"

# 1. Desktop shortcut
$desktopShortcut = $WshShell.CreateShortcut((Join-Path $desktopPath "Audingo Songs Forge.lnk"))
$desktopShortcut.TargetPath = $batPath
$desktopShortcut.WorkingDirectory = $projectDir
$desktopShortcut.IconLocation = "$icoPath,0"
$desktopShortcut.Description = "Launch Audingo Songs Forge Studio"
$desktopShortcut.Save()

# 2. Local project folder shortcut
$localShortcut = $WshShell.CreateShortcut((Join-Path $projectDir "Audingo Songs Forge.lnk"))
$localShortcut.TargetPath = $batPath
$localShortcut.WorkingDirectory = $projectDir
$localShortcut.IconLocation = "$icoPath,0"
$localShortcut.Description = "Launch Audingo Songs Forge Studio"
$localShortcut.Save()

Write-Host "Audingo Songs Forge shortcuts successfully created with custom logo!" -ForegroundColor Green
