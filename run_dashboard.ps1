$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONPATH = Join-Path $PSScriptRoot 'src'
py -3.10 -m streamlit run src/ma_deallab/ui/app.py
