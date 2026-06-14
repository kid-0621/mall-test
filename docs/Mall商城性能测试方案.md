# Mall 商城性能测试方案

---

> **文档性质**: 性能测试方案（测试计划）  
> **测试对象**: Mall 商城后端 API  
> **测试工具**: JMeter + Locust  
> **文档版本**: v1.0  
> **创建日期**: 2026-06-11

---

## 一、测试目标

### 1.1 业务目标

| 目标 | 说明 |
|------|------|
| **验证系统容量** | 确认当前架构能支撑的最大并发用户数和吞吐量 |
| **发现性能瓶颈** | 定位 CPU、内存、数据库、网络等层面的瓶颈点 |
| **提供优化建议** | 给出可落地的性能优化方案和预期效果 |
| **建立基线数据** | 为后续版本迭代提供性能对比基准 |

### 1.2 技术指标

| 指标 | 目标值 |
|------|--------|
| 核心接口 P95 响应时间 | < 500ms |
| 混合场景目标 TPS | ≥ 500 |
| 错误率 | < 0.1% |
| 500 并发下 CPU | < 80% |
| 稳定性测试时长 | 2 小时无内存泄漏 |

---

## 二、测试范围

### 2.1 测试接口清单

| 模块 | 接口 | 方法 | 场景权重 | 优先级 |
|------|------|------|---------|--------|
| **用户管理** | `/admin/login` | POST | 1% | P0 |
| **商品管理** | `/product/list` | GET | 40% | P0 |
| **商品管理** | `/product/{id}` | GET | 15% | P0 |
| **订单管理** | `/order/list` | GET | 10% | P1 |
| **订单管理** | `/order/generateOrder` | POST | 3% | P1 |
| **营销管理** | `/home/content` | GET | 10% | P1 |
| **品牌管理** | `/brand/list` | GET | 10% | P1 |
| **商品分类** | `/productCategory/list/{parentId}` | GET | 10% | P2 |
| **订单管理** | `/returnReason/list` | GET | 1% | P2 |

### 2.2 核心业务链路

```
用户行为链路（模拟真实用户）:

登录 → 浏览商品列表 → 搜索商品 → 查看商品详情 → 加入购物车 → 下单 → 查看订单
 1%       40%           15%          10%           5%         3%       1%
```

---

## 三、测试策略

### 3.1 测试类型与阶段

```
Phase 1: 基准测试（Benchmark）
├── 1 个并发用户，各接口单独压测 5 分钟
├── 目的：拿到单用户基线 TPS 和 RT
└── 工具：Locust

Phase 2: 负载测试（Load Test）
├── 模拟线上正常流量（500 并发），跑 10 分钟
├── 目的：验证系统在日常负载下表现正常
└── 工具：JMeter（混合场景）

Phase 3: 压力测试（Stress Test）
├── 阶梯加压：50 → 100 → 200 → 300 → 500 → 800 → 1000
├── 目的：找到系统 TPS 拐点和极限吞吐量
└── 工具：Locust

Phase 4: 稳定性测试（Soak Test）
├── 300 并发持续 2 小时
├── 目的：检测内存泄漏、连接池耗尽、GC 异常
└── 工具：JMeter

Phase 5: 峰值测试（Spike Test）
├── 瞬间从 100 → 1000 并发
├── 目的：验证系统应对突发流量的能力（秒杀场景）
└── 工具：Locust
```

### 3.2 加压策略

```
阶梯加压曲线:

并发数
1000 │                               ●───● (峰值测试)
 800 │                          ●───┘
 500 │                     ●───┘
 300 │                ●───┘              ●═══════════● (稳定性测试)
 200 │           ●───┘
 100 │      ●───┘
  50 │ ●───┘
  1  │●
     └────────────────────────────────────────────────→ 时间
        Phase1  Phase2      Phase3          Phase4     Phase5
```

---

## 四、测试环境

### 4.1 硬件配置

| 组件 | 配置 | 说明 |
|------|------|------|
| **应用服务器** | 4C8G, 50G SSD | 部署 mall 后端 |
| **数据库服务器** | 4C8G, 100G SSD | MySQL 8.0 |
| **压测机 1** | 4C8G | JMeter 主控 |
| **压测机 2** | 2C4G | Locust Worker（分布式） |

### 4.2 软件版本

| 软件 | 版本 |
|------|------|
| mall 后端 | 1.0-SNAPSHOT（Spring Boot 2.x） |
| MySQL | 8.0 |
| JDK | 8 |
| JMeter | 5.6.2 |
| Locust | 2.31.x |
| 操作系统 | Ubuntu 22.04 / Windows Server 2019 |

### 4.3 Docker 部署命令

```bash
# 应用 + 数据库一键部署
docker-compose up -d

# 查看资源使用
docker stats
```

---

## 五、测试数据准备

### 5.1 数据量级

| 数据类型 | 数量 | 用途 |
|---------|------|------|
| 测试用户 | 1,000 | 登录和 token 生成 |
| 商品数据 | 5,000 | 商品列表查询 |
| 已生成订单 | 10,000 | 订单查询（模拟历史数据） |
| 品牌数据 | 50 | 品牌查询 |

### 5.2 参数化文件

CSV 格式 (`test_users.csv`)：

```csv
username,password
testuser001,123456
testuser002,123456
...
testuser1000,123456
```

---

## 六、监控方案

### 6.1 监控指标

| 层面 | 指标 | 工具 | 告警阈值 |
|------|------|------|---------|
| **应用层** | TPS、RT、错误率 | JMeter Dashboard / Locust Web UI | RT P95 > 1s |
| **系统层** | CPU、内存、磁盘 IO | `top`, `free`, `iostat` | CPU > 85% |
| **JVM** | 堆内存、GC 频率 | `jstat`、VisualVM | Full GC > 1次/min |
| **数据库** | 慢查询、连接数、QPS | `SHOW PROCESSLIST`、慢查询日志 | 慢查询 > 200ms |
| **网络** | 带宽、丢包 | `iftop`, `nload` | 带宽 > 80% |

### 6.2 监控脚本

```bash
# 压测期间实时采集
while true; do
  echo "=== $(date) ==="
  top -bn1 | head -5                    # CPU + 内存
  mysql -uroot -proot -e "SHOW PROCESSLIST" | wc -l  # MySQL 连接数
  sleep 10
done
```

---

## 七、测试用例

### 7.1 JMeter 混合场景脚本结构

```
Test Plan: Mall 商城混合压测
├── setUp Thread Group（初始化）
│   └── 批量登录获取 token → 写入 JMeter 属性
│
├── Thread Group: 浏览商品（40% 比例）
│   ├── Throughput Controller (40%)
│   ├── HTTP Request: GET /product/list
│   └── Constant Timer: 500ms 思考时间
│
├── Thread Group: 搜索商品（15%）
│   ├── Throughput Controller (15%)
│   ├── HTTP Request: GET /product/{id}
│   └── Uniform Random Timer: 200~800ms
│
├── Thread Group: 查看订单（10%）
│   ├── Throughput Controller (10%)
│   └── HTTP Request: GET /order/list
│
├── Thread Group: 浏览品牌（10%）
│   └── HTTP Request: GET /brand/list
│
├── Thread Group: 下单（3%）
│   ├── Throughput Controller (3%)
│   ├── HTTP Request: POST /order/generateOrder
│   └── JSON Extractor: 提取订单号
│
├── Thread Group: 登录（1%）
│   └── HTTP Request: POST /admin/login
│
└── Listener
    ├── Aggregate Report（汇总表 → 核心数据）
    ├── Response Time Graph（趋势图）
    └── Transactions per Second（TPS 图）
```

### 7.2 Locust 混合场景脚本

```python
# mall_locust_mixed.py
from locust import HttpUser, task, between, constant_pacing
import random

class MallUser(HttpUser):
    # 模拟真实用户操作间隔（恒定吞吐量模式）
    wait_time = constant_pacing(2)     # 每 2 秒发一次请求

    def on_start(self):
        """每个用户启动时登录"""
        resp = self.client.post("/admin/login", json={
            "username": f"testuser{random.randint(1, 1000):03d}",
            "password": "macro123"
        })
        data = resp.json().get("data", {})
        self.token = data.get("tokenHead", "") + data.get("token", "")
        self.headers = {"Authorization": self.token}

    @task(40)       # 权重 40 — 浏览商品（最频繁）
    def browse_products(self):
        self.client.get("/product/list",
            params={"pageNum": random.randint(1, 10), "pageSize": 20},
            headers=self.headers, name="/product/list")

    @task(15)       # 权重 15 — 查看商品详情
    def view_product(self):
        self.client.get(f"/product/{random.randint(1, 100)}",
            headers=self.headers, name="/product/{id}")

    @task(10)       # 权重 10 — 浏览品牌
    def browse_brands(self):
        self.client.get("/brand/list",
            params={"pageNum": 1, "pageSize": 20},
            headers=self.headers, name="/brand/list")

    @task(10)       # 权重 10 — 查看首页内容
    def home_content(self):
        self.client.get("/home/content",
            headers=self.headers, name="/home/content")

    @task(10)       # 权重 10 — 查看订单
    def view_orders(self):
        self.client.get("/order/list",
            params={"pageNum": 1, "pageSize": 10},
            headers=self.headers, name="/order/list")

    @task(10)       # 权重 10 — 商品分类
    def browse_categories(self):
        self.client.get("/productCategory/list/0",
            headers=self.headers, name="/productCategory/list")

    @task(3)        # 权重 3 — 下单（低频）
    def create_order(self):
        self.client.post("/order/generateOrder", json={
            "orderItemList": [{
                "productId": random.randint(1, 50),
                "productQuantity": 1
            }]
        }, headers=self.headers, name="/order/generateOrder")

    @task(1)        # 权重 1 — 退货原因查询
    def return_reasons(self):
        self.client.get("/returnReason/list",
            params={"pageNum": 1, "pageSize": 10},
            headers=self.headers, name="/returnReason/list")

    @task(1)        # 权重 1 — 重新登录
    def re_login(self):
        self.on_start()
```

---

## 八、执行计划

### 8.1 测试日程

| 日期 | 阶段 | 内容 | 负责人 | 预计耗时 |
|------|------|------|--------|---------|
| D1 | 环境搭建 | Docker 部署 mall + MySQL，安装 JMeter/Locust | 测试 | 0.5 天 |
| D1 | 数据准备 | 生成 1000 用户 + 5000 商品数据 | 测试 | 0.5 天 |
| D2 | Phase 1 | 基准测试（单接口基线） | 测试 | 0.5 天 |
| D2-D3 | Phase 2 | 负载测试（混合场景，500 并发） | 测试 | 1 天 |
| D3 | Phase 3 | 压力测试（阶梯加压，找拐点） | 测试 | 0.5 天 |
| D4 | Phase 4 | 稳定性测试（2 小时长跑） | 测试 | 0.5 天 |
| D4 | Phase 5 | 峰值测试（突发流量） | 测试 | 0.5 天 |
| D5 | 分析报告 | 数据汇总、瓶颈分析、优化建议 | 测试 | 1 天 |

### 8.2 Locust 执行命令

```bash
# 基准测试（单接口）
locust -f mall_locust_mixed.py --host=http://localhost:8080 \
  --headless -u 1 -r 1 -t 5m --csv=results/benchmark

# 负载测试（500 并发）
locust -f mall_locust_mixed.py --host=http://localhost:8080 \
  --headless -u 500 -r 50 -t 10m --csv=results/load_500

# 压力测试（阶梯到 1000 并发）
locust -f mall_locust_mixed.py --host=http://localhost:8080 \
  --headless -u 1000 -r 100 -t 15m --csv=results/stress_1000

# 分布式压测（3 台 Worker）
# Master
locust -f mall_locust_mixed.py --master --host=http://localhost:8080
# Worker × 3
locust -f mall_locust_mixed.py --worker --master-host=<master_ip>
```

### 8.3 JMeter 执行命令

```bash
# GUI 模式（调试脚本）
jmeter -t mall_mixed_test.jmx

# 命令行模式（正式执行）
jmeter -n -t mall_mixed_test.jmx -l results/mixed_500.jtl \
  -Jthreads=500 -Jrampup=60 -Jduration=600 \
  -e -o report/mixed_500/

# CI 集成
jmeter -n -t mall_mixed_test.jmx -l results/ci_test.jtl \
  -e -o report/ci_test/ -Jthreads=100 -Jduration=120
```

---

## 九、风险与预案

| 风险 | 影响 | 预案 |
|------|------|------|
| 压测机资源不足 | 达不到目标并发 | 用 Locust 分布式（1 Master + 3 Worker） |
| 数据库被压垮 | 影响测试环境 | 压测前备份数据库，压测后恢复 |
| 压测导致线上问题 | 测试环境影响生产 | 严格隔离测试环境和生产环境网络 |
| 脚本断言误报 | 数据不可信 | 压测前小流量验证脚本正确性 |

---

## 十、预期结果与输出物

### 10.1 测试交付物

| 交付物 | 格式 | 说明 |
|--------|------|------|
| **性能测试报告** | PDF / Markdown | 含所有阶段的 TPS、RT、错误率汇总 |
| **TPS 并发曲线图** | PNG | 展示 TPS 随并发数变化趋势 |
| **响应时间分位数图** | PNG | P50/P90/P95/P99 对比 |
| **资源监控截图** | PNG | CPU、内存、MySQL 连接数趋势 |
| **瓶颈分析报告** | Markdown | 具体瓶颈点 + 优化方案 + 预期效果 |
| **压测脚本** | .py / .jmx | JMeter + Locust 完整脚本 |

### 10.2 预期发现

| 瓶颈点（假设） | 现象 | 解决方案 | 预期收益 |
|--------------|------|---------|---------|
| DB 缺少索引 | 300 并发时 `/product/list` RT 飙升 | 加联合索引 | TPS +50% |
| 无缓存 | 商品列表每次查 DB | 加 Redis 缓存 | TPS +300% |
| 连接池不足 | 500 并发出现 `Connection timeout` | 调大连接池 + 连接超时 | 错误率从 5%→0.1% |
| JVM GC 频繁 | Full GC 导致 RT 毛刺 | 调 JVM 堆内存参数 | P99 RT -60% |

---

## 十一、附录：关键概念速查

| 术语 | 说明 |
|------|------|
| **TPS** (Transactions Per Second) | 每秒处理事务数，核心吞吐量指标 |
| **RT** (Response Time) | 响应时间，从发请求到收完响应 |
| **P95** | 95% 的请求在此时间内完成 |
| **Ramp-Up** | 爬坡时间，逐步加压避免"冲击效应" |
| **Think Time** | 用户操作间隔，模拟真实操作节奏 |
| **拐点** | TPS 不再随并发增长的点 = 系统瓶颈 |
| **Headless** | 无界面模式，用于 CI 集成 |

---

> **文档版本**: v1.0 | **创建日期**: 2026-06-11  
> **后续步骤**: 在 GitHub Actions 中增加一个 `performance-test` job，代码合并到 master 前自动跑轻量压测验证性能不退化。
