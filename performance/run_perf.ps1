# mall 商城性能测试 — 一键运行脚本 (PowerShell)
# 用法：.\performance\run_perf.ps1 [场景] [用户类]
# 场景: quick | load | stress | stability | readonly
# 用户类: MallAdminUser | BusinessChainUser | SpikeUser (可选)

param(
    [string]$Scenario = "quick",
    [string]$UserClass = ""
)

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReportDir = "$BaseDir\report"
$HostUrl = "http://localhost:8080"

if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
}

# 根据场景选择参数
if ($Scenario -eq "quick") {
    $Users = 50; $SpawnRate = 10; $RunTime = "3m"; $ReportName = "quick_test"
} elseif ($Scenario -eq "load") {
    $Users = 100; $SpawnRate = 10; $RunTime = "10m"; $ReportName = "load_100u"
} elseif ($Scenario -eq "stress") {
    $Users = 500; $SpawnRate = 50; $RunTime = "10m"; $ReportName = "stress_500u"
} elseif ($Scenario -eq "stability") {
    $Users = 200; $SpawnRate = 20; $RunTime = "1h"; $ReportName = "stability_1h"
} elseif ($Scenario -eq "readonly") {
    $Users = 200; $SpawnRate = 20; $RunTime = "10m"; $ReportName = "readonly_200u"
} elseif ($Scenario -eq "spike") {
    $Users = 50; $SpawnRate = 10; $RunTime = "1m"; $ReportName = "spike_warmup"
} else {
    $Users = 50; $SpawnRate = 10; $RunTime = "3m"; $ReportName = "quick_test"
}

Write-Host "mall 性能测试: $Scenario | ${Users}并发 | ${RunTime}" -ForegroundColor Cyan

# 检查后端是否运行
try {
    Invoke-WebRequest -Uri $HostUrl -TimeoutSec 5 -UseBasicParsing | Out-Null
    Write-Host "后端服务 ONLINE" -ForegroundColor Green
} catch {
    Write-Host "后端服务 OFFLINE - 请先启动 mall-admin!" -ForegroundColor Red
    exit 1
}

# 构建 Locust 命令参数
$locustCmd = @(
    "locust",
    "-f", "$BaseDir\locustfile.py",
    "--host=$HostUrl",
    "--headless",
    "--users", "$Users",
    "--spawn-rate", "$SpawnRate",
    "--run-time", "$RunTime",
    "--html=$ReportDir\$ReportName.html",
    "--csv=$ReportDir\$ReportName"
)
if ($UserClass) { $locustCmd += $UserClass }

Write-Host "开始压测... (等待${RunTime})" -ForegroundColor Yellow

& locust -f "$BaseDir\locustfile.py" --host=$HostUrl --headless --users $Users --spawn-rate $SpawnRate --run-time $RunTime --html="$ReportDir\$ReportName.html" --csv="$ReportDir\$ReportName" $UserClass

Write-Host ""
Write-Host "压测完成!" -ForegroundColor Green
Write-Host "HTML报告: $ReportDir\$ReportName.html" -ForegroundColor Green
