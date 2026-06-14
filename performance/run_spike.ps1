# mall 商城性能测试 — 峰值（Spike）测试专用脚本 (PowerShell)
# 用法：.\performance\run_spike.ps1
# 描述：分三步执行峰值测试（预热 → 脉冲 → 恢复）

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $BaseDir
$ReportDir = "$BaseDir\report"
$HostUrl = "http://localhost:8080"

# 确保报告目录存在
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
}

function Check-Backend {
    Write-Host "`n检查后端服务..." -ForegroundColor Gray
    try {
        $response = Invoke-WebRequest -Uri $HostUrl -TimeoutSec 5 -UseBasicParsing
        Write-Host "  后端服务: ONLINE ($($response.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "  后端服务: OFFLINE — 请先启动 mall-admin！" -ForegroundColor Red
        Write-Host "  启动命令: cd D:\mall\mall-admin && mvn spring-boot:run" -ForegroundColor Gray
        exit 1
    }
}

function Run-Locust {
    param($UserClass, $Users, $SpawnRate, $RunTime, $ReportName)
    
    Write-Host "`n  执行: locust -u $UserClass --users $Users --spawn-rate $SpawnRate --run-time $RunTime" -ForegroundColor Gray
    
    & locust -f "$BaseDir\locustfile.py" `
        -u $UserClass `
        --host=$HostUrl `
        --headless `
        --users $Users `
        --spawn-rate $SpawnRate `
        --run-time $RunTime `
        --html="$ReportDir\$ReportName.html" `
        --csv="$ReportDir\$ReportName"
    
    Write-Host "  报告已保存: $ReportDir\$ReportName.html" -ForegroundColor Cyan
}

# ========== 主流程 ==========

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  mall 峰值测试（Spike Test）— 3 阶段" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Check-Backend

# 阶段 1：预热（正常负载，50 并发，1 分钟）
Write-Host "`n[阶段 1/3] 预热：50 并发，1 分钟..." -ForegroundColor Yellow
Run-Locust -UserClass "MallAdminUser" -Users 50 -SpawnRate 10 -RunTime "1m" -ReportName "spike_warmup"

# 阶段 2：峰值脉冲（1000 并发，spawn-rate=500，1 分钟）
Write-Host "`n[阶段 2/3] 峰值脉冲：1000 并发（spawn-rate=500），1 分钟..." -ForegroundColor Magenta
Write-Host "  ⚠️ 这是峰值阶段，系统可能返回 429/503，属正常现象" -ForegroundColor Yellow
Run-Locust -UserClass "SpikeUser" -Users 1000 -SpawnRate 500 -RunTime "1m" -ReportName "spike_pulse"

# 阶段 3：恢复期（回到 50 并发，2 分钟）
Write-Host "`n[阶段 3/3] 恢复期：50 并发，2 分钟..." -ForegroundColor Green
Run-Locust -UserClass "MallAdminUser" -Users 50 -SpawnRate 10 -RunTime "2m" -ReportName "spike_recovery"

# ========== 完成 ==========

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  峰值测试完成！" -ForegroundColor Green
Write-Host "  预热报告: $ReportDir\spike_warmup.html" -ForegroundColor Green
Write-Host "  脉冲报告: $ReportDir\spike_pulse.html" -ForegroundColor Green
Write-Host "  恢复报告: $ReportDir\spike_recovery.html" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n📊 对比三份报告的 TPS / P95 RT / 错误率，判断是否通过峰值测试。" -ForegroundColor Cyan
