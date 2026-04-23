$ErrorActionPreference = "Stop"

$BaseDir = "C:\gpu-agent"
$BinDir = "$BaseDir\bin"
$PkgDir = "$BaseDir\pkg"
$StatusDir = "$BaseDir\status"
$TelegrafVersion = if ($env:TELEGRAF_VERSION) { $env:TELEGRAF_VERSION } else { "1.33.3" }
$TelegrafMsiUrl = if ($env:TELEGRAF_MSI_URL) { $env:TELEGRAF_MSI_URL } else { "https://dl.influxdata.com/telegraf/releases/telegraf-$TelegrafVersion_windows_amd64.msi" }
$TelegrafMsiPath = "$env:TEMP\telegraf-$TelegrafVersion-x64.msi"
$TelegrafConfDir = "C:\Program Files\Telegraf\conf.d"

if (-not (Get-Service -Name telegraf -ErrorAction SilentlyContinue)) {
  Invoke-WebRequest -UseBasicParsing -Uri $TelegrafMsiUrl -OutFile $TelegrafMsiPath
  Start-Process msiexec.exe -ArgumentList "/i `"$TelegrafMsiPath`" /qn" -Wait
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
Restart-Service -Name telegraf

Write-Host "Installed. Next steps:"
Write-Host "  1) Ensure Python 3.10+ is installed and in PATH"
Write-Host "  2) gpu-agent validate"
