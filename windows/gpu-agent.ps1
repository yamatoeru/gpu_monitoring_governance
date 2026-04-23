param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("install", "validate", "repair", "upgrade", "version")]
  [string]$Command
)

$env:PYTHONPATH = "C:\gpu-agent\pkg"
python C:\gpu-agent\bin\gpu-agent.py $Command
