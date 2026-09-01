param(
    [switch]$PythonOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    $venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        python -m venv (Join-Path $repoRoot '.venv')
    }
    & $venvPython -m pip install --disable-pip-version-check --upgrade pip setuptools
    & $venvPython -m pip install --disable-pip-version-check -e '.[dev]'
    & $venvPython -m ruff format --check python python_tests scripts
    & $venvPython -m ruff check python python_tests scripts
    & $venvPython -m mypy
    & $venvPython scripts/check_sil_traceability.py
    & $venvPython -m pytest --cov=tca_sil --cov-branch --cov-report=term-missing --cov-report=xml
    & $venvPython -m pip_audit --skip-editable

    if (-not $PythonOnly) {
        if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) {
            throw 'CMake/compiler unavailable. Re-run with -PythonOnly or use hosted CI.'
        }
        cmake -S . -B build -DTCA_WARNINGS_AS_ERRORS=ON
        cmake --build build --config Release --parallel
        ctest --test-dir build -C Release --output-on-failure
        $silLibrary = Join-Path $repoRoot 'build\Release\tca_sil.dll'
        if (-not (Test-Path -LiteralPath $silLibrary)) {
            $silLibrary = Join-Path $repoRoot 'build\tca_sil.dll'
        }
        $env:TCA_SIL_LIBRARY = $silLibrary
        $env:TCA_SIL_ARTIFACT_DIR = Join-Path $repoRoot 'artifacts\sil'
        & $venvPython -m robot --outputdir robot-output --xunit xunit.xml robot_tests
        & $venvPython scripts/validate_sil_evidence.py artifacts/sil
    }
}
finally {
    Pop-Location
}
