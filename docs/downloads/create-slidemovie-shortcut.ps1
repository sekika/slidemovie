<#
Creates a desktop shortcut that launches the installed slidemovie GUI.
Run from PowerShell after saving this file and slidemovie.ico in the same folder.
If Python is not on PATH, supply -PythonPath with the full path to pythonw.exe.
#>
[CmdletBinding()]
param(
    [string]$PythonPath,
    [string]$ShortcutDirectory = [Environment]::GetFolderPath("Desktop"),
    [string]$IconPath = (Join-Path $PSScriptRoot "slidemovie.ico")
)

$ErrorActionPreference = "Stop"

if (-not $PythonPath) {
    $python = Get-Command python.exe -ErrorAction Stop
    $candidate = Join-Path (Split-Path -Parent $python.Source) "pythonw.exe"
    if (-not (Test-Path -LiteralPath $candidate)) {
        throw "pythonw.exe was not found. Run again with -PythonPath C:\\path\\to\\pythonw.exe."
    }
    $PythonPath = $candidate
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Python was not found: $PythonPath"
}
if (-not (Test-Path -LiteralPath $IconPath)) {
    throw "Icon was not found: $IconPath"
}
if (-not (Test-Path -LiteralPath $ShortcutDirectory)) {
    New-Item -ItemType Directory -Path $ShortcutDirectory | Out-Null
}

$shortcutPath = Join-Path $ShortcutDirectory "SlideMovie.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $PythonPath
$shortcut.Arguments = "-m slidemovie.cli -g"
$shortcut.WorkingDirectory = $HOME
$shortcut.IconLocation = "$IconPath,0"
$shortcut.Description = "Open the SlideMovie GUI"
$shortcut.Save()

Write-Host "Created: $shortcutPath"
