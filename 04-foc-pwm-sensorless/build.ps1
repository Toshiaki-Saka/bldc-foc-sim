#Requires -Version 5.1
<#
.SYNOPSIS
    Build script for the BrushlessDCMotor simulator
.PARAMETER Config
    Build configuration (Debug / Release). Default: Release
.PARAMETER Clean
    Remove the existing build directory and perform a full rebuild
.EXAMPLE
    .\build.ps1
    .\build.ps1 -Config Debug
    .\build.ps1 -Clean
#>
param(
    [ValidateSet("Debug", "Release")]
    [string]$Config = "Release",
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root      = $PSScriptRoot
$BuildDir  = Join-Path $Root "build"
$CMakeExe  = "cmake"

Write-Host "=== BrushlessDCMotor Build ===" -ForegroundColor Cyan
Write-Host "Config   : $Config"
Write-Host "BuildDir : $BuildDir"

# --- Clean build ---
if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host "Removing build directory..." -ForegroundColor Yellow
    Remove-Item $BuildDir -Recurse -Force
}

# --- CMake configuration (only when the build directory does not exist) ---
if (-not (Test-Path (Join-Path $BuildDir "CMakeCache.txt"))) {
    Write-Host "`nConfiguring with CMake (Visual Studio 17 2022)..." -ForegroundColor Cyan
    & $CMakeExe -S $Root -B $BuildDir -G "Visual Studio 17 2022" -A x64 "-DVCPKG_APPLOCAL_DEPS=OFF"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "CMake configure failed (exit code $LASTEXITCODE)"
    }
}

# --- Build ---
Write-Host "`nBuilding ($Config)..." -ForegroundColor Cyan
& $CMakeExe --build $BuildDir --config $Config --parallel
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed (exit code $LASTEXITCODE)"
}

$Exe = Join-Path $Root "BrushlessDCMotor.exe"
if (Test-Path $Exe) {
    Write-Host "`nBuild succeeded: $Exe" -ForegroundColor Green
} else {
    Write-Error "Executable not found after build: $Exe"
}
