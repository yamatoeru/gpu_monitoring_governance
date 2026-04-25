$ErrorActionPreference = "Stop"

$BaseDir = "C:\gpu-agent"
$BinDir = "$BaseDir\bin"
$PkgDir = "$BaseDir\pkg"
$StatusDir = "$BaseDir\status"
$TelegrafVersion = if ($env:TELEGRAF_VERSION) { $env:TELEGRAF_VERSION } else { "1.33.3" }
$TelegrafZipUrl = if ($env:TELEGRAF_ZIP_URL) { $env:TELEGRAF_ZIP_URL } else { "https://dl.influxdata.com/telegraf/releases/telegraf-${TelegrafVersion}_windows_amd64.zip" }
$TelegrafZipPath = "$env:TEMP\telegraf-$TelegrafVersion-x64.zip"
$TelegrafExtractDir = "$env:TEMP\telegraf-$TelegrafVersion-x64"
$TelegrafConfDir = "C:\Program Files\Telegraf\conf.d"
$TelegrafExe = "C:\Program Files\Telegraf\telegraf.exe"
$TelegrafForceVersion = if ($env:TELEGRAF_FORCE_VERSION) { $env:TELEGRAF_FORCE_VERSION } else { "false" }

function Get-TelegrafInstalledVersion {
  if (-not (Test-Path $TelegrafExe)) {
    return $null
  }
  $output = & $TelegrafExe version 2>$null
  if (-not $output) {
    return $null
  }
  if ($output -match 'Telegraf\s+([0-9.]+)') {
    return $Matches[1]
  }
  return $null
}

function Install-TelegrafZip {
  $ProgressPreference = "SilentlyContinue"
  Invoke-WebRequest -UseBasicParsing -Uri $TelegrafZipUrl -OutFile $TelegrafZipPath
  Remove-Item $TelegrafExtractDir -Recurse -Force -ErrorAction SilentlyContinue
  Expand-Archive -Path $TelegrafZipPath -DestinationPath $TelegrafExtractDir -Force
  $downloadedExe = Get-ChildItem $TelegrafExtractDir -Recurse -Filter telegraf.exe | Select-Object -First 1 -ExpandProperty FullName
  if (-not $downloadedExe) {
    throw "telegraf.exe not found in downloaded archive"
  }
  $downloadedDir = Split-Path $downloadedExe -Parent
  Remove-Item "C:\Program Files\Telegraf" -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path "C:\Program Files\Telegraf", $TelegrafConfDir | Out-Null
  Copy-Item -Path "$downloadedDir\*" -Destination "C:\Program Files\Telegraf" -Recurse -Force
  if (Get-Service -Name telegraf -ErrorAction SilentlyContinue) {
    Stop-Service telegraf -Force -ErrorAction SilentlyContinue
    sc.exe delete telegraf | Out-Null
    Start-Sleep -Seconds 2
  }
  & $TelegrafExe --config-directory $TelegrafConfDir --service-name telegraf service install --display-name telegraf --auto-restart | Out-Null
}

$TelegrafAction = "install"
$InstalledTelegrafVersion = Get-TelegrafInstalledVersion
$HasTelegrafService = $null -ne (Get-Service -Name telegraf -ErrorAction SilentlyContinue)
if ($HasTelegrafService -or $InstalledTelegrafVersion) {
  $TelegrafAction = "preserve"
  if (-not $InstalledTelegrafVersion) {
    Write-Warning "Detected Telegraf service without a valid Telegraf binary. Reinstalling target version $TelegrafVersion."
    $TelegrafAction = "replace"
    Install-TelegrafZip
  } elseif ($InstalledTelegrafVersion -ne $TelegrafVersion) {
    Write-Warning "Detected existing Telegraf version $InstalledTelegrafVersion (target $TelegrafVersion)."
    if ($TelegrafForceVersion -eq "true") {
      Write-Host "TELEGRAF_FORCE_VERSION=true, replacing installed Telegraf with $TelegrafVersion."
      $TelegrafAction = "replace"
      Install-TelegrafZip
    } else {
      Write-Warning "Preserving existing Telegraf. Set TELEGRAF_FORCE_VERSION=true to replace it."
    }
  }
} else {
  Install-TelegrafZip
}

New-Item -ItemType Directory -Force -Path $BaseDir, $BinDir, $PkgDir, $StatusDir, $TelegrafConfDir | Out-Null

Copy-Item ..\agent\gpu_agent "$PkgDir" -Recurse -Force
Copy-Item .\telegraf-gpu-agent.conf "$TelegrafConfDir\gpu-agent.conf" -Force

@"
@echo off
set PYTHONPATH=C:\gpu-agent\pkg
if exist "%ProgramFiles%\Python312\python.exe" (
  "%ProgramFiles%\Python312\python.exe" -m gpu_agent.main %*
) else (
  python -m gpu_agent.main %*
)
"@ | Out-File -Encoding ASCII "$BinDir\gpu-agent.cmd"

@"
GPU_AGENT_ENV_TYPE=vm
GPU_AGENT_CONFIG_VERSION=2026.04.23
GPU_AGENT_LATEST_VERSION_URL=http://repo.internal/gpu-agent/latest_version.json
# GPU_AGENT_INGEST_URL=http://ingest.internal:8080/events
# GPU_AGENT_INGEST_TOKEN=
"@ | Out-File -Encoding ASCII "$BaseDir\agent.env"

schtasks.exe /Create /SC MINUTE /MO 5 /TN "GPU-Agent-Validate" /TR "cmd.exe /c C:\gpu-agent\bin\gpu-agent.cmd validate" /RU SYSTEM /F | Out-Null
Set-Service -Name telegraf -StartupType Automatic
if ((Get-Service -Name telegraf).Status -eq "Running") {
  Restart-Service -Name telegraf -ErrorAction Stop
} else {
  Start-Service -Name telegraf -ErrorAction Stop
}
if ((Get-Service -Name telegraf).Status -ne "Running") {
  throw "Telegraf service is installed but not running after installation."
}

Write-Host "Installed. Next steps:"
if ($TelegrafAction -eq "preserve") {
  Write-Host "  - preserved existing telegraf installation"
} elseif ($TelegrafAction -eq "replace") {
  Write-Host "  - replaced telegraf with version $TelegrafVersion"
}
Write-Host "  1) Ensure Python 3.10+ is installed and in PATH"
Write-Host "  2) gpu-agent validate"
