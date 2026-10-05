param(
    [string]$Python = "python",
    [switch]$InstallDependencies
)
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Push-Location $ProjectRoot
try {
    & $Python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
    if ($LASTEXITCODE -ne 0) { throw "Unsupported Python" }
    if ($InstallDependencies) {
        & $Python -m pip install -r requirements-dev.txt
        if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
    }
    $UiPath = Join-Path $ProjectRoot 'rocket_league_rpc/ui'
    & $Python -m PyInstaller --noconfirm --onefile --windowed --name rocket-league-rpc --distpath dist --workpath build/work --specpath build --hidden-import websockets.asyncio.client --add-data "${UiPath}:rocket_league_rpc/ui" run.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
    Write-Output "Built: $ProjectRoot\dist\rocket-league-rpc.exe"
} finally {
    Pop-Location
}
