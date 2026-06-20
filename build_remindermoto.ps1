Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

$rootExe = Join-Path $PSScriptRoot 'remindermoto.exe'
$legacyExe = Join-Path $PSScriptRoot 'remidnermoto.exe'
$buildDir = Join-Path $PSScriptRoot 'build'
$distDir = Join-Path $PSScriptRoot 'dist'

Remove-Item -Force $rootExe -ErrorAction SilentlyContinue
Remove-Item -Force $legacyExe -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $buildDir -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $distDir -ErrorAction SilentlyContinue

python -m PyInstaller --noconfirm --distpath $PSScriptRoot --workpath $buildDir remindermoto.spec
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Build complete: $rootExe"
