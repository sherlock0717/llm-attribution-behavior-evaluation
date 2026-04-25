param(
    [int]$NPerCell = 20,
    [switch]$Mock,
    [switch]$Fresh
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    Write-Host "[1/5] Creating virtual environment..."
    python -m venv .venv
} else {
    Write-Host "[1/5] Virtual environment already exists."
}

Write-Host "[2/5] Activating environment and installing requirements..."
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host "[3/5] Validating synthetic materials..."
python .\src\validate_materials.py

Write-Host "[4/5] Running simulated study..."
$argsList = @(".\src\run_simulated_study.py", "--n-per-cell", "$NPerCell")
if ($Mock) {
    $argsList += "--mock"
}
if ($Fresh) {
    $argsList += "--fresh"
}
python @argsList

Write-Host "[5/5] Analyzing results..."
python .\src\analyze_results.py

Write-Host "Done. Check outputs/."
