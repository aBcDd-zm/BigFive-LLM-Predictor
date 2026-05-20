$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

$PythonBin = $env:PYTHON_BIN
if (-not $PythonBin) {
    $VenvPython = Join-Path $RepoRoot ".venv/Scripts/python.exe"
    if (Test-Path $VenvPython) {
        $PythonBin = $VenvPython
    } else {
        $PythonBin = "python"
    }
}

$RequestDir = "outputs/bfi_requests"
$RequestFile = Join-Path $RequestDir "request.jsonl"
$ResponseFile = "outputs/response.jsonl"
$OceanFile = "outputs/ocean_scores.csv"
$MetricsFile = "outputs/evaluation_metrics.csv"

New-Item -ItemType Directory -Force -Path "outputs" | Out-Null
New-Item -ItemType Directory -Force -Path $RequestDir | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue `
    $RequestFile, `
    (Join-Path $RequestDir "run.sh"), `
    $ResponseFile, `
    $OceanFile, `
    $MetricsFile

Write-Host "[1/4] Generating BFI requests..."
& $PythonBin src/generate_bfi_requests.py `
    --model_name kurileo/Gemma-2-2b-it-BFI-Anonymous `
    --source_path data/dialogues `
    --output_path $RequestDir

Write-Host "[2/4] Running mock inference..."
& $PythonBin src/run_local_inference.py `
    --backend mock `
    --requests_path $RequestFile `
    --output_path $ResponseFile

Write-Host "[3/4] Processing OCEAN scores..."
& $PythonBin src/process_results.py `
    --response_paths $ResponseFile `
    --output_path $OceanFile

Write-Host "[4/4] Evaluating metrics..."
& $PythonBin src/evaluate_ocean.py `
    --pred_path $OceanFile `
    --truth_path data/ground_truth.csv `
    --output_path $MetricsFile

Write-Host "Done. Generated:"
Write-Host "  $RequestFile"
Write-Host "  $ResponseFile"
Write-Host "  $OceanFile"
Write-Host "  $MetricsFile"
