param(
    [string]$Python = "python",
    [switch]$InstallDependencies,
    [string]$DistPath = "dist"
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
    $IconPath = Join-Path $UiPath 'app.ico'
    $CoreDirectory = Join-Path $ProjectRoot 'build/core'
    & $Python -m PyInstaller --noconfirm --onefile --windowed --name rl-presence-core --icon $IconPath --distpath $CoreDirectory --workpath build/work --specpath build --hidden-import websockets.asyncio.client --add-data "${UiPath}:rocket_league_rpc/ui" run.py
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
    $CorePath = Join-Path $CoreDirectory 'rl-presence-core.exe'
    $CoreHash = (Get-FileHash -LiteralPath $CorePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $Version = (& $Python -c "from rocket_league_rpc import __version__; print(__version__)").Trim()
    $LauncherDirectory = Join-Path $ProjectRoot 'build/launcher'
    New-Item -ItemType Directory -Force -Path $LauncherDirectory | Out-Null
    $LauncherSource = Join-Path $LauncherDirectory 'windows_launcher.cs'
    (Get-Content -LiteralPath (Join-Path $ProjectRoot 'packaging/windows_launcher.cs') -Raw).Replace('@@CORE_SHA256@@',$CoreHash).Replace('@@VERSION@@',$Version) | Set-Content -LiteralPath $LauncherSource -Encoding UTF8
    $Compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if (-not (Test-Path -LiteralPath $Compiler)) { throw ".NET Framework 4.x C# compiler required" }
    $Destination = if ([IO.Path]::IsPathRooted($DistPath)) { $DistPath } else { Join-Path $ProjectRoot $DistPath }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    $Executable = Join-Path $Destination 'rl-presence.exe'
    & $Compiler /nologo /target:winexe /platform:x64 /optimize+ /reference:System.Windows.Forms.dll "/win32icon:$IconPath" "/resource:$CorePath,rl-presence-core" "/out:$Executable" $LauncherSource
    if ($LASTEXITCODE -ne 0) { throw "Windows launcher compilation failed" }
    Write-Output "Built: $Executable"
} finally {
    Pop-Location
}
