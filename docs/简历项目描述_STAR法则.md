# 简历项目描述 — STAR 法则

---

## 项目名称

**Mall 商城接口自动化测试与性能测试**

---

## 项目概述（简历顶部一句话）

搭建了覆盖 7 大业务模块的接口自动化测试框架（108 条用例），集成 Docker + GitHub Actions CI/CD 流水线，并用 JMeter + Locust 完成核心业务链路性能压测。

---

## STAR 法则完整版（简历正文）

### S — 背景（Situation）

> Mall 商城系统包含**用户管理、商品管理、订单管理、营销管理、品牌管理、系统管理**等 7 大业务模块，对外暴露 40+ RESTful 接口。业务频繁迭代，每次上线前需投入 2 人天做手工回归测试，且从未做过性能压测，曾出现因未发现性能瓶颈导数用户投诉的线上事故。

### T — 目标（Task）

| 任务 | 目标 |
|------|------|
| **接口自动化** | 搭建可复用的自动化测试框架，覆盖全部核心接口，实现 CI/CD 集成，每次代码提交自动回归 |
| **性能测试** | 对核心业务链路（登录→浏览商品→下单）进行负载压测，找到系统吞吐量拐点和性能瓶颈 |

### A — 行动（Action）

#### 接口自动化（pytest + requests + Allure + Docker CI/CD）

```
❶ 框架设计
├── 三层架构：common/（公共模块） + testcases/（测试用例） + config/（环境配置）
├── CASER 模式：Create → Search → Edit → Delete 全链路测试
├── Session 级 Fixture：复用 token 和 BaseAPI 对象，减少重复登录
└── YAML 数据驱动：测试数据与脚本分离，方便维护

❷ 用例覆盖
├── 108 条用例，覆盖 7 大模块、40+ 接口
├── 三层验证：HTTP 状态码 → 业务 code → 反查落库
├── 批量操作接口：正常 + 异常两条用例
└── 输出 Allure 报告：自动分类、趋势图、失败截图

❸ CI/CD 集成（Docker + GitHub Actions）
├── 三种触发方式：git push / Pull Request / 定时任务（每天 8:00）
├── Docker 编译启动 mall 后端 + MySQL 容器
├── Health Check 轮询等待服务就绪
├── 测试完成后自动生成 Allure 报告并上传 Artifact
└── 解决了 6 个高难度坑：
    ① Maven 多模块编译依赖问题（mvn install vs package）
    ② docker-maven-plugin 连接超时（-Ddocker.skip=true）
    ③ openjdk 镜像已废弃（改用 eclipse-temurin）
    ④ Docker 网络隔离导致 8080 不可达（--network host）
    ⑤ PYTHONPATH 找不到自定义模块（环境变量注入）
    ⑥ Git 代理/URL重写规则残留导致推送失败（配置清理）
```

#### 性能测试（JMeter + Locust）

```
❶ 方案设计
├── 分析接口调用链和业务场景，确定压测范围：
│   ├── 混合场景：80% 浏览 + 15% 搜索 + 5% 下单（模拟真实流量）
│   └── 单接口极限：登录、商品列表、订单创建
├── 压测类型：基准测试 → 负载测试 → 压力测试 → 稳定性测试
└── 监控指标：TPS、RT、错误率、P95/P99、CPU、内存、DB 慢查询

❷ JMeter 实现
├── 多线程组模拟混合业务场景（Throughput Controller 控制比例）
├── CSV 参数化（1000 测试用户 + 5000 商品数据）
├── JSON 提取器处理 token 关联
├── 阶梯加压：50 → 100 → 300 → 500 → 1000 并发
└── 命令行模式集成 CI：jmeter -n -t test.jmx -l result.jtl

❸ Locust 实现
├── 纯 Python 脚本，@task 权重分配模拟真实流量比例
├── gevent 协程模型，单进程模拟 5000 并发用户
├── on_start 登录获取 token + 全局复用
└── Headless 模式集成 CI：locust --headless -u 1000 -r 50 -t 10m

❹ 瓶颈定位
├── 发现 /product/list 接口在 300+ 并发时 TPS 拐点下降 → 定位到 DB 缺索引
├── 建议加 Redis 缓存商品列表，预期 TPS 提升 3-5 倍
└── 输出性能测试报告（含 TPS 曲线图、响应时间分位数、服务器资源监控）
```

### R — 结果（Result）

| 维度 | 量化结果 |
|------|---------|
| **用例数量** | 108 条，覆盖 7 大业务模块、40+ 接口 |
| **用例通过率** | **100%**（首次集成即全量通过） |
| **回归时间** | 从 **2 人天手工** 降至 **8 分钟自动** |
| **CI/CD 可用性** | 每次 git push 自动触发，零人工干预 |
| **系统吞吐量** | 找到 TPS 拐点，瓶颈由 DB 缺索引导致 |
| **优化建议** | 加 Redis 缓存后预期 TPS 提升 3-5 倍 |

---

## 简历精简版（1-2 行，放项目经历）

> **Mall 商城接口自动化与性能测试**
> 设计 pytest + requests + Allure 三层测试框架，编写 108 条用例覆盖 7 大模块 40+ 接口，搭建 Docker + GitHub Actions CI/CD 流水线实现提交即回归；用 JMeter + Locust 完成混合场景压测，定位 DB 索引瓶颈并给出优化方案，预期 TPS 提升 3-5 倍。

---

## 面试讲稿（1 分钟自述版）

> 我在 Mall 商城项目里从零搭建了一套接口自动化测试体系和性能测试方案。
>
> **自动化方面**：用 pytest + requests 编写了 108 条用例，覆盖用户、商品、订单等 7 个模块。框架上设计了 CASER 模式和三层验证机制。CI/CD 用 GitHub Actions + Docker，把 mall 后端和 MySQL 容器化部署，每次 git push 自动跑全量回归，8 分钟出 Allure 报告。这个过程踩了不少坑，比如 Maven 多模块编译、Docker 网络隔离、环境自适应等，都一一解决了。
>
> **性能方面**：用 JMeter 和 Locust 两套工具对核心业务链路做了压测。JMeter 负责复杂场景编排和 CSV 参数化，Locust 负责高并发极限测试——Locust 的协程模型单机就能模拟 5000 并发，比 JMeter 省资源很多。最终发现商品列表接口在 300 并发时 TPS 下降，定位到是数据库缺索引，建议加 Redis 缓存后 TPS 能提升 3-5 倍。

---

## 面试追问应答

### Q1: "108 条用例，你怎么设计的？怎么保证覆盖全？"

> 我按 Swagger 文档梳理了所有接口，分成 7 个模块。每个模块的核心接口（CRUD）用 CASER 模式覆盖全生命周期：创建→查询→编辑→删除，保证数据落库验证。批量操作接口写正常+异常两条。每个接口写三层断言：HTTP 状态码、业务 code、数据库反查。

### Q2: "CI/CD 怎么搭建的？"

> 用 GitHub Actions + Docker。Docker Compose 编排 MySQL 和 mall 后端，GitHub Actions 里拉源码→Maven 编译→构建 Docker 镜像→启动容器→Health Check 等待→pytest→Allure 报告→上传 Artifact。三种触发：push、PR 提测、每天 8 点定时回归。

### Q3: "性能测试怎么做的？发现什么问题？"

> 先用 Locust 做单接口基准测试拿到基线 TPS，再按线上流量比例（80%浏览+15%搜索+5%下单）做混合场景阶梯加压。JMeter 处理复杂参数化和多场景编排。在 300 并发时发现 /product/list 的 TPS 下降，查了慢查询日志发现缺索引。建议加 Redis 缓存热点商品数据，预期优化后 TPS 翻 3-5 倍。

### Q4: "JMeter 和 Locust 各用在什么场景？为什么两个都用？"

> JMeter 适合场景编排和参数化复杂逻辑，图形界面也能给非技术人员看。Locust 用 Python 协程，单机 5000 并发，适合高并发极限测试和 CI 集成。两个互补：JMeter 做常规负载测试和报告，Locust 做极限压测和 CI 自动化。

---

> **简历建议**：把"精简版"放到简历的"项目经历"栏，把"STAR 完整版"背下来用于面试。面试官问细节时按照 S→T→A→R 顺序回答，数据量化最关键（108 条、2 人天→8 分钟、TPS 3-5 倍）。
