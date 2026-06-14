# mall 商城后台管理系统 — 性能测试执行方案

> 版本: v2.1 | 日期: 2026-06-14 | 工具: Locust 2.33.1 + JMeter 5.6.3
>
> **更新说明（v2.1）**：补充五阶段实测数据汇总、更新执行步骤与实际命令、新增"遇到的困难与解决方法"章节。
> 完整报告见 [PERFORMANCE_TEST_REPORT.md](./PERFORMANCE_TEST_REPORT.md)

---

## 目录

1. [测试概述](#1-测试概述)
2. [核心指标详解](#2-核心指标详解)
3. [测试环境](#3-测试环境)
4. [工具对比：Locust vs JMeter](#4-工具对比locust-vs-jmeter)
5. [4 个 User 类设计](#5-4-个-user-类设计)
6. [5 阶段测试策略（含实测数据）](#6-5-阶段测试策略含实测数据)
7. [执行步骤（实测命令）](#7-执行步骤实测命令)
8. [Locust 报告解读](#8-locust-报告解读)
9. [遇到的困难与解决方法](#9-遇到的困难与解决方法)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 测试概述

### 1.1 测试目标

| 项目 | 说明 |
|------|------|
| **被测系统** | mall 商城后台管理系统 (Spring Boot) |
| **测试目的** | 使用 JMeter 和 Locust 对核心业务链路实施压测，验证系统性能表现 |
| **核心指标** | TPS、响应时间、并发用户数、P95/P99 RT、错误率 |
| **压测工具** | Locust 2.33.1（Python 协程）+ JMeter 5.6.3（Java 线程） |
| **并发模型** | Locust: gevent 协程（单进程数千并发）；JMeter: 操作系统线程（受限 CPU 核数） |

### 1.2 核心业务链路设计

压测不是随机请求，而是模拟真实用户操作流程（业务链路）：

```
核心业务链路（Business Chain）：
  [登录] → [浏览商品列表] → [搜索商品] → [查看商品详情]
    → [浏览订单列表] → [查看订单详情] → [浏览优惠券] → [查看分类树]

对应 Locust 脚本中的 BusinessChainUser 类（串行执行，非随机权重）。
对应 JMeter 脚本中的"核心业务链路"线程组（按顺序执行 Sampler）。
```

### 1.3 为什么同时使用 JMeter 和 Locust？

| 维度 | Locust | JMeter | 为什么两个都用 |
|------|--------|--------|----------------|
| 并发模型 | gevent 协程，轻量 | Java 线程，较重 | 对比两种模型的资源消耗 |
| 脚本语言 | Python（已掌握） | XML/GUI | 展示工具广度 |
| 分布式 | 原生支持 `--worker` | 需要 Remote 启动 | 学习不同分布式方案 |
| 报告 | HTML/CSV，需自行解析 | 聚合报告开箱即用 | 对比报告易读性 |
| 简历价值 | ✅ 展示 Python 能力 | ✅ 展示工具广度 | 企业两者都会更受欢迎 |

> **面试话术**："我用 Locust 做日常回归（与接口测试技术栈一致），用 JMeter 做大并发压测（JMeter 的生态更成熟，与 Prometheus/Grafana 集成更方便）。"

---

## 2. 核心指标详解

### 2.1 TPS（Transactions Per Second）

| 概念 | 说明 |
|------|------|
| **定义** | 每秒处理的事务数（这里 = 每秒完成的 HTTP 请求数） |
| **计算** | `TPS = 总请求数 / 总耗时（秒）` |
| **关注点** | TPS 随并发数增加 → 达到拐点后不再增长 → 下降 |
| **Locust 中的含义** | `Current RPS`（Report 中的 Requests/s） |

### 2.2 P95 / P99 响应时间

| 概念 | 说明 | 举例 |
|------|------|------|
| **P50（中位数）** | 50% 的请求 RT 低于此值 | P50=6ms → 一半请求在 6ms 内完成 |
| **P95** | 95% 的请求 RT 低于此值 | P95=15ms → 95% 请求在 15ms 内完成 |
| **P99** | 99% 的请求 RT 低于此值 | P99=99ms → 99% 请求在 99ms 内完成 |

> **为什么 P95/P99 比 Average 更有意义？**
> 假设 100 个请求：99 个耗时 100ms，1 个耗时 10s。
> Average = 199ms → 看起来很好。P99 = 10000ms → 真实反映了长尾问题。

### 2.3 Locust 协程并发模型（简历亮点）

```
传统线程模型（JMeter）：
  Thread-1 ──┐
  Thread-2 ──┤  → OS 线程（昂贵资源，上下文切换开销大）
  Thread-N ──┘

Locust 协程模型（gevent）：
  Coroutine-1 ──┐
  Coroutine-2 ──┤
  ...             ├──→ 同 1 个 OS 线程内协作式调度（极低开销）
  Coroutine-N ──┘
                    遇 IO 自动让出 CPU，不阻塞线程

优势：单进程可模拟 10,000+ 并发用户（JMeter 约 2,000 线程即耗尽内存）
```

---

## 3. 测试环境

| 组件 | 参数 |
|------|------|
| 压测工具 | Locust 2.33.1 + JMeter 5.6.3 |
| 被测服务 | mall-admin (Spring Boot 2.x) |
| 数据库 | MySQL 8.0, mall 库（已导入 mall.sql） |
| 操作系统 | Windows 11 |
| Java | JDK 17 |
| Python | 3.9 (Anaconda) |
| 后端地址 | http://localhost:8080 |

> **⚠️ 压测机瓶颈说明**：
> 压测机与被测服务在同一台机器，Locust 协程本身也会消耗 CPU。
> 若 TPS 上不去但 CPU 未满，可能是 Locust 单机瓶颈 → 需分布式运行。

---

## 4. 工具对比：Locust vs JMeter

| 维度 | Locust | JMeter |
|------|--------|--------|
| **并发能力** | 单进程 10,000+ 用户 | 约 2,000 线程即耗尽内存 |
| **资源消耗** | 极低（共享线程） | 高（每用户 = 1 线程） |
| **脚本语言** | Python（易读易改） | XML/GUI（改脚本需开 GUI） |
| **报告** | HTML/CSV（需自行解析） | 聚合报告开箱即用 |
| **适用场景** | 高并发、复杂逻辑 | 标准协议、开箱即用报告 |

---

## 5. 4 个 User 类设计

`locustfile.py` 中定义了 4 种虚拟用户行为模型：

| User 类 | 模拟角色 | 行为特征 | wait_time | 对应阶段 |
|---------|---------|-----------|------------|---------|
| `MallAdminUser` | 后台管理员 | 按权重随机访问各模块 | 1~3s | ①②④ |
| `BusinessChainUser` | 运营人员 | **固定顺序**串行 8 步 | 0.5~1.5s | ①② |
| `MallReadOnlyUser` | 只读访客 | 纯查询，高密度 | 0.5~1.5s | 可选补充 |
| `SpikeUser` | 秒杀大促 | 无间隔，瞬间高并发 | 0s | ⑤ |

**链路 8 步详解（BusinessChainUser）**：

```
Step 1:  login              → POST /admin/login
Step 2:  list_products     → GET  /product/list
Step 3:  search_products   → GET  /product/list?keyword=...
Step 4:  view_product      → GET  /product/updateInfo/{id}
Step 5:  view_orders       → GET  /order/list
Step 6:  view_category     → GET  /productCategory/list/withChildren
Step 7:  view_brand        → GET  /brand/list
Step 8:  view_coupon       → GET  /coupon/list
```

---

## 6. 5 阶段测试策略（含实测数据）

### 实测结果汇总

| 阶段 | 并发 | 场景 | TPS | P50 | P95 | P99 | 失败率 | 关键发现 |
|------|------|------|-----|-----|-----|-----|--------|---------|
| ① 基准 | 50 | MallAdminUser | 24.95 | 6ms | 9ms | 98ms | 0% | 建立基线 ✅ |
| ① 基准 | 50 | BusinessChainUser | 32.81 | 8ms | 23ms | 190ms | 0% | login 冷启动拉高 P99 |
| ② 负载 | 100 | MallAdminUser | 49.77 | 8ms | 15ms | 99ms | 0% | TPS 翻倍，线性扩展 ✅ |
| ② 负载 | 100 | BusinessChainUser | 66.22 | 6ms | 9ms | 24ms | 0% | 稳态性能优秀 ✅ |
| ③ 压力 | 500 | MallAdminUser | 247.90 | 7ms | 13ms | 57ms | 0% | 未找到瓶颈，完美线性 ✅ |
| ④ 稳定 | 200 | MallAdminUser | 99.39 | 6ms | 9ms | 11ms | 0% | 1h 零劣化 ✅ |
| ⑤ 峰值 | 1000 | SpikeUser | 578.72 | 1100ms | 1600ms | 4800ms | 0% | 排队不雪崩 ✅ |

### 阶段详解

#### 阶段①：基准测试（Benchmark）

| 参数 | 值 |
|------|-----|
| **目的** | 建立单接口性能基线 |
| **并发** | 50 |
| **时长** | 3 分钟 |
| **场景** | MallAdminUser + BusinessChainUser 各跑一次 |
| **判定** | 记录各接口基线 TPS/RT |

#### 阶段②：负载测试（Load Test）

| 参数 | 值 |
|------|-----|
| **目的** | 验证日常运营峰值下的系统表现 |
| **并发** | 100 |
| **时长** | 5 分钟 |
| **场景** | MallAdminUser + BusinessChainUser 各跑一次 |
| **通过标准** | TPS 线性增长，P95 RT < 100ms，错误率 = 0% |

**实测**：TPS 从 24.95 → 49.77（MallAdminUser），近乎完美翻倍。

#### 阶段③：压力测试（Stress Test）

| 参数 | 值 |
|------|-----|
| **目的** | 找到系统 TPS 拐点 |
| **并发** | 500 |
| **时长** | 10 分钟 |
| **场景** | MallAdminUser（均匀冲击所有接口） |
| **观察重点** | TPS 不再增长 + RT 急剧上升的拐点 |

**实测**：TPS = 247.90，P95 = 13ms，0 失败。系统在 500 并发下未找到瓶颈（本机 localhost 环境）。

#### 阶段④：稳定性测试（Soak Test）

| 参数 | 值 |
|------|-----|
| **目的** | 发现内存泄漏、连接泄漏等"慢性病" |
| **并发** | 200（压力阶段的 40%） |
| **时长** | 1 小时 |
| **通过标准** | RT 无明显上升趋势，错误率不累积 |

**实测**：TPS = 99.39（始终平稳），P95 = 9ms，0 失败。1 小时长跑零劣化，无内存泄漏/GC 抖动。

#### 阶段⑤：峰值测试（Spike Test）

| 参数 | 值 |
|------|-----|
| **目的** | 模拟瞬时流量脉冲（秒杀场景） |
| **并发** | 1000 |
| **spawn-rate** | 200（5 秒内全部就绪） |
| **时长** | 5 分钟 |
| **通过标准** | 允许 RT 上升，但不允许大量 5xx 错误 |

**实测**：TPS = 578.72（五阶段之巅），P50 = 1100ms，P95 = 1600ms，0 失败。
瓶颈根因：数据库连接池（HikariCP 默认 10 连接）饱和，请求排队而非崩溃（优雅降级）。

---

## 7. 执行步骤（实测命令）

### 7.0 环境检查

```powershell
# 1. 确认后端运行
curl http://localhost:8080
# 应返回 JSON（即使 404 也行，说明服务在线）

# 2. 确认 Locust 可用
locust --version
# 应输出: locust 2.33.1

# 3. 进入项目目录
cd D:\mall-test
```

### 7.1 基准测试（50 并发）

```powershell
# MallAdminUser 场景
locust -f performance\locustfile.py MallAdminUser `
    --host=http://localhost:8080 `
    --headless --users 50 --spawn-rate 10 --run-time 3m `
    --html=performance\report\quick_test.html

# BusinessChainUser 场景（核心业务链路）
locust -f performance\locustfile.py BusinessChainUser `
    --host=http://localhost:8080 `
    --headless --users 50 --spawn-rate 10 --run-time 3m `
    --html=performance\report\chain_benchmark.html
```

### 7.2 负载测试（100 并发）

```powershell
# MallAdminUser 场景
locust -f performance\locustfile.py MallAdminUser `
    --host=http://localhost:8080 `
    --headless --users 100 --spawn-rate 20 --run-time 5m `
    --html=performance\report\load_test.html

# BusinessChainUser 场景
locust -f performance\locustfile.py BusinessChainUser `
    --host=http://localhost:8080 `
    --headless --users 100 --spawn-rate 20 --run-time 5m `
    --html=performance\report\chain_load.html
```

### 7.3 压力测试（500 并发）

```powershell
locust -f performance\locustfile.py MallAdminUser `
    --host=http://localhost:8080 `
    --headless --users 500 --spawn-rate 50 --run-time 10m `
    --html=performance\report\stress_test.html
```

### 7.4 稳定性测试（200 并发 × 1 小时）

```powershell
locust -f performance\locustfile.py MallAdminUser `
    --host=http://localhost:8080 `
    --headless --users 200 --spawn-rate 20 --run-time 1h `
    --html=performance\report\stability_test.html
```

### 7.5 峰值测试（1000 并发脉冲）

```powershell
locust -f performance\locustfile.py SpikeUser `
    --host=http://localhost:8080 `
    --headless --users 1000 --spawn-rate 200 --run-time 5m `
    --html=performance\report\spike_test.html
```

### 7.6 一键运行脚本

```powershell
# 快速验证（MallAdminUser，50 并发，3 分钟）
.\performance\run_perf.ps1 -Scenario quick -UserClass MallAdminUser

# 负载测试（MallAdminUser，100 并发，5 分钟）
.\performance\run_perf.ps1 -Scenario load -UserClass MallAdminUser

# 压力测试（MallAdminUser，500 并发，10 分钟）
.\performance\run_perf.ps1 -Scenario stress -UserClass MallAdminUser

# 稳定性测试（MallAdminUser，200 并发，1 小时）
.\performance\run_perf.ps1 -Scenario stability -UserClass MallAdminUser

# 峰值测试（SpikeUser，1000 并发，5 分钟）
.\performance\run_perf.ps1 -Scenario spike -UserClass SpikeUser
```

### 7.7 JMeter 运行命令

```powershell
$env:JMETER_HOME = "D:\tools\apache-jmeter-5.6.3"
& "$env:JMETER_HOME\bin\jmeter.bat" -n `
    -t "D:\mall-test\performance\jmeter\mall_performance_test.jmx" `
    -l "D:\mall-test\performance\report\jmeter\results.jtl" `
    -e -o "D:\mall-test\performance\report\jmeter\html"
```

---

## 8. Locust 报告解读

### 8.1 汇总统计表关键字段

| 字段 | 含义 | 关注点 |
|------|------|--------|
| **Requests/s** | 当前 TPS | 是否随并发数线性增长？ |
| **50%ile** | P50（中位数 RT） | 大多数用户的体感延迟 |
| **95%ile** | P95 RT | **关键！** 尾部用户体感延迟 |
| **99%ile** | P99 RT | 极端情况延迟 |
| **Max** | 最大 RT | 受极端值影响，参考意义有限 |
| **Failures** | 失败数 | 是否为 0？ |

### 8.2 健康信号 vs 危险信号

```
健康信号：
  ✅ TPS 随并发数线性增长
  ✅ P95 随并发数缓慢上升（而非陡增）
  ✅ Failures = 0
  ✅ 长时间运行后 TPS 不衰减

危险信号：
  ❌ TPS 不再增长，但 RT 急剧上升 → 系统达到瓶颈
  ❌ Failures > 0 → 系统已开始拒绝请求
  ❌ P99 远大于 P95（10 倍以上）→ 存在严重长尾问题
  ❌ 长时间运行后 TPS 逐渐下降 → 可能存在内存泄漏
```

### 8.3 实际报告解读示例

以 `load_test.html`（100 并发负载测试）为例：

```
Aggregated 汇总行：
  Requests/s: 49.77  → TPS 接近基准的 2 倍（24.95×2=49.9），线性扩展优秀
  Median: 8ms        → 大多数用户体感延迟 8ms，极快
  95%ile: 15ms       → 95% 用户在 15ms 内收到响应，优秀
  99%ile: 99ms       → 1% 用户等待较久，但仍在可接受范围
  Max: 1400ms        → 受 login 接口影响，不代表业务接口性能
  Failures: 0         → 完美

结论：系统在 100 并发下表现优秀，可继续加压
```

---

## 9. 遇到的困难与解决方法

### Q1: 所有请求都报 401（Token 拼接 Bug）

```
现象：基准测试所有请求报 "暂未登录或token已经过期"

根因：locustfile.py 中 tokenHead 拼接多了一个空格
  - mall 后端 tokenHead 返回 "Bearer "（自带尾部空格）
  - 正确写法：f"{tokenHead}{token}"   → "Bearer xxx"
  - 错误写法：f"{tokenHead} {token}" → "Bearer  xxx"（双空格无效）

修复：locustfile.py 4 处 + login_locust.py 1 处，改为无空格拼接

预防：用功能测试 conftest.py 的写法作为基准，保持一致性
```

### Q2: PowerShell `switch` 语法错误

```
现象：run_perf.ps1 脚本报错，无法识别 switch 语法

根因：PowerShell 版本兼容性问题

修复：用 if/elseif 替代 switch
```

### Q3: 多类 User 并发 Token 冲突

```
现象：同时运行多个 User 类时，部分请求报 401

根因：多个 User 类的 on_start() 方法并发执行，Token 更新存在竞争条件

修复：每次只指定一个 User 类运行
  错误：locust -f locustfile.py --users 100
  正确：locust -f locustfile.py MallAdminUser --users 100
```

### Q4: JMeter JMX 文件兼容性问题

```
现象：JMeter 5.6.3 无法运行 .jmx 文件，报 XML 解析错误

根因：.jmx 文件从高版本生成，包含 5.6.3 不支持的 XML 元素

修复：手动编辑 .jmx 文件，删除不兼容的 XML 元素
  （<assertionsResults>、<threadCounts>、<idleTime>、<conectTime>、<sentBytes>）
```

### Q5: 变量名拼写错误

```
现象：Locust 运行时报 NameError: name 'SEARCH_KEY_WORDS' is not defined

根因：定义时是 SEARCH_KEYWORDS，使用时误写为 SEARCH_KEY_WORDS（多了一个下划线）

修复：全局搜索 SEARCH_KEY_WORDS，全部替换为 SEARCH_KEYWORDS
```

---

## 10. 常见问题排查

### Q1: Locust 报 `ConnectionRefusedError`

```
原因：后端没启动或端口不对
检查：
  1. mall-admin 是否启动？→ IDE 里看有没有报错
  2. 端口是否正确？→ curl http://localhost:8080
  3. 防火墙？→ Windows 本地一般不影响
```

### Q2: TPS 上不去，但 CPU 也很低

```
可能原因：Locust 压测机自己成了瓶颈（同一台机器）

解决方法：
  1. 用另一台机器运行 Locust（分布式模式）
  2. 或者降低 Locust 的日志级别
  3. 检查 Locust 是否启用了 --web-ui（GUI 模式更耗资源）
```

### Q3: 大量请求返回 404

```
原因：随机生成的 ID 在数据库中不存在

这是正常的设计 —— locustfile 中已经 catch_response=True
404 不算失败，模拟了"查看不存在的商品/订单"场景

如果要避免 404：
  - 先查询数据库获取真实 ID 范围
  - 或在 CSV 中准备有效 ID 列表
```

### Q4: 登录失败，所有请求都报 401

```
检查：
  1. 账号密码是否正确？→ admin / macro123
  2. token 格式是否正确？→ 看 Authorization header（注意 Bearer 后只能有一个空格）
  3. 后端是否重启过？→ token 可能失效
  → 解决：Locust 的 on_start 每次都会重新登录
```

### Q5: MySQL 连接数不足

```
错误信息：Too many connections

解决：
  # 1. 查看当前连接数
  SHOW VARIABLES LIKE 'max_connections';
  SHOW STATUS LIKE 'Threads_connected';

  # 2. 增大连接数
  SET GLOBAL max_connections = 500;

  # 3. 检查 Spring Boot 连接池配置
  # application.yml 中调整 HikariCP 的 maximum-pool-size
```

---

## 附录

### A. 测试数据检查清单

```
□ mall 后端已启动 (http://localhost:8080)
□ MySQL 数据库 mall 库有数据
□ 管理员账号 admin / macro123 可用
□ Locust 2.33.1 已安装
□ JMeter 5.x 已安装
□ 报告输出目录 performance/report/ 已创建
```

### B. 产出物清单

| 文件 | 说明 |
|------|------|
| `performance/locustfile.py` | Locust 压测脚本（核心，667 行） |
| `performance/plan.py` | 场景定义和配置 |
| `performance/run_perf.ps1` | 一键运行脚本 (PowerShell) |
| `performance/jmeter/mall_performance_test.jmx` | JMeter 测试计划（482 行） |
| `performance/report/*.html` | HTML 性能报告 |
| `PERFORMANCE_TEST_REPORT.md` | 完整性能测试总结报告 |

### C. 后续迭代方向

```
v2.1 (当前): 5 阶段完成，含实测数据
v2.2:      加入写入操作（创建/更新商品、处理订单）
v2.3:      参数化数据池（多账号轮换）
v2.4:      Prometheus + Grafana 实时监控
v2.5:      GitHub Actions CI 集成性能回归测试
```

---

*文档更新时间: 2026-06-14 · 工具: WorkBuddy*
