$ErrorActionPreference = 'Stop'
$modRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vsRoot = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (!$vsRoot) { throw 'Visual Studio C++ x64 tools were not found.' }
$devcmd = Join-Path $vsRoot 'Common7/Tools/VsDevCmd.bat'
$buildRoot = Join-Path $modRoot 'tmp/native-displays'
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
$source = Join-Path $PSScriptRoot 'F117Displays.cpp'
$output = Join-Path $buildRoot 'F117Displays.dll'
Push-Location $buildRoot
try {
    $commandFile = Join-Path $buildRoot 'build.cmd'
    @"
@echo off
call "$devcmd" -no_logo -arch=x64
if errorlevel 1 exit /b %errorlevel%
cl.exe /nologo /LD /O2 /W4 /WX /std:c++17 /EHsc /MD "$source" /link bcrypt.lib /OUT:"$output"
if errorlevel 1 exit /b %errorlevel%
cl.exe /nologo /O2 /W4 /WX /std:c++17 /EHsc /MD "$PSScriptRoot/test_compositor.cpp" /link bcrypt.lib /OUT:"$buildRoot/test_compositor.exe"
if errorlevel 1 exit /b %errorlevel%
"$buildRoot/test_compositor.exe" "E:/Eagle Dynamics/DCS World/bin-mt/lua.dll" "$output"
exit /b %errorlevel%
"@ | Set-Content -LiteralPath $commandFile -Encoding ASCII
    & $env:ComSpec /d /c $commandFile
    if ($LASTEXITCODE -ne 0) { throw "Native compositor build failed ($LASTEXITCODE)." }
    Copy-Item -LiteralPath $output -Destination (Join-Path $modRoot 'bin/F117Displays.dll')
} finally { Pop-Location }
