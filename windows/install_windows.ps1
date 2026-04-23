$ErrorActionPreference = "Stop"

$BaseDir = "C:\gpu-agent"
$BinDir = "$BaseDir\bin"
$PkgDir = "$BaseDir\pkg"
$StatusDir = "$BaseDir\status"
$TelegrafConfDir = "C:\Program Files\Telegraf\conf.d"

New-Item -ItemType Directory -Force -Path $BaseDir, $BinDir, $PkgDir, $StatusDir, $TelegrafConfDir | Out-Null

Copy-Item ..\agent\gpu_agent\main.py "$BinDir\gpu-agent.py" -Force
Copy-Item ..\agent\gpu_agent\* $PkgDir -Recurse -Force
Copy-Item .\telegraf-gpu-agent.conf "$TelegrafConfDir\gpu-agent.conf" -Force

@"
@echo off
set PYTHONPATH=C:\gpu-agent\pkg
python C:\gpu-agent\bin\gpu-agent.py %*
"@ | Out-File -Encoding ASCII "$BinDir\gpu-agent.cmd"

@"
GPU_AGENT_ENV_TYPE=vm
GPU_AGENT_CONFIG_VERSION=2026.04.23
GPU_AGENT_LATEST_VERSION_URL=http://repo.internal/gpu-agent/latest_version.json
# GPU_AGENT_INGEST_URL=http://ingest.internal:8080/events
# GPU_AGENT_INGEST_TOKEN=
"@ | Out-File -Encoding ASCII "$BaseDir\agent.env"

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\gpu-agent\bin\gpu-agent.cmd validate"
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$Trigger.Repetition = New-ScheduledTaskRepetitionSettings -Interval (New-TimeSpan -Minutes 5) -Duration (New-TimeSpan -Days 3650)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "GPU-Agent-Validate" -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null

Write-Host "Installed. Next steps:"
Write-Host "  1) Ensure Python 3.10+ is installed and in PATH"
Write-Host "  2) Ensure Telegraf service is installed and running"
Write-Host "  3) gpu-agent validate"
