$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$workRoot = (Resolve-Path (Join-Path $projectRoot '..')).Path
$environmentRoot = Join-Path $workRoot 'eden-environment'
$recordPath = Join-Path $environmentRoot 'controller-pid.json'
if (Test-Path -LiteralPath $recordPath) {
    $record = Get-Content -LiteralPath $recordPath | ConvertFrom-Json
    if ($record.script -notmatch '[\\/]work[\\/]eden-rw5[\\/]tools[\\/]emulator-server\.cjs$') { throw 'Unexpected controller owner' }
    $controllerProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)"
    if ($controllerProcess) {
        if ($controllerProcess.Name -ne 'node.exe' -or $controllerProcess.CommandLine -notlike '*tools/emulator-server.cjs*') { throw 'Unexpected process identity' }
        $emulatorProcesses = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($record.pid)" | Where-Object { $_.Name -eq 'emulator.exe' }
        foreach ($emulatorProcess in $emulatorProcesses) {
            if ($emulatorProcess.CommandLine -notlike '*EdenRW5-432x514*') { throw 'Unexpected virtual device identity' }
            Get-CimInstance Win32_Process -Filter "ParentProcessId = $($emulatorProcess.ProcessId)" | Where-Object { $_.Name -like 'qemu-*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
            Stop-Process -Id $emulatorProcess.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Stop-Process -Id $record.pid -Force -ErrorAction SilentlyContinue
    }
}
& (Join-Path $PSScriptRoot 'start-emulator.ps1')
