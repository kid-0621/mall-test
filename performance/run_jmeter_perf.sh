#!/bin/bash
# JMeter 五阶段性能测试 — 非 GUI 模式
# 对齐简历：基准→负载→压力→稳定→峰值
# 用法: bash run_jmeter_perf.sh [quick|full]

set -e

JMETER="D:/tools/apache-jmeter-5.6.3/bin/jmeter.bat"
JMX="D:/mall-test/performance/jmeter/mall_performance_test.jmx"
REPORT="D:/mall-test/performance/jmeter/reports"

MODE="${1:-full}"

# 五阶段配置
if [ "$MODE" = "quick" ]; then
    STAGES="benchmark:50:120:10:基准测试"
    echo "=== 快速模式：仅跑基准测试 ==="
else
    STAGES="benchmark:50:120:10:基准测试
load:100:120:20:负载测试
stress:500:120:30:压力测试
stability:200:300:20:稳定性测试
spike:1000:60:5:峰值测试"
    echo "=== 完整五阶段 JMeter 性能测试 ==="
fi

echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

TOTAL_START=$(date +%s)

echo "$STAGES" | while IFS=':' read -r name threads duration rampup desc; do
    [ -z "$name" ] && continue
    
    JTL="$REPORT/${name}.jtl"
    RPT="$REPORT/${name}"
    TMP="$REPORT/_${name}.jmx"
    
    echo "========================================"
    echo "  阶段: $desc ($name)"
    echo "  并发: $threads | 时长: ${duration}s | 预热: ${rampup}s"
    echo "========================================"
    
    # 清理旧结果（注意：不预建目录，JMeter -e -o 需要目录不存在或为空）
    rm -rf "$RPT" "$JTL" 2>/dev/null
    
    # 生成参数化JMX（匹配核心业务链路线程组的参数）
    cp "$JMX" "$TMP"
    sed -i "/testname=\"核心业务链路/,/<\/ThreadGroup>/ {
        s/<intProp name=\"ThreadGroup.num_threads\">[0-9]*</<intProp name=\"ThreadGroup.num_threads\">$threads</
        s/<intProp name=\"ThreadGroup.ramp_time\">[0-9]*</<intProp name=\"ThreadGroup.ramp_time\">$rampup</
        s/<longProp name=\"ThreadGroup.duration\">[0-9]*</<longProp name=\"ThreadGroup.duration\">$duration</
    }" "$TMP"
    
    STAGE_START=$(date +%s)
    echo "启动 JMeter..."
    
    "$JMETER" -n -t "$TMP" -l "$JTL" -e -o "$RPT" 2>&1 | grep -E "summary|Err|Tidying|error" || true
    RC=${PIPESTATUS[0]}
    
    rm -f "$TMP"
    
    STAGE_ELAPSED=$(( $(date +%s) - STAGE_START ))
    echo "完成! 耗时: ${STAGE_ELAPSED}s | 退出码: $RC"
    
    if [ "$RC" -ne 0 ]; then
        echo "警告: JMeter 非正常退出"
    fi
    echo ""
done

TOTAL_ELAPSED=$(( $(date +%s) - TOTAL_START ))
echo "========================================"
echo "  全部完成！总耗时: ${TOTAL_ELAPSED}s"
echo "  报告目录: $REPORT"
echo "========================================"
echo ""
echo "各阶段报告:"
for d in "$REPORT"/*/; do
    name=$(basename "$d")
    if [ -f "$d/index.html" ]; then
        echo "  $name → $d/index.html"
    fi
done
