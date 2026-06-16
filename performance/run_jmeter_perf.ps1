# JMeter 五阶段性能测试 — 非 GUI 模式
# 对齐简历：基准→负载→压力→稳定→峰值
# 用法: .\run_jmeter_perf.ps1 [quick|full]

param(
    [string]$Mode = "full"
)

$ErrorActionPreference = "Stop"

$JMETER = "D:\tools\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMX    = "D:\mall-test\performance\jmeter\mall_performance_test.jmx"
$REPORT = "D:\mall-test\performance\jmeter\reports"

# 确保报告目录存在
if (-not (Test-Path $REPORT)) {
    New-Item -ItemType Directory -Path $REPORT -Force | Out-Null
}

# 五阶段配置（对齐 Locust）
$stages = @(
    @{ Name = "benchmark"; Threads = 50;  Duration = 120; RampUp = 10; Desc = "基准测试" },
    @{ Name = "load";      Threads = 100; Duration = 120; RampUp = 20; Desc = "负载测试" },
    @{ Name = "stress";    Threads = 500; Duration = 120; RampUp = 30; Desc = "压力测试" },
    @{ Name = "stability"; Threads = 200; Duration = 300; RampUp = 20; Desc = "稳定性测试" },
    @{ Name = "spike";     Threads = 1000;Duration = 60;  RampUp = 5;  Desc = "峰值测试" }
)

if ($Mode -eq "quick") {
    $stages = @($stages[0])  # 只跑基准测试
    Write-Host "=== 快速模式：仅跑基准测试 ===" -ForegroundColor Yellow
}
else {
    Write-Host "=== 完整五阶段 JMeter 性能测试 ===" -ForegroundColor Cyan
}

$totalStart = Get-Date

foreach ($stage in $stages) {
    $name = $stage.Name
    $threads = $stage.Threads
    $duration = $stage.Duration
    $rampup = $stage.RampUp
    $desc = $stage.Desc

    $jtlFile = "$REPORT\$name.jtl"
    $reportDir = "$REPORT\$name"

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  阶段: $desc ($name)" -ForegroundColor Cyan
    Write-Host "  并发: $threads | 时长: ${duration}s | 预热: ${rampup}s" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    # 清理旧结果
    if (Test-Path $jtlFile) { Remove-Item $jtlFile -Force }
    if (Test-Path $reportDir) { Remove-Item $reportDir -Recurse -Force }

    $stageStart = Get-Date

    # 运行 JMeter 非 GUI 模式
    $args = @(
        "-n",
        "-t", $JMX,
        "-Jthreads=$threads",
        "-Jduration=$duration",
        "-Jrampup=$rampup",
        "-l", $jtlFile,
        "-e",
        "-o", $reportDir
    )

    Write-Host "启动 JMeter..." -ForegroundColor Yellow
    $proc = Start-Process -FilePath $JMETER -ArgumentList $args -NoNewWindow -Wait -PassThru

    $stageElapsed = [math]::Round(((Get-Date) - $stageStart).TotalSeconds, 1)
    Write-Host "完成! 耗时: ${stageElapsed}s | 退出码: $($proc.ExitCode)" -ForegroundColor Green

    if ($proc.ExitCode -ne 0) {
        Write-Host "警告: JMeter 非正常退出 (exit code: $($proc.ExitCode))" -ForegroundColor Red
    }
}

$totalElapsed = [math]::Round(((Get-Date) - $totalStart).TotalSeconds, 1)
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  全部五阶段完成！总耗时: ${totalElapsed}s" -ForegroundColor Cyan
Write-Host "  报告目录: $REPORT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 汇总各阶段 JTL 统计
Write-Host ""
Write-Host "=== 各阶段结果文件 ===" -ForegroundColor Yellow
foreach ($stage in $stages) {
    $jtl = "$REPORT\$($stage.Name).jtl"
    $report = "$REPORT\$($stage.Name)"
    $exists = Test-Path $jtl
    $hasReport = Test-Path "$report\index.html"
    $status = if ($exists) { "JTL: $([math]::Round((Get-Item $jtl).Length/1KB,1))KB" } else { "JTL: MISSING" }
    $rpt = if ($hasReport) { "报告: OK" } else { "报告: MISSING" }
    Write-Host "  $($stage.Name) [$($stage.Desc)] → $status | $rpt"
}

Write-Host ""
Write-Host "提示: 用浏览器打开 $REPORT\<阶段名>\index.html 查看 HTML 报告" -ForegroundColor Green
