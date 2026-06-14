"""
mall 商城性能测试 — 执行方案

本文档定义了完整的性能测试场景规划和执行步骤。
"""

# ============================================
# 一、测试环境
# ============================================

"""
┌─────────────────────────────────────────────────────┐
│                     测试环境                          │
├─────────────────────────────────────────────────────┤
│  后端服务:  mall-admin (Spring Boot)                 │
│  服务地址:  http://localhost:8080                     │
│  数据库:    MySQL 8.0 (通过 mall.sql 初始化)          │
│  压测工具:  Locust 2.33.1                            │
│  压测账号:  admin / macro123                         │
│  操作系统:  Windows 11                               │
│  CPU:      本地开发机                                │
│  内存:     本地开发机                                │
└─────────────────────────────────────────────────────┘
"""

# ============================================
# 二、接口清单与权重
# ============================================

INTERFACE_WEIGHTS = {
    # 商品浏览类 (45%)
    "GET /product/list":                    {"weight": 25, "type": "READ", "desc": "商品列表查询"},
    "GET /product/simpleList":              {"weight": 10, "type": "READ", "desc": "模糊搜索商品"},
    "GET /product/updateInfo/{id}":         {"weight": 5,  "type": "READ", "desc": "商品详情"},
    "GET /brand/list":                      {"weight": 5,  "type": "READ", "desc": "品牌列表"},

    # 分类浏览类 (12%)
    "GET /productCategory/list/withChildren":{"weight": 7,  "type": "READ", "desc": "分类树"},
    "GET /productCategory/list/{parentId}": {"weight": 5,  "type": "READ", "desc": "分类列表"},

    # 订单查看类 (25%)
    "GET /order/list":                      {"weight": 15, "type": "READ", "desc": "订单列表"},
    "GET /order/{id}":                      {"weight": 10, "type": "READ", "desc": "订单详情"},

    # 营销数据类 (13%)
    "GET /coupon/list":                     {"weight": 8,  "type": "READ", "desc": "优惠券列表"},
    "GET /flash/list":                      {"weight": 5,  "type": "READ", "desc": "秒杀活动"},

    # 系统类 (5%)
    "GET /admin/info":                      {"weight": 3,  "type": "READ", "desc": "管理员信息"},
    "GET /menu/treeList":                   {"weight": 2,  "type": "READ", "desc": "菜单树"},
}

# ============================================
# 三、测试场景设计
# ============================================

SCENARIOS = {
    # ── 场景1：单接口基准测试 ──
    "benchmark": {
        "name": "基准测试",
        "goal": "获取每个核心接口的单点性能基线",
        "method": "逐接口单独压测",
        "steps": [
            ("1并发-5min",  "baseline"),
            ("10并发-5min", "建立基准曲线"),
            ("30并发-5min", "找拐点"),
            ("50并发-5min", "找拐点"),
        ],
        "locust_cmd": """
# 使用 --run-time 控制时长，修改 locustfile 中的 @task 权重来单独测某个接口
# （实际通过 Web UI 更方便：设置 task 权重后启动）
locust -f locustfile.py --host=http://localhost:8080
        """.strip(),
    },

    # ── 场景2：混合场景负载测试 ──
    "load": {
        "name": "负载测试（混合场景）",
        "goal": "模拟日常运营峰值，验证系统在目标负载下的表现",
        "criteria": "P95 RT < 2s, 错误率 < 0.5%",
        "steps": [
            ("50并发-10min",  "轻负载基线"),
            ("100并发-10min", "目标负载"),
            ("200并发-10min", "高峰负载"),
            ("300并发-10min", "验证余量"),
        ],
        "locust_cmd": """
# 50 并发，每秒启动 10 个用户，运行 10 分钟
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 50 --spawn-rate 10 --run-time 10m \\
    --html=performance/report/load_50u.html --csv=performance/report/load_50u

# 100 并发
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 100 --spawn-rate 10 --run-time 10m \\
    --html=performance/report/load_100u.html --csv=performance/report/load_100u

# 200 并发
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 200 --spawn-rate 20 --run-time 10m \\
    --html=performance/report/load_200u.html --csv=performance/report/load_200u

# 300 并发
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 300 --spawn-rate 30 --run-time 10m \\
    --html=performance/report/load_300u.html --csv=performance/report/load_300u
        """.strip(),
    },

    # ── 场景3：压力测试 ──
    "stress": {
        "name": "压力测试",
        "goal": "持续加压直到系统崩溃，找到极限并发和极限 TPS",
        "criteria": "观察 TPS 不再增长 + RT 急剧上升 + 错误率飙升的拐点",
        "steps": [
            ("300并发-10min", "重负载"),
            ("500并发-10min", "接近极限"),
            ("800并发-10min", "极限加压"),
            ("1000并发-10min","超极限"),
        ],
        "locust_cmd": """
# 500 并发压力
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 500 --spawn-rate 50 --run-time 10m \\
    --html=performance/report/stress_500u.html

# 800 并发
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 800 --spawn-rate 80 --run-time 10m \\
    --html=performance/report/stress_800u.html

# 1000 并发
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 1000 --spawn-rate 100 --run-time 10m \\
    --html=performance/report/stress_1000u.html
        """.strip(),
    },

    # ── 场景4：稳定性测试 ──
    "stability": {
        "name": "稳定性测试（Soak Test）",
        "goal": "验证系统在持续负载下无内存泄漏、连接泄漏等慢性问题",
        "criteria": "运行 1h 后 RT 无明显上升趋势，错误率不累积",
        "steps": [
            ("最大TPS的70%并发-1h", "长时间稳定性"),
        ],
        "locust_cmd": """
# 假设最大并发是 500，取 70% 即 350，运行 1 小时
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 350 --spawn-rate 35 --run-time 1h \\
    --html=performance/report/stability_1h.html
        """.strip(),
    },

    # ── 场景5：峰值测试（Spike Test）───
    "spike": {
        "name": "峰值测试（Spike Test）",
        "name_en": "Spike Test",
        "goal": "模拟瞬时流量脉冲，验证系统的弹性扩容和降级能力",
        "criteria": "系统在峰值后恢复正常，无雪崩；允许短暂 503/429，不允许持续失败",
        "method": "使用 SpikeUser 类，超高速生成并发（spawn-rate=500）",
        "steps": [
            ("正常负载 60s",   "用 MallAdminUser, 50 并发预热"),
            ("峰值脉冲 60s",   "切换到 SpikeUser, 1000 并发, spawn-rate=500"),
            ("恢复期 120s",    "回到 50 并发，观察系统是否恢复"),
        ],
        "locust_cmd": """
# 峰值测试：瞬时加压 → 观察 → 恢复
# 方式：用 headless 分三次运行，或用 Web UI 手动控制

# 第一步：正常负载预热（50 并发，1 分钟）
locust -f performance/locustfile.py -u MallAdminUser --host=http://localhost:8080 \\
    --headless --users 50 --spawn-rate 10 --run-time 1m \\
    --html=performance/report/spike_warmup.html

# 第二步：峰值脉冲（1000 并发，spawn-rate=500，1 分钟）
locust -f performance/locustfile.py -u SpikeUser --host=http://localhost:8080 \\
    --headless --users 1000 --spawn-rate 500 --run-time 1m \\
    --html=performance/report/spike_pulse.html

# 第三步：恢复期（50 并发，2 分钟）
locust -f performance/locustfile.py -u MallAdminUser --host=http://localhost:8080 \\
    --headless --users 50 --spawn-rate 10 --run-time 2m \\
    --html=performance/report/spike_recovery.html
        """.strip(),
    },

    # ── 场景6：纯读场景（补充）───
    "read-only": {
        "name": "纯读场景",
        "goal": "单独测试数据库读承载能力",
        "method": "使用 MallReadOnlyUser，只做查询",
        "locust_cmd": """
# 修改 locustfile 中的 HttpUser 类名，或者在 Web UI 中选择
# 或直接命令行指定（需在代码中切换）
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 200 --spawn-rate 20 --run-time 10m \\
    --html=performance/report/readonly_200u.html
        """.strip(),
    },
}

# ============================================
# 四、执行步骤
# ============================================

EXECUTION_PLAN = """
执行顺序（推荐）：

Step 0. 环境检查
  ├── 确认 mall 后端已启动：curl http://localhost:8080
  ├── 确认数据库有数据：已导入 mall.sql
  └── 确认 Locust 已安装：locust --version

Step 1. 基准测试（30 min）
  ├── 1 并发预热 → 了解单用户 RT
  ├── 10 并发 → 建立基准曲线
  └── 记录各接口基线数据

Step 2. 负载测试（60 min）
  ├── 50 → 100 → 200 → 300 逐步加压
  ├── 每个梯度 10 分钟
  └── 输出 TPS-RT 曲线

Step 3. 压力测试（60 min）
  ├── 300 → 500 → 800 → 1000
  ├── 找到系统崩溃点
  └── 记录极限 TPS 和并发

Step 4. 稳定性测试（60 min）
  ├── 取极限并发的 70%
  └── 运行 1 小时观察趋势

Step 5. 结果分析 & 报告
  ├── 汇总所有场景的 TPS/RT/错误率
  ├── 对比基线数据
  └── 输出性能测试报告

总计预估时间：~3.5 小时（不含调优）
"""

# ============================================
# 五、运行命令速查
# ============================================

QUICK_START = """
# === 一键启动 Web UI ===
cd /d/mall-test
locust -f performance/locustfile.py --host=http://localhost:8080
# 浏览器打开 http://localhost:8089

# === Headless 快速压测（100 并发，5 分钟）===
cd /d/mall-test
locust -f performance/locustfile.py --host=http://localhost:8080 \\
    --headless --users 100 --spawn-rate 10 --run-time 5m \\
    --html=performance/report/quick_test.html

# === Windows PowerShell 版本（注意反引号选义）===
cd D:\mall-test
locust -f performance\locustfile.py --host=http://localhost:8080 `
    --headless --users 100 --spawn-rate 10 --run-time 5m `
    --html=performance\report\quick_test.html
"""

# ============================================
# 六、监控指标采集
# ============================================

MONITORING = """
压测期间需同步监控以下指标：

┌──────────────┬──────────────────────┬──────────────────┐
│ 层次          │ 关注指标              │ 工具/命令         │
├──────────────┼──────────────────────┼──────────────────┤
│ 服务器        │ CPU / 内存 / 磁盘IO   │ 任务管理器        │
│ Java 应用     │ GC 频率 / 堆内存       │ jstat -gc <pid>  │
│ MySQL         │ 慢查询 / 连接数        │ SHOW PROCESSLIST │
│ Locust 自身   │ RPS / 失败数 / P95   │ Web UI 或 HTML   │
└──────────────┴──────────────────────┴──────────────────┘

Windows 监控命令：
  # 查看 Java 进程 PID
  jps -l | findstr mall

  # GC 统计（每2秒采样）
  jstat -gc <pid> 2000

  # 任务管理器 → 性能页 → 查看 CPU/内存/磁盘
"""


if __name__ == "__main__":
    print("mall 商城性能测试 — 执行方案")
    print("=" * 50)
    print(f"\n核心接口数: {len(INTERFACE_WEIGHTS)}")
    print(f"测试场景数: {len(SCENARIOS)}")
    print(f"\n{QUICK_START}")
