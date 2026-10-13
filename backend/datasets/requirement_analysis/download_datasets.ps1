$ErrorActionPreference = 'Stop'

$base = Join-Path $PSScriptRoot 'backend\datasets\requirement_analysis'
$promise = Join-Path $base 'promise'
$promiseExp = Join-Path $base 'promise_exp'
$pure = Join-Path $base 'pure'
$humanGold = Join-Path $base 'human_gold'

New-Item -ItemType Directory -Force -Path $promise,$promiseExp,$pure,$humanGold | Out-Null

Write-Host 'Downloading original PROMISE NFR dataset...'
Invoke-WebRequest -Uri 'https://zenodo.org/records/268542/files/nfr.tar?download=1' -OutFile (Join-Path $promise 'nfr.tar')

Write-Host 'Downloading PROMISE_exp (969 labelled requirements)...'
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/AleksandarMitrevski/se-requirements-classification/master/0-datasets/PROMISE_exp/PROMISE_exp.arff' -OutFile (Join-Path $promiseExp 'PROMISE_exp.arff')

Write-Host 'Downloading PURE raw requirements documents...'
Invoke-WebRequest -Uri 'https://zenodo.org/records/7118517/files/requirements.zip?download=1' -OutFile (Join-Path $pure 'requirements.zip')

Write-Host 'Downloading PURE XML subset...'
Invoke-WebRequest -Uri 'https://zenodo.org/records/7118517/files/requirements-xml.zip?download=1' -OutFile (Join-Path $pure 'requirements-xml.zip')

Write-Host 'Downloading PURE XML schema...'
Invoke-WebRequest -Uri 'https://zenodo.org/records/7118517/files/req_document.xsd?download=1' -OutFile (Join-Path $pure 'req_document.xsd')

Write-Host ''
Write-Host 'Done. Dataset files are under:'
Write-Host $base
