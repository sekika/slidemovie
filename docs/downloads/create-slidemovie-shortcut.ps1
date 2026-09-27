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
$launcherDirectory = Join-Path $env:LOCALAPPDATA "SlideMovie"
$launcherPath = Join-Path $launcherDirectory "SlideMovie.vbs"
New-Item -ItemType Directory -Path $launcherDirectory -Force | Out-Null

function ConvertTo-VbsString([string]$Value) {
    '"' + $Value.Replace('"', '""') + '"'
}

$command = '"' + $PythonPath + '" -m slidemovie.cli -g'
$vbsLines = @(
    'Set shell = CreateObject("WScript.Shell")',
    'Set environment = shell.Environment("Process")',
    ('environment.Item("PATH") = ' + (ConvertTo-VbsString $env:Path)),
    ('shell.CurrentDirectory = ' + (ConvertTo-VbsString $HOME)),
    ('shell.Run ' + (ConvertTo-VbsString $command) + ', 0, False')
)
Set-Content -LiteralPath $launcherPath -Value $vbsLines -Encoding Unicode

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:SystemRoot "System32\wscript.exe"
$shortcut.Arguments = '"' + $launcherPath + '"'
$shortcut.WorkingDirectory = $HOME
$shortcut.IconLocation = "$IconPath,0"
$shortcut.Description = "Open the SlideMovie GUI"
$shortcut.Save()

Write-Host "Created: $shortcutPath"
Write-Host "Launcher: $launcherPath"
