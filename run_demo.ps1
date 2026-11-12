$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
py -3.10 -m ma_deallab.cli demo
exit $LASTEXITCODE
