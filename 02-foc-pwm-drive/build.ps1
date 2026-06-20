#Requires -Version 5.1
<#
.SYNOPSIS
    BrushlessDCMotor プロジェクトをビルドします。
.PARAMETER Generator
    CMake ジェネレータ。"VS2022"（デフォルト）または "Ninja"。
.PARAMETER Config
    ビルド構成。"Release"（デフォルト）または "Debug"。
.PARAMETER Eigen3Dir
    Eigen3Config.cmake があるディレクトリ（自動検出できない場合に指定）。
.PARAMETER Clean
    既存の build ディレクトリを削除してからビルドします。
.EXAMPLE
    .\build.ps1
    .\build.ps1 -Generator Ninja -Config Debug
    .\build.ps1 -Clean
    .\build.ps1 -Eigen3Dir "C:\vcpkg\installed\x64-windows\share\eigen3"
#>
param(
    [ValidateSet("VS2022", "Ninja")]
    [string]$Generator = "VS2022",

    [ValidateSet("Release", "Debug")]
    [string]$Config = "Release",

    [string]$Eigen3Dir = "",

    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BuildDir    = Join-Path $ProjectRoot "build"

Write-Host "=== BrushlessDCMotor Build ===" -ForegroundColor Cyan
Write-Host "Generator : $Generator"
Write-Host "Config    : $Config"
Write-Host "BuildDir  : $BuildDir"

if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host "既存の build ディレクトリを削除します..." -ForegroundColor Yellow
    Remove-Item $BuildDir -Recurse -Force
}

if (-not (Test-Path $BuildDir)) {
    New-Item $BuildDir -ItemType Directory | Out-Null
}

$cmakeArgs = @("..")

switch ($Generator) {
    "VS2022" {
        $cmakeArgs += @("-G", "Visual Studio 17 2022", "-A", "x64")
    }
    "Ninja" {
        $cmakeArgs += @("-G", "Ninja", "-DCMAKE_BUILD_TYPE=$Config")
    }
}

if ($Eigen3Dir -ne "") {
    $cmakeArgs += "-DEigen3_DIR=$Eigen3Dir"
}
$cmakeArgs += "-DVCPKG_APPLOCAL_DEPS=OFF"

Write-Host "`n[1/2] CMake configure..." -ForegroundColor Cyan
Push-Location $BuildDir
try {
    & cmake @cmakeArgs
    if ($LASTEXITCODE -ne 0) { throw "cmake configure failed (exit $LASTEXITCODE)" }

    Write-Host "`n[2/2] CMake build..." -ForegroundColor Cyan
    if ($Generator -eq "VS2022") {
        & cmake --build . --config $Config
    } else {
        & cmake --build .
    }
    if ($LASTEXITCODE -ne 0) { throw "cmake build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}

$Exe = Join-Path $ProjectRoot "BrushlessDCMotor.exe"
if (Test-Path $Exe) {
    Write-Host "`nビルド成功: $Exe" -ForegroundColor Green
} else {
    Write-Warning "実行ファイルが見つかりません: $Exe"
}
