$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$workRoot = (Resolve-Path (Join-Path $projectRoot '..')).Path
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'node_modules/@aiot-toolkit/emulator'))) {
    $fallbackModules = Join-Path $workRoot 'starry-rw5/node_modules'
    if (-not (Test-Path -LiteralPath (Join-Path $fallbackModules '@aiot-toolkit/emulator'))) { throw 'Run npm install --ignore-scripts first' }
    $env:NODE_PATH = $fallbackModules
}
$env:STARRY_EMULATOR_HOME = Join-Path $workRoot 'eden-environment'
if (-not $env:WATCH_SDK_HOME) {
    $sharedSDK = Join-Path $workRoot 'vela-environment/sdk'
    $env:WATCH_SDK_HOME = if (Test-Path -LiteralPath $sharedSDK) { $sharedSDK } else { Join-Path $env:STARRY_EMULATOR_HOME 'sdk' }
}
$env:WATCH_VVD_NAME = 'EdenRW5-432x514'
$env:WATCH_SERIAL_PORT = '5580'
$env:WATCH_GRPC_PORT = '8580'
$env:WATCH_DEBUG_PORT = '10080'
$env:WATCH_CONTROL_PORT = '43140'
if (-not (Test-Path -LiteralPath (Join-Path $env:STARRY_EMULATOR_HOME 'vvd/EdenRW5-432x514.ini'))) {
    & node (Join-Path $PSScriptRoot 'setup-emulator.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Simulator setup failed' }
}
$controller = Start-Process -FilePath 'node' -ArgumentList 'tools/emulator-server.cjs' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $env:STARRY_EMULATOR_HOME 'controller-stdout.log') -RedirectStandardError (Join-Path $env:STARRY_EMULATOR_HOME 'controller-stderr.log')
Write-Output "Controller $($controller.Id), http://127.0.0.1:43140/"
