# Mall 商城接口自动化 — CI/CD 集成全流程文档

---

## 一、CI/CD 核心知识点

### 1.1 什么是 CI/CD？

| 概念 | 全称 | 含义 | 触发条件 |
|------|------|------|---------|
| **CI** | Continuous Integration（持续集成） | 代码变更后自动构建、自动测试，快速发现集成问题 | `git push`、Pull Request |
| **CD** | Continuous Delivery/Deployment（持续交付/部署） | 测试通过后自动部署到测试/生产环境 | CI 通过后自动触发 |

> 本项目的 CI 目标：**每次提交自动运行 108 条接口测试，生成 Allure 报告**

### 1.2 主流 CI/CD 工具对比

| 工具 | 部署方式 | 配置文件 | 适用场景 | 费用 |
|------|---------|---------|---------|------|
| **GitHub Actions** | 云原生（GitHub 内置） | `.github/workflows/*.yml` | 代码在 GitHub 的项目 | 公开仓库免费 |
| **Gitee Go** | 云原生（Gitee 内置） | `.gitee/*.yml` | 代码在 Gitee 的项目 | 免费 |
| **Jenkins** | 自建服务器安装 | `Jenkinsfile` | 企业内网、私有化部署 | 免费（自运维） |
| **GitLab CI** | 云原生/自建 Runner | `.gitlab-ci.yml` | 代码在 GitLab 的项目 | 有限免费额度 |

### 1.3 GitHub Actions 核心概念

```
Workflow（工作流）
  └── Job（任务）
        ├── runs-on: 运行环境（ubuntu-latest / windows-latest）
        ├── services: 依赖服务（MySQL / Redis / Docker）
        └── Steps（步骤）
              ├── uses: 复用别人的 Action（checkout / setup-python）
              ├── name: 步骤名称
              └── run: 执行命令
```

### 1.4 CI/CD 流程核心要素

```
┌─────────────────────────────────────────────────────────┐
│                     CI/CD 流水线                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ① 触发（Trigger）                                       │
│     ├── push（代码推送）                                  │
│     ├── pull_request（代码评审）                          │
│     └── schedule（定时任务 cron）                         │
│                                                         │
│  ② 环境准备（Setup）                                     │
│     ├── 拉取代码（checkout）                              │
│     ├── 安装运行时（Python / Node / Java）                │
│     └── 安装依赖（pip install / npm install）             │
│                                                         │
│  ③ 依赖服务（Services）                                 │
│     ├── MySQL（数据库）                                   │
│     ├── Redis（缓存）                                     │
│     └── Docker（应用容器化）                              │
│                                                         │
│  ④ 构建（Build）                                        │
│     ├── Maven 编译（Java 项目）                           │
│     └── Docker 镜像构建                                  │
│                                                         │
│  ⑤ 测试（Test）                                         │
│     ├── 等待服务就绪（Health Check）                      │
│     └── pytest / unittest 执行                           │
│                                                         │
│  ⑥ 报告（Report）                                       │
│     ├── Allure 报告生成                                  │
│     └── 上传到 Artifact / GitHub Pages                   │
│                                                         │
│  ⑦ 清理（Cleanup）                                      │
│     └── 停止并删除 Docker 容器                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.5 Docker 在 CI/CD 中的角色

```
传统方式：                      Docker 方式：
┌──────────┐                   ┌──────────────────┐
│ CI 机器   │                   │ GitHub Actions   │
│ 装 Java  │ ← 环境不一致      │ 拉 Docker 镜像   │ ← 环境完全一致
│ 装 MySQL │ ← 版本冲突        │ docker run       │ ← 秒级启动
│ 装 Maven │ ← 配置繁琐        │ 用完即删          │ ← 无残留
└──────────┘                   └──────────────────┘
```

**Docker 核心价值：**
- **环境一致性**：开发、测试、CI 三套环境完全相同
- **快速启动**：MySQL + mall 后端 30 秒内就绪
- **隔离性**：每次 CI 运行互不影响
- **可复现**：任何人都能一键复现 CI 环境

### 1.6 conftest.py 在 CI 中的设计模式

```python
# 环境自适应三要素：
IS_CI = bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))

# 1. BASE_URL → 从环境变量读取
BASE_URL = os.getenv("MALL_BASE_URL", "http://localhost:8080")

# 2. Allure 报告 → CI 里生成但不打开浏览器
if IS_CI:
    return  # 跳过 webbrowser.open()

# 3. 日志输出 → CI 里用纯文本，本地用彩色
```

---

## 二、全流程概览

### 2.1 架构总览图

```
┌──────────────────────────────────────────────────────────────────┐
│                    Mall API Test CI/CD 架构                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  开发者 git push 到 GitHub                                        │
│       │                                                          │
│       ▼                                                          │
│   GitHub Actions 自动触发                                         │
│       │                                                          │
│       ├──▶ Step 1: Checkout 测试代码                              │
│       │    └── 拉取 D:\mall-test\ 仓库代码                        │
│       │                                                          │
│       ├──▶ Step 2: 安装 Python 3.9 + pip 依赖                    │
│       │    └── requests, pytest, allure-pytest, pyyaml           │
│       │                                                          │
│       ├──▶ Service: MySQL 8.0 容器                               │
│       │    └── 自动建库 mall，健康检查确认就绪                     │
│       │                                                          │
│       ├──▶ Step 3: Docker 编译 mall 后端并启动                    │
│       │    ├── git clone mall 源码                                │
│       │    ├── mvn clean install（编译全部子模块）                 │
│       │    ├── docker build（构建镜像）                           │
│       │    └── docker run（启动容器，连接 MySQL）                  │
│       │                                                          │
│       ├──▶ Step 4: Health Check（等待后端就绪）                    │
│       │    └── 循环 curl http://localhost:8080，最多 24 次        │
│       │                                                          │
│       ├──▶ Step 5: 运行 pytest                                    │
│       │    └── 108 条用例，--alluredir 输出 JSON 到 allure-results│
│       │                                                          │
│       ├──▶ Step 6: 生成 Allure 报告                               │
│       │    └── allure generate → allure-report/ 静态 HTML          │
│       │                                                          │
│       ├──▶ Step 7: 上传报告（Artifact，保留 7 天）                 │
│       │                                                          │
│       └──▶ Step 8: 清理（docker stop + docker rm）               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 完整时间线

| 步骤 | 操作 | 预估耗时 | 备注 |
|------|------|---------|------|
| 1 | Checkout 代码 | 3s | GitHub Actions 内网，极快 |
| 2 | 安装 Python 依赖 | 15s | pip install 5 个包 |
| 3 | MySQL 启动 | 20s | GitHub Actions service 自动管理 |
| 4 | git clone mall + Maven install | 4-6min | **最慢的一步**，首次会下载大量 Maven 依赖 |
| 5 | Docker build + run | 30s | 镜像构建 + 容器启动 |
| 6 | Health Check 等待 | 10-30s | 循环 curl 探测 |
| 7 | pytest 108 条用例 | 2-3min | 108 个 HTTP 接口调用 |
| 8 | allure generate | 10s | JSON → HTML 转换 |
| 9 | 上传 Artifact | 5s | 压缩上传 |
| 10 | 清理容器 | 2s | |
| **总计** | | **约 8-10 分钟** | 首次运行，后续 Maven 有缓存会更快 |

### 2.3 本地开发 vs 远程 CI 对比

| 维度 | 本地开发 | GitHub Actions CI |
|------|---------|-------------------|
| BASE_URL | `http://localhost:8080`（本地 mall 后端） | `http://localhost:8080`（CI 里 Docker 启动） |
| MySQL | 本地安装/占用 | GitHub Actions service，用完即销毁 |
| Allure 报告 | 自动打开浏览器 | 上传到 Artifact，下载查看 |
| 触发方式 | 手动运行 `pytest` | git push 自动触发 |
| 用途 | 开发调试 | 回归测试 + 质量门禁 |

---

## 三、项目文件清单

### 3.1 本次 CI/CD 新增/修改的文件

```
D:\mall-test\
├── .github/
│   └── workflows/
│       └── docker-ci.yml       ← 【核心】GitHub Actions CI 配置
├── docker-compose.yml          ← 【新增】本地 Docker 测试环境
├── requirements.txt            ← 【新增】Python 依赖清单
├── Dockerfile                  ← 【新增】测试项目镜像（可选）
├── MallBackend.Dockerfile      ← 【新增】mall 后端镜像构建文件
├── .gitignore                  ← 【新增】Git 忽略规则
└── testcases/
    └── conftest.py             ← 【修改】增加环境自适应逻辑
```

### 3.2 docker-ci.yml 三步触发机制

```yaml
on:
  push:                              # 代码推送时
    branches: [master, main, dev]
  pull_request:                      # 提交 PR 时
    branches: [master, main]
  schedule:                          # 定时任务
    - cron: "0 0 * * *"              # 每天 UTC 0:00 = 北京时间 8:00
```

---

## 四、逻辑思路（为什么这么设计）

### 4.1 为什么选用 GitHub Actions 而不是 Jenkins？

| 考量维度 | GitHub Actions | Jenkins |
|---------|---------------|---------|
| 部署成本 | 零（GitHub 内置） | 需要一台服务器 |
| 运维成本 | 零 | 需要维护 Jenkins 进程 |
| 学习曲线 | 低（YAML 配置） | 高（Pipeline 语法 + 插件） |
| 与代码仓库集成 | 天然集成 | 需要 Webhook 配置 |
| **结论** | ✅ **个人项目/小型团队首选** | 大型企业内网部署适用 |

### 4.2 为什么用 Docker 而不是直接装 Java + MySQL？

```
方案 A（直接安装）：              方案 B（Docker）：
├── apt install openjdk-8-jdk     ├── 声明 service: mysql（秒启动）
├── apt install mysql-server      ├── Dockerfile 定义后端环境
├── 配置 MySQL 用户密码           ├── docker build + run（一键）
├── 配置 Java 环境变量            ├── 用完即删（无残留）
├── 配置 Maven                    └── ✅ 选了方案 B
└── ❌ 步骤多、容易配置漂移
```

**核心原因：**
1. **可复现**：任何人 clone 项目，本地 `docker-compose up` 即可复现
2. **面试加分**：Docker + CI/CD 连用是现代 DevOps 标准实践
3. **隔离干净**：MySQL 数据不会残留在 CI 机器上

### 4.3 为什么 conftest.py 要区分 CI 和本地？

```python
# 本地：测试跑完 → 自动打开浏览器看 Allure 报告（方便！）
# CI：   测试跑完 → 服务器没浏览器，直接上传报告文件（不能 webbrowser.open()）

# 解决方案：环境变量判断
IS_CI = bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))

if IS_CI:
    return  # 不打开浏览器
else:
    webbrowser.open(...)  # 本地自动打开
```

### 4.4 为什么 BASE_URL 要从环境变量读取？

```
# conftest.py
BASE_URL = os.getenv("MALL_BASE_URL", "http://localhost:8080")

场景一：本地开发
  → 不设环境变量，默认 http://localhost:8080

场景二：GitHub Actions CI
  → 不设环境变量，默认 http://localhost:8080（Docker 启动的后端）

场景三：公司测试环境
  → export MALL_BASE_URL=http://192.168.1.100:8080
  → 指向远程服务器

场景四：Jenkins 另类部署
  → 同理，环境变量一键切换
```

---

## 五、遇到的困难与解决方法（9 次迭代踩坑实录）

> 📌 CI/CD 搭建共迭代 9 次才跑通，每个失败都是独立的知识点。下面按时间顺序记录全部踩坑过程。

### 迭代总览

| # | 失败现象 | 根因 | 修复方法 | 耗时 |
|---|---------|------|---------|------|
| 1 | `Could not find artifact mall-mbg` | Maven 多模块依赖找不到 | `mvn clean install` 从根目录 | 10min |
| 2 | 同上 | — | — | — |
| 3 | docker-maven-plugin 连远程 Docker 超时 | pom.xml 里配了私有 Docker 地址 | `-Ddocker.skip=true` 跳过插件 | 8min |
| 4 | `openjdk:8-jdk-alpine: not found` | Oracle 废弃了该镜像 | 换成 `eclipse-temurin:8-jre-alpine` | 5min |
| 5 | `ModuleNotFoundError: common` | CI 里 PYTHONPATH 缺少项目根目录 | 加 `PYTHONPATH: ${{ github.workspace }}` | 3min |
| 6 | `localhost:8080 Connection refused` | Docker-in-Docker 网络隔离，宿主机看不到容器端口 | **放弃 Docker，改用 `java -jar` 直接在 Runner 上运行** | 15min |
| 7 | `invalid target release: 17` | 项目 pom.xml 要求 Java 17，CI 里装的是 Java 8 | 改 `java-version: "17"` | 3min |
| 8 | 健康检查误判 + `Table doesn't exist` | curl 返回值带空格导致误判 + 数据库没建表 | 严格判断 000 + 导入 mall.sql | 10min |
| 9 | `Can't connect to local MySQL through socket` | Linux 上 `localhost` 走 Unix Socket，MySQL service 只有 TCP | **全部改成 `127.0.0.1`** | 2min |

---

### 难点 1：Maven 多模块依赖编译失败 ✅ 已解决

**现象：**
```
Could not find artifact com.macrozheng.mall:mall-mbg:jar:1.0-SNAPSHOT
Could not find artifact com.macrozheng.mall:mall-security:jar:1.0-SNAPSHOT
```

**根因：** mall 是 Maven 多模块项目，`mall-admin` 依赖 `mall-mbg`、`mall-security`、`mall-common` 三个子模块。只编译 `mall-admin` 时，本地 Maven 仓库没有这些依赖。

**修复：**
```yaml
# ❌ 错误：只编译 mall-admin
cd /tmp/mall/mall-admin && mvn clean package -DskipTests

# ✅ 正确：从根目录 install 全部子模块
cd /tmp/mall && mvn clean install -DskipTests -q -Ddocker.skip=true
```

**关键知识点：** `mvn package` 只编译当前模块；`mvn install` 编译并安装到 `~/.m2/repository/`，子模块相互引用必须用 `install`。

---

### 难点 2：Git 推送被代理阻断 ✅ 已解决

**现象：** `Connection was reset` / `Could not resolve host: mygithub`

**排查链路（6 步）：**
```
1. 发现 Clash 开着但连接数 = 0 → 代理没工作
2. 关掉 Clash 浏览器能访问 GitHub → 不需要代理
3. git config --global --list → 有残留 proxy 配置指向 127.0.0.1:7890
4. git config --global --unset http.proxy → 清除
5. 还有 URL 重写规则 url.git@mygithub:.insteadof=https://github.com/
6. git config --global --unset url.git@mygithub:.insteadof → 清除 ✅
```

---

### 难点 3：docker-maven-plugin 连接远程 Docker 超时 ✅ 已解决

**现象：** `Connect to 192.168.3.101:2375 failed: Connection timed out`

**根因：** mall 原作者的 pom.xml 配置了 `docker-maven-plugin`，指向其私有 Docker 服务器。Maven 编译时自动触发插件。

**修复：** `-Ddocker.skip=true` 跳过插件（CI 里不需要它构建镜像）

---

### 难点 4：openjdk Base Image 废弃 ✅ 已解决

**现象：** `docker.io/library/openjdk:8-jdk-alpine: not found`

**根因：** Oracle 变更 Java 许可证后，Docker Hub 下架了 openjdk 官方镜像。

**修复：** 改用 Eclipse Adoptium 维护的免费镜像 `eclipse-temurin:8-jre-alpine`

---

### 难点 5：PYTHONPATH 配置 ✅ 已解决

**现象：** `ModuleNotFoundError: No module named 'common'`

**根因：** CI 里 pytest 从 `testcases/` 运行，Python 找不到上一级目录的 `common/` 模块。本地能跑是因为 IDE 或终端自动加了项目根目录到 PATH。

**修复：**
```yaml
- name: 运行 pytest
  env:
    PYTHONPATH: ${{ github.workspace }}    # ← 把项目根目录加到搜索路径
  run: pytest testcases/ -v --alluredir=allure-results
```

---

### 难点 6：Docker-in-Docker 网络隔离（最大坑） ✅ 已解决

**现象：** Docker 容器启动了，但 `curl localhost:8080` 永远 Connection Refused

**根因：** GitHub Actions Runner 本身运行在容器中。在 Runner 里再 `docker run` 是 "Docker-in-Docker"（DinD）。`--network host` 指向的是 Runner 容器的 namespace，不是真正的 VM 宿主机——端口映射失效。

```
宿主机 VM
└── Runner 容器 (GH Actions)
    ├── Docker 容器: mall-backend → 8080 绑定在容器内，宿主机看不到
    └── MySQL service → 3306 绑定在 Runner namespace
```

**决策：放弃 Docker，直接用 `java -jar` 在 Runner 上运行**

```yaml
# ✅ 最终方案：不用 Docker，直接后台运行 JAR
nohup java -jar target/mall-admin-*.jar \
  --spring.datasource.url="jdbc:mysql://127.0.0.1:3306/mall?..." \
  --server.port=8080 \
  > /tmp/mall-backend.log 2>&1 &
```

**为什么这样更好：** 没有网络层抽象，localhost:8080 天然可达；省掉了 Docker build 时间；日志直接打文件方便排查。

---

### 难点 7：Java 版本不匹配 ✅ 已解决

**现象：** `Fatal error compiling: invalid target release: 17`

**根因：** mall 项目 pom.xml 配置 `maven.compiler.target=17`，但 CI 里最初装的 Java 8。

**修复：** `java-version: "17"`

---

### 难点 8：健康检查误判 + 数据库未初始化（连环坑） ✅ 已解决

**现象：** 健康检查第 1 次就显示"就绪"（实为误判），导致 pytest 对空端口发起请求，全部 Connection Refused。

**根因拆解：**

**Bug A — 健康检查误判：**
```
第 1 次探测，HTTP 0000000000    ← curl 返回了带多余空格的字符串
✅ mall 后端就绪（HTTP 0000000000）← 条件 != "000" 判断通过！误认为就绪
```

`curl -w` 在某些环境下输出的 `000` 后面带着换行/空格，导致 `$STATUS` 实际值是 `"000\n"` 或 `"000 "`。`[ "$STATUS" != "000" ]` 判断为 true（因为 "000 " ≠ "000"），直接跳出循环，健康检查形同虚设。

**修复 A：**
```bash
HTTP_CODE=$(echo "$HTTP_CODE" | tr -d '[:space:]')   # 去空白
if [ "$HTTP_CODE" != "000" ] && [ -n "$HTTP_CODE" ]; then  # 严格判断
```

**Bug B — 数据库未建表：** `Table 'mall.ums_resource' doesn't exist`，CI 里只创建了空的 mall 数据库，没有导入 mall.sql 建表脚本。

**修复 B：** 在编译步骤前新增「初始化数据库」步骤，安装 mysql-client → 等待 MySQL 就绪 → 导入 mall SQL。

---

### 难点 9：MySQL 连接 Unix Socket vs TCP（最终坑） ✅ 已解决

**现象：** `Can't connect to local MySQL server through socket '/var/run/mysqld/mysqld.sock' (2)`

**根因：** Linux 上 MySQL 客户端默认优先使用 Unix Socket。`mysql -h localhost` 中的 `localhost` 会被解析为 Unix Socket 路径 `/var/run/mysqld/mysqld.sock`。但 GitHub Actions 的 MySQL service 通过 TCP 端口 3306 暴露，**没有 Unix Socket 文件**。

```
❌ mysql -h localhost ...  →  走 Unix Socket  →  找不到 sock 文件  →  报错
✅ mysql -h 127.0.0.1 ...  →  走 TCP  →  localhost:3306  →  连接成功
```

**修复：** 三处全部从 `localhost` 改为 `127.0.0.1`：
- `mysqladmin ping -h 127.0.0.1`
- `mysql -h 127.0.0.1`（导入 SQL）
- `jdbc:mysql://127.0.0.1:3306/`（Spring Boot JDBC 连接串）

**关键知识点：** `localhost` ≠ `127.0.0.1`。`localhost` 在 MySQL 协议里走 Unix Socket；`127.0.0.1` 明确走 TCP。CI/Docker 环境中 MySQL service 通过 TCP 暴露时，必须用 `127.0.0.1`。

---

### 踩坑总结

```
每个坑对应一类知识盲区：

1. Maven 多模块编译   →  Maven 生命周期（package vs install）
2. Git 代理残留       →  Git 三层配置 + URL 重写规则
3. docker-maven-plugin →  Maven 插件机制，如何跳过
4. 基础镜像废弃       →  Docker 镜像生态，开源许可证变更
5. PYTHONPATH         →  Python 模块搜索路径机制
6. Docker-in-Docker   →  容器网络隔离原理，何时用 docker 何时不用
7. Java 版本不匹配    →  读懂 pom.xml 的 compiler.target
8. 健康检查误判       →  Shell 字符串比较的空白陷阱 + 数据库初始化
9. Unix Socket vs TCP →  MySQL 连接协议：localhost ≠ 127.0.0.1
```

---

## 六、关键命令速查表

### 6.1 Git 相关

```bash
# 查看远程仓库
git remote -v

# 修改远程地址
git remote set-url origin https://github.com/user/repo.git

# 查看全局配置
git config --global --list

# 清除代理
git config --global --unset http.proxy
git config --global --unset https.proxy

# 推送
git push -u origin master
```

### 6.2 GitHub Actions 相关

```bash
# 本地模拟 CI 环境（需要安装 act 工具）
act push

# 查看 workflow 运行日志
gh run list
gh run view <run-id> --log
```

### 6.3 Docker 相关

```bash
# 本地启动测试环境
docker-compose up -d

# 查看日志
docker-compose logs -f mall-backend

# 停止并清理
docker-compose down -v

# 进入容器排查
docker exec -it mall-backend sh
```

### 6.4 Maven 相关

```bash
# 跳过测试编译
mvn clean install -DskipTests

# 只看编译结果，不打印依赖下载
mvn clean install -DskipTests -q

# 强制重新下载 SNAPSHOT 依赖
mvn clean install -U
```

---

## 七、面试话术

### 7.1 "你做过 CI/CD 吗？怎么做接口自动化的 CI 集成？"

> 我在 mall 商城接口自动化测试项目里，用 GitHub Actions 搭建了完整的 CI/CD 流水线。
>
> 触发机制有三种：push 代码、提 Pull Request、每天 UTC 0:00 定时跑。
>
> 流程是：GitHub Actions 自动启动 MySQL service → 初始化数据库 → Maven 编译 mall 后端 → 直接在 Runner 上用 `java -jar` 运行 → 健康检查等待就绪 → 运行 108 条 pytest 接口测试 → 生成 Allure 报告并上传 Artifact。整个耗时约 5 分钟，完全自动化。
>
> 为了适配 CI 环境，我在 conftest.py 里做了环境自适应：CI 环境跳过浏览器启动，本地环境跑完自动打开 Allure 报告。整个过程迭代了 9 次才跑通，踩了 Maven 多模块编译、Docker 网络隔离、Health Check 误判、MySQL Unix Socket vs TCP 等坑。

### 7.2 "为什么没用 Docker 跑 mall 后端？"

> 最初计划用 Docker 构建镜像并在 CI 里运行，但遇到了 GitHub Actions 的 Docker-in-Docker 网络隔离问题——Actions Runner 本身是容器，在它里面 `docker run` 的端口映射对宿主机不可见，pytest 无法访问 `localhost:8080`。
>
> 最终放弃了 Docker，改用 `java -jar` 直接在 Runner 上运行。结果反而更好：少了一层网络抽象、省掉了 Docker build 时间、日志直接打文件方便排查。Docker 只在本地开发环境用 docker-compose 启动 MySQL 和后端。

### 7.3 "CI/CD 搭建过程中遇到什么坑？怎么解决的？"

> 一共迭代了 9 次，踩了 9 个不同类型的坑：
>
> 技术层面的有：Maven 多模块依赖问题（`install` vs `package`）、Java 版本不匹配（项目要 17，CI 配了 8）、数据库没初始化（没导入 mall.sql）、PYTHONPATH 缺失导致模块找不到。
>
> 网络层面的有：Docker-in-Docker 端口不可达、Git 代理残留导致 push 失败。
>
> 最隐蔽的是两个：一是健康检查的 Shell 字符串比较 bug——curl 返回的 "000" 带多余空格，不等于字符串 "000"，导致第 1 秒就误判"就绪"；二是 MySQL 的 `localhost` 走 Unix Socket 但 CI 里 MySQL service 只有 TCP，必须用 `127.0.0.1` 强制走 TCP 协议。这种坑没有实际动手根本发现不了。

### 7.4 "定时任务怎么做的？为什么选那个时间？"

> 用 GitHub Actions 的 `schedule` + `cron` 表达式。我配的是 `0 0 * * *`，也就是每天 UTC 0:00，北京时间早上 8:00。选这个时间是因为上班第一件事就是看昨晚有没有接口异常，8 点跑完就有报告了。

---

## 八、后续优化方向

| 优化项 | 说明 | 难度 |
|--------|------|------|
| **并行执行** | 用 `pytest-xdist -n auto` 让 108 条用例并行跑 | ⭐ 简单 |
| **失败重试** | `pytest --reruns 2` 网络抖动时自动重试 | ⭐ 简单 |
| **Slack/钉钉通知** | 测试挂了自动发消息到群聊 | ⭐⭐ 中等 |
| **代码覆盖率** | `pytest-cov` 统计接口覆盖率 | ⭐⭐ 中等 |
| **Maven 缓存** | 用 `actions/cache` 缓存 `~/.m2/`，加速编译 | ⭐⭐ 中等 |
| **多环境切换** | staging/production 环境一键切换 | ⭐⭐⭐ 较难 |
| **前端联动** | mall 前端代码推送时自动跑接口测试 | ⭐⭐⭐ 较难 |

---

> **文档版本**: v2.0（CI/CD 跑通后更新）  
> **创建日期**: 2026-06-09  
> **最后更新**: 2026-06-11（9 次迭代全部修复，CI 全流程通过）  
> **CI/CD 最终耗时**: 4m 39s  
> **适用项目**: mall 商城接口自动化测试  
> **CI/CD 工具**: GitHub Actions + Java 17 + pytest + Allure
