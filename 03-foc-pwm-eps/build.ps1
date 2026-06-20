#Requires -Version 5.1
<#
.SYNOPSIS
    CMake build script for BrushlessDCMotor / EpsGearboxSim.

.PARAMETER EigenPath
    Path to the Eigen3 installation directory. Default: C:/eigen-3.4.0

.PARAMETER Config
    Build configuration: Release or Debug. Default: Release

.PARAMETER Target
    Target to build: All, BrushlessDCMotor, or EpsGearboxSim. Default: All

.PARAMETER Clean
    Remove the build directory before configuring.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -EigenPath "C:/eigen-3.4.0" -Config Debug
    .\build.ps1 -Target EpsGearboxSim -Clean
#>
param(
    [string]$EigenPath = "C:/eigen-3.4.0",
    [ValidateSet("Release", "Debug")]
    [string]$Config = "Release",
    [ValidateSet("All", "BrushlessDCMotor", "EpsGearboxSim")]
    [string]$Target = "All",
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BuildDir    = Join-Path $ProjectRoot "build"

Write-Host "=== BrushlessDCMotor Build ===" -ForegroundColor Cyan
Write-Host "  Config    : $Config"
Write-Host "  Target    : $Target"
Write-Host "  EigenPath : $EigenPath"
Write-Host ""

# --- Clean ---
if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host "[clean] Removing $BuildDir ..." -ForegroundColor Yellow
    Remove-Item $BuildDir -Recurse -Force
}

# --- Configure ---
if (-not (Test-Path $BuildDir)) {
    Write-Host "[cmake] Configuring ..." -ForegroundColor Green
    cmake -S $ProjectRoot -B $BuildDir "-DCMAKE_PREFIX_PATH=$EigenPath" "-DVCPKG_APPLOCAL_DEPS=OFF"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "CMake configure failed (exit $LASTEXITCODE)."
    }
} else {
    Write-Host "[cmake] Build dir exists, skipping configure (use -Clean to reconfigure)." -ForegroundColor DarkGray
}

# --- Build ---
Write-Host ""
Write-Host "[cmake] Building ($Config) ..." -ForegroundColor Green

$BuildArgs = @("--build", $BuildDir, "--config", $Config)
if ($Target -ne "All") {
    $BuildArgs += @("--target", $Target)
}

cmake @BuildArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "CMake build failed (exit $LASTEXITCODE)."
}

Write-Host ""
Write-Host "[done] Build succeeded." -ForegroundColor Cyan

# Show produced executables
$Exes = Get-ChildItem $ProjectRoot -Filter "*.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "^(BrushlessDCMotor|EpsGearboxSim)" }
foreach ($exe in $Exes) {
    Write-Host "  -> $($exe.FullName)"
}
