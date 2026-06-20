#Requires -Version 7
<#
.SYNOPSIS
    BrushlessDCMotor プロジェクトをビルドします。

.PARAMETER Config
    ビルド構成 (Release / Debug)。デフォルト: Release

.PARAMETER ToolchainFile
    vcpkg ツールチェーンファイルのパス。
    省略時は C:\vcpkg\scripts\buildsystems\vcpkg.cmake を使用します。

.PARAMETER Eigen3Dir
    vcpkg を使わない場合の Eigen3 CMake ディレクトリ。
    指定すると ToolchainFile より優先されます。

.PARAMETER Clean
    指定するとビルドディレクトリを削除してからビルドします。

.EXAMPLE
    .\build.ps1
    .\build.ps1 -Config Debug
    .\build.ps1 -Clean
    .\build.ps1 -Eigen3Dir "C:\eigen3\cmake"
#>
param(
    [ValidateSet("Release", "Debug")]
    [string]$Config = "Release",

    [string]$ToolchainFile = "C:\vcpkg\scripts\buildsystems\vcpkg.cmake",

    [string]$Eigen3Dir = "",

    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BuildDir    = Join-Path $ProjectRoot "build"

if ($Clean -and (Test-Path $BuildDir)) {
    Write-Host ">> ビルドディレクトリを削除します: $BuildDir"
    Remove-Item -Recurse -Force $BuildDir
}

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

Push-Location $BuildDir
try {
    Write-Host ">> CMake 構成 ($Config) ..."

    if ($Eigen3Dir -ne "") {
        cmake .. "-DEigen3_DIR=$Eigen3Dir" "-DVCPKG_APPLOCAL_DEPS=OFF"
    } elseif (Test-Path $ToolchainFile) {
        cmake .. "-DCMAKE_TOOLCHAIN_FILE=$ToolchainFile" "-DVCPKG_APPLOCAL_DEPS=OFF"
    } else {
        Write-Warning "vcpkg ツールチェーンが見つかりません: $ToolchainFile"
        Write-Warning "-Eigen3Dir オプションで Eigen3 のパスを指定してください。"
        cmake ..
    }

    if ($LASTEXITCODE -ne 0) { throw "CMake 構成に失敗しました。" }

    Write-Host ">> ビルド中 ($Config) ..."
    cmake --build . --config $Config

    if ($LASTEXITCODE -ne 0) { throw "ビルドに失敗しました。" }

    $ExePath = Join-Path $ProjectRoot "BrushlessDCMotor.exe"
    if (Test-Path $ExePath) {
        Write-Host ""
        Write-Host "ビルド成功: $ExePath" -ForegroundColor Green
    } else {
        Write-Warning "実行ファイルが見つかりません: $ExePath"
    }
} finally {
    Pop-Location
}
