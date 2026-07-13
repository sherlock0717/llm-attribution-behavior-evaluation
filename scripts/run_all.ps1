<#
.SYNOPSIS
    Cross-platform mock run wrapper (FND-008) delegating to the package CLI.

.DESCRIPTION
    This is a thin wrapper over:

        python -m freewill_attribution.cli run

    It only supports explicit mock runs. It never enables a real API mode, never
    reads API keys, never copies research logic, and never writes the repository
    historical outputs/. By default it writes to a unique system-temp directory;
    an explicit -OutDir is forwarded and validated by the existing CLI /
    path_safety. It preserves the CLI exit code.

.EXAMPLE
    scripts\run_all.ps1 -Mock -NPerCell 1 -Seed 20260425 -OutDir C:\tmp\run

.EXAMPLE
    scripts\run_all.ps1 -Mock   # writes to a unique system-temp directory
#>
[CmdletBinding()]
param(
    [switch]$Mock,
    [string]$OutDir,
    [int]$NPerCell = 20,
    [int]$Seed = 20260425,
    [double]$Temperature = 1.0,
    [switch]$Fresh,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host "Usage: run_all.ps1 -Mock [-OutDir <path>] [-NPerCell <int>] [-Seed <int>] [-Temperature <float>] [-Fresh] [-Help]"
    Write-Host ""
    Write-Host "Runs a mock simulated study via 'python -m freewill_attribution.cli run'."
    Write-Host "Only mock runs are supported; no real API mode, no API key is read."
    Write-Host "Without -OutDir, a unique system-temp directory is used (never the repository outputs/)."
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  run_all.ps1 -Mock -NPerCell 1 -Seed 20260425 -OutDir C:\tmp\run"
    Write-Host "  run_all.ps1 -Mock"
    exit 0
}

# Capture the caller's working directory before any relocation.
$CallerCwd = (Get-Location).Path

if (-not $Mock) {
    [Console]::Error.WriteLine("error: -Mock is required (this wrapper only supports explicit mock runs).")
    exit 2
}

if ($NPerCell -lt 1) {
    [Console]::Error.WriteLine("error: -NPerCell must be >= 1.")
    exit 2
}

if ($Temperature -lt 0) {
    [Console]::Error.WriteLine("error: -Temperature must be >= 0.")
    exit 2
}

if (
    $PSBoundParameters.ContainsKey("OutDir") -and
    [string]::IsNullOrWhiteSpace($OutDir)
) {
    [Console]::Error.WriteLine(
        "error: -OutDir was provided but is empty."
    )
    exit 2
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# Locate uv without downloading or installing anything.
$UvExecutable = $null
$uvOnPath = Get-Command uv -ErrorAction SilentlyContinue
if ($uvOnPath) {
    $UvExecutable = $uvOnPath.Source
} else {
    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\uv.exe"),
        (Join-Path $RepoRoot ".venv/bin/uv")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { $UvExecutable = $candidate; break }
    }
}
if (-not $UvExecutable) {
    [Console]::Error.WriteLine("error: uv not found on PATH or in <repo>/.venv. Install uv manually; this wrapper will not download it.")
    exit 127
}

# Resolve the output directory relative to the caller's cwd (before relocation).
# An empty -OutDir was already rejected above, so ContainsKey alone is sufficient.
if ($PSBoundParameters.ContainsKey("OutDir")) {
    $expanded = [Environment]::ExpandEnvironmentVariables($OutDir)
    if ([System.IO.Path]::IsPathRooted($expanded)) {
        $ResolvedOut = [System.IO.Path]::GetFullPath($expanded)
    } else {
        $ResolvedOut = [System.IO.Path]::GetFullPath((Join-Path $CallerCwd $expanded))
    }
} else {
    $stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
    $guid = [guid]::NewGuid().ToString("N")
    $tempRoot = [System.IO.Path]::GetTempPath()
    $ResolvedOut = Join-Path (Join-Path $tempRoot "freewill-attribution") ("run-" + $stamp + "-" + $guid)
}

$Invariant = [Globalization.CultureInfo]::InvariantCulture
$NText = $NPerCell.ToString($Invariant)
$SeedText = $Seed.ToString($Invariant)
$TemperatureText = $Temperature.ToString($Invariant)

$UvArgs = @(
    "run",
    "--frozen",
    "python",
    "-m",
    "freewill_attribution.cli",
    "run",
    "--mock",
    "--n-per-cell",
    $NText,
    "--seed",
    $SeedText,
    "--temperature",
    $TemperatureText,
    "--out",
    $ResolvedOut
)
if ($Fresh) { $UvArgs += "--fresh" }

Write-Host "OUTPUT_DIR=$ResolvedOut"

Push-Location -LiteralPath $RepoRoot
try {
    & $UvExecutable @UvArgs
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $code
