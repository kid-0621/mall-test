# JMeter 五阶段性能测试 — PowerShell 包装器
# 调用可靠的 Bash 脚本执行
# 用法: .\run_jmeter_perf.ps1 [quick|full]

param(
    [string]$Mode = "full"
)

$BashScript = "D:\mall-test\performance\run_jmeter_perf.sh"

if (-not (Test-Path $BashScript)) {
    Write-Error "找不到 $BashScript"
    exit 1
}

Write-Host "启动 JMeter 五阶段性能测试..." -ForegroundColor Cyan
& bash $BashScript $Mode
