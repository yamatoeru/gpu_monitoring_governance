param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("install", "validate", "repair", "upgrade", "version")]
  [string]$Command
)

$env:PYTHONPATH = "C:\gpu-agent\pkg"
if (Test-Path "C:\Program Files\Python312\python.exe") {
  & "C:\Program Files\Python312\python.exe" -m gpu_agent.main $Command
} else {
  python -m gpu_agent.main $Command
}
