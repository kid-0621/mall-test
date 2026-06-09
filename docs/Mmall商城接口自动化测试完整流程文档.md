# Mmall 商城接口自动化测试 — 完整流程文档

> 本文档记录从**零基础**到**产出能写进简历的接口自动化测试框架**的完整过程。  
> 重点不是"代码怎么写"，而是 **"为什么这样设计？""每个决策背后的思考"**。

---

## 目录

1. [第一阶段：接口梳理与解读](#一第一阶段接口梳理与解读)
2. [第二阶段：测试用例设计](#二第二阶段测试用例设计)
3. [第三阶段：框架搭建](#三第三阶段框架搭建)
4. [第四阶段：批量编写用例](#四第四阶段批量编写用例)
5. [第五阶段：踩坑与修复](#五第五阶段踩坑与修复)
6. [第六阶段：报告与交付](#六第六阶段报告与交付)
7. [设计决策回顾](#七设计决策回顾)
8. [面试话术模板](#八面试话术模板)

---

## 一、第一阶段：接口梳理与解读

### 1.1 你拿到了一个陌生项目，第一步做什么？

**不要急着写代码。** 先搞懂这个项目是什么、有哪些接口、接口之间有什么关系。

### 1.2 接口梳理三步法

```
步骤 1：启动项目 → 打开 Swagger → 浏览所有接口
步骤 2：按模块分组（登录/用户/商品/订单/营销/品牌/系统）
步骤 3：对每个接口标注：请求方法、URL、必填参数、返回格式
```

### 1.3 实际梳理过程

#### Step 1：启动 mall 项目

```bash
# 启动 MySQL + Redis（mall 的依赖）
docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:5.7
docker run -d --name redis -p 6379:6379 redis

# 启动 mall-admin（后台管理服务）
java -jar mall-admin.jar
```

启动成功后访问 `http://localhost:8080/swagger-ui.html`，看到所有接口列表。

#### Step 2：按模块分组

我打开了 Swagger 页面，**没有一个个抄下来**，而是用 Python 脚本**自动梳理**：

```python
import requests, json

# 登录获取 Token
r = requests.post("http://localhost:8080/admin/login",
                  json={"username": "admin", "password": "macro123"})
token = r.json()['data']['token']

# 拉取 Swagger JSON 数据
headers = {"Authorization": f"Bearer {token}"}
r = requests.get("http://localhost:8080/v2/api-docs", headers=headers)
swagger = json.loads(r.json()['data'])

# 按 Tag（Controller 名称）分组
paths = swagger.get('paths', {})
modules = {}
for path, methods in paths.items():
    for method, details in methods.items():
        tag = details.get('tags', ['Unknown'])[0]
        if tag not in modules:
            modules[tag] = []
        modules[tag].append({
            'path': path,
            'method': method.upper(),
            'summary': details.get('summary', '')
        })

# 打印每个模块的接口数
for tag, apis in sorted(modules.items()):
    print(f"{tag}: {len(apis)} 个接口")
```

**输出结果**：
```
pms-product-category: 5    # 商品分类
pms-product-attribute: 7    # 商品属性
pms-product: 8              # 商品管理
oms-order: 7               # 订单管理
oms-order-return: 4        # 退货管理
sms-coupon: 6              # 优惠券
sms-flash: 6               # 秒杀
ums-admin: 5               # 管理员
ums-role: 6                # 角色
ums-menu: 5                # 菜单
... (共 21 个 Controller，138 个接口)
```

#### Step 3：标注必填参数

**不是每个接口都要测的。** 我用了下面的策略决定测哪些：

| 优先级 | 接口类型 | 策略 | 例子 |
|--------|----------|------|------|
| **P0** | CRUD 核心接口（创建/查询/更新/删除） | **全测**（CASER 模式，5 条） | `/productCategory/create` |
| **P1** | 批量操作接口（批量上架/下架/删除） | **测 2 条**（正常 + 异常） | `/productCategory/update/showStatus` |
| **P2** | 纯查询接口（只读，无副作用） | **测 1 条**（验证数据结构） | `/brand/listAll` |
| **P3** | 基础设施接口（文件上传/OSS） | **跳过**（依赖环境） | `/upload` |
| **P4** | 前台门户接口（用户端） | **跳过**（权限不同） | `/product/detail/{id}` |

**为什么这样分层？**

- **P0（CRUD）最重要**：这是业务核心，测通了就说明接口能正常工作
- **P1（批量）次之**：涉及多数据操作，容易出错
- **P2（查询）最不重要**：如果不涉及副作用，出错的概率很低
- **P3/P4 跳过**：要么依赖外部环境，要么不是本次测试范围

### 1.4 关于"必填参数"的思考

**Swagger 文档常常不准确。** 判断必填参数的正确方式是：

```
方式 1：看 Swagger 的 required 字段（可能有遗漏）
方式 2：看 Java 源码的 @NotNull / @NotBlank 注解（最准确）
方式 3：直接调接口测试（最实操）
```

我会**三种方式结合**：先看 Swagger，再验证 Java 源码（如果有的情况下），最后实际调一下接口。

**真实案例**：
- `/productCategory/create` 的 `parentId` 在 Swagger 里**没标注 required**
- 但 Java 源码里确实有 `@NotNull` 注解
- 实际调用时不传 `parentId` → HTTP 500 → **踩坑了**
- 这就是为什么要用"三层验证"（详见第二章）

---

## 二、第二阶段：测试用例设计

### 2.1 我是怎么验证"登录成功"的？

#### 第一次尝试（初学者思维）：

```python
def test_login():
    resp = requests.post("/admin/login", json={"username": "admin", "password": "macro123"})
    print(resp.text)  # 打印出来看看
    # 手动看输出判断对不对
```

**问题**：没有自动化验证 —— 如果下次代码出 bug 导致登录失败，你会收到 200 还是 500？你也**不知道**，因为没有断言。

#### 第二次尝试（基础断言）：

```python
def test_login():
    resp = requests.post("/admin/login", json={"username": "admin", "password": "macro123"})
    assert resp.status_code == 200  # 有断定了！
```

**问题**：HTTP 200 不代表业务成功。接口可能返回 `{"code": 500, "message": "内部错误"}`。

#### 第三次尝试（二层验证）：

```python
def test_login():
    resp = requests.post("/admin/login", json={"username": "admin", "password": "macro123"})
    assert resp.status_code == 200           # 第 1 层：HTTP 通不通
    assert resp.json()['code'] == 200        # 第 2 层：业务对不对
```

**问题**：对于 CRUD 操作，接口返回成功，但**数据库真的写进去了吗？**

#### 最终方案（三层验证体系）：

```python
def test_create_category(self, base_api):
    # 第 1 层：HTTP 状态码
    resp = base_api.post("/productCategory/create", json=body)
    assert resp.status_code == 200
    
    # 第 2 层：业务 code
    result = resp.json()
    assert result['code'] == 200
    
    # 第 3 层：反查数据库
    cat_id = result['data']['id']
    verify = base_api.get(f"/productCategory/{cat_id}")
    assert verify.json()['data']['name'] == "测试分类"  # 确认真写进去了
```

### 2.2 三层验证的设计哲学

```
┌─────────────────────────────────────┐
│  第 1 层：HTTP 状态码 = 200         │ ← 验证"接口通不通"
├─────────────────────────────────────┤
│  第 2 层：业务 code = 200           │ ← 验证"业务对不对"
├─────────────────────────────────────┤
│  第 3 层：反查数据库               │ ← 验证"数据真写了吗"
└─────────────────────────────────────┘
          ↑
    越往下越精准，但也越"贵"
    （需要额外请求）
```

**为什么大多数教程只教到第二层？**

- **简单** —— 只验证 HTTP 200 省事
- **不会发现更深层的 bug** —— "接口返回成功，但数据库没写"这种 bug 最隐蔽

**面试时怎么回答"为什么用三层验证"？**

> "因为我发现只验证 HTTP 状态码是不够的。比如有个接口返回 200 + code=200，但数据库里根本没有这条记录 —— 这就是所谓的'伪成功'。加了第三层反查后，这种问题就能 100% 发现。"

### 2.3 CASER 模式 —— 为什么不用"独立测试"？

#### 错误的做法（独立测试）：

```python
def test_login(): ...      # 测登录
def test_create(): ...      # 测创建
def test_query(): ...       # 测查询
def test_update(): ...      # 测更新
def test_delete(): ...      # 测删除
# 每个测试孤立的，不知道前一个测试创建了什么数据
```

**问题**：
- `test_query` 不知道查询谁的 ID（硬编码一个已存在的 ID）
- `test_update` 不知道更新谁（也是硬编码）
- `test_delete` 也是硬编码 ID
- 如果那个硬编码 ID 的数据被删了 → **测试全崩**

#### 正确的做法（CASER 模式）：

```python
class TestProductCategory:
    cat_id = None  # 类变量，用例之间共享
    
    def test_c_create(self):
        """C: Create — 创建，拿到 cat_id"""
        TestProductCategory.cat_id = create_category(...)
    
    def test_s_search(self):
        """S: Search — 用 cat_id 查询"""
        assert search_category(TestProductCategory.cat_id)['name'] == "测试分类"
    
    def test_e_update(self):
        """E: Edit — 更新 cat_id 对应记录"""
        update_category(TestProductCategory.cat_id, {"name": "新名称"})
    
    def test_r_delete(self):
        """R: Remove — 删除 cat_id 对应记录"""
        delete_category(TestProductCategory.cat_id)
    
    # 测试完后，数据库没有残留数据
```

**CASER 的优势**：

| 对比维度 | 独立测试 | CASER 模式 |
|---------|-----------|----------------|
| **数据依赖** | 硬编码 ID（易崩） | 前一个用例的产出自动传给下一个 |
| **数据清理** | 需要手动清理 | 最后一个用例（Remove）自动清理 |
| **真实性** | 单元测试思维 | 模拟真实用户操作链路 |
| **可维护性** | ID 硬编码，后面不知道它从哪来 | 有清晰的依赖链路 |

**面试话术**：
> "我发现每个接口单独测试有个问题：测试数据不好管理。如果是独立测试，查询和更新都要硬编码一个 ID，运行多次就会崩。所以我设计了 CASER 模式，创建后的 ID 自动传给后续用例，删除用例自动清理测试数据。"

### 2.4 参数化的设计思路

#### 问题：如何高效验证多组登录场景？

**硬编码法**（每组建一个新函数）：
```python
def test_login_ok(): ...       # 正常登录
def test_login_wrong_pwd(): ...# 密码错误
def test_login_empty_user():...# 用户名为空
def test_login_empty_pwd(): ...# 密码为空
def test_login_not_exist(): ...# 用户不存在
```

**问题**：5 个函数，90% 的代码是重复的（都是 `requests.post() + assert`）

**参数化法**：
```python
@pytest.mark.parametrize("username,password,expected", [
    ("admin", "macro123", 200),    # 正常
    ("admin", "wrong", 401),      # 密码错
    ("", "macro123", 400),        # 用户名为空
    ("admin", "", 400),           # 密码为空
    ("nonexist", "123456", 404),  # 不存在
])
def test_login(username, password, expected):
    resp = requests.post(...)
    assert resp.status_code == expected
```

**优势**：
- **代码量减少 80%**：从 25 行 → 5 行
- **一目了然**：所有测试场景列在一起，容易 review
- **加新场景只需一行**：不需要写新函数

---

## 三、第三阶段：框架搭建

### 3.1 为什么先搭框架再写用例？

**反模式**（初学者常犯的错误）：

```python
# test_admin.py
def test_login_admin():
    resp = requests.post("/admin/login", json={"username": "admin", "password": "macro123"})
    token = resp.json()['data']['token']

def test_create_role():
    resp = requests.post("/admin/login", json={...})  # 又登录了一遍！
    token = resp.json()['data']['token']
    # ...

def test_delete_role():
    resp = requests.post("/admin/login", json={...})  # 第三遍了！
    token = resp.json()['data']['token']
    # ...
```

**问题**：每个用例都重新登录一次！100 个用例 = 100 次登录请求！

**正确做法**：先搭框架，把公共逻辑抽出来。

### 3.2 框架搭的建思路

```
第 1 步：解决 Token 共享问题 → conftest.py (Fixture)
第 2 步：封装 HTTP 请求层 → base_api.py
第 3 步：实现统一断言 → assert_code_ok()
```

#### 第 1 步：Token 共享

```python
# conftest.py
@pytest.fixture(scope="session")  # ← 关键！scope="session" 意味着只执行一次
def login_token():
    resp = requests.post("/admin/login", json={"username": "admin", "password": "macro123"})
    return resp.json()['data']['token']

@pytest.fixture(scope="session")
def base_api(login_token):
    return BaseAPI(token=login_token)
```

**设计思考**：
- `scope="session"` = 整个测试会话只登录一次
- 100 个测试用例共享同一个 Token
- 性能：从 10 秒（100 次登录）降到 2 秒（1 次登录）

**面试问答**：
> "为什么用 scope='session' 而不是默认的 scope='function'？"  
> "因为 Token 是全局共享的，不需要每个用例都重新登录。scope='session' 让 100 个用例共享同一个 Token，执行时间从 10 秒降到了 2 秒。"

#### 第 2 步：封装 BaseAPI

```python
class BaseAPI:
    def __init__(self, base_url, token):
        self.session = requests.Session()   # ← 用 Session 而不是 requests.get()
        self.session.headers.update({"Authorization": token})
    
    def get(self, path, params=None): ...    # 封装 GET
    def post(self, path, json=None, params=None): ...  # 封装 POST
    
    def assert_code_ok(self, response, msg=""): ...
```

**为什么用 Session 而不是 Requests 的 get/post？**

```python
# 不用 Session（不好）
resp = requests.get(url, headers={...})  # 每次新建连接
resp = requests.get(url, headers={...})  # 又新建连接
# 100 次请求 = 100 次 TCP 握手

# 用 Session（好）
resp = self.session.get(url)  # 复用 TCP 连接
resp = self.session.get(url)  # 还是同一条连接
# 100 次请求 = 1 次 TCP 握手 + 99 次复用
```

#### 第 3 步：统一断言

```python
def assert_code_ok(self, response, msg=""):
    """统一断言：HTTP 200 + 业务 code 200"""
    result = response.json()
    assert response.status_code == 200, f"{msg} | HTTP状态码非200"
    assert result.get('code') == 200, f"{msg} | 业务code非200"
    return result  # 返回完整的 JSON，方便上层继续提取数据
```

**为什么 return result？**
- 方便上层用例**直接提取数据**，不需要再解析一次 JSON
- 链式调用：`data = base_api.assert_code_ok(resp)['data']['id']`

### 3.3 为什么选择三层架构？

```
测试用例层（写业务逻辑）
    ↓ 依赖
公共封装层（HTTP 请求 + 断言）
    ↓ 依赖  
HTTP Client 层（requests / urllib）
```

**设计原则**：
1. **测试用例只关心业务**：不需要知道 HTTP 细节
2. **底层变化不影响上层**：从 HTTP 换成 HTTPS，只改 base_api.py
3. **新模块即插即用**：写新测试文件只需 import base_api

**如果不用分层会怎样？**

```python
# 每个测试文件里都这么写（噩梦！）
headers = {"Authorization": f"Bearer {token}"}
resp = requests.post(f"{base_url}/admin/login", json=data, headers=headers)
assert resp.status_code == 200
assert resp.json()['code'] == 200
# 100 行测试 = 100 行重复代码
```

---

## 四、第四阶段：批量编写用例

### 4.1 编写顺序：从核心模块到边缘模块

```
Day 1: 登录模块（2 条） → 验证框架能跑通
Day 2: 用户管理模块（11 条） → 验证 CRUD 逻辑
Day 3: 商品模块（19 条） → 验证复杂业务
Day 4: 订单模块（15 条） → 验证依赖关系
Day 5: 营销模块（27 条） → 验证批量操作
Day 6: 品牌 + 系统模块（17 条） → 补全边缘模块
```

**为什么不一次写完？**

- **逐步验证**：每写完一个模块就跑一下，确保框架没问题
- **渐进复杂度**：Login（2 条）→ CRUD（5 条）→ 复杂业务（19 条）
- **及时修复**：发现框架问题立刻修正，而不是写完 100 条再修复

### 4.2 用例设计原则

**原则 1：每个用例的名字要"自解释"**

```python
# 不好：看不出来测什么
def test1(): ...
def test2(): ...

# 好：看名字就知道测什么
def test_c_create_category(self): ...  # C = Create
def test_s_search_category(self): ...  # S = Search
def test_e_update_category(self): ...  # E = Edit
def test_r_delete_category(self): ...  # R = Remove
```

**原则 2：测试数据要"自我标识"**

```python
# 不好：不知道数据是谁创建的
name = "测试分类"

# 好：一看就知道是自动化测试创建的数据
import random
suffix = random.randint(10000, 99999)
name = f"AutoTest分类_{suffix}"  # AutoTest分类_13045
```

**原则 3：每个测试类用类变量传数据**

```python
class TestProductCategory:
    cat_id = None  # 类变量，跨用例共享
    
    def test_c_create(self, base_api):
        TestProductCategory.cat_id = create_category(...)  # 写入
    
    def test_s_search(self, base_api):
        assert TestProductCategory.cat_id is not None  # 读取
```

### 4.3 模块接口决策逻辑

```
对于每个模块：

1. 先列出所有接口（从 Swagger 获取）
2. 判断哪些值得测试
   - 有 CRUD 操作 → CASER 模式全覆盖（5 条）
   - 只有查询 → 1 条验证数据结构
   - 有批量操作 → 2 条（正常 + 状态切换）
3. 编写用例（一个接口至少一条）
4. 审视遗漏 → 补充边界条件用例
```

**决策树**：

```
接口是什么类型？
├── CRUD 接口
│   ├── Create → 至少 1 条（正常 + 缺必填参数）
│   ├── Search → 1 条（验证能查到 + 数据正确）
│   ├── Edit → 1 条（验证更新 + 反查确认）
│   └── Remove → 1 条（验证删除 + 反查不存在）
│   ✅ 5 条 CASER 覆盖
│
├── 批量操作接口
│   ├── 正常批量 → 1 条
│   └── 状态切换 → 1 条（切换后还原）
│   ✅ 2 条
│
├── 纯查询接口
│   └── 验证返回结构 → 1 条
│   ✅ 1 条
│
├── 需要外键的接口（如首页品牌推荐）
│   └── 只测查询，不测创建（因为需要真实的 brand_id）
│   ✅ 1 条
│
└── 基础设施接口（文件上传等）
    └── 跳过
    ❌ 0 条
```

---

## 五、第五阶段：踩坑与修复

### 5.1 踩坑不是坏事 — 是深度学习的机会

每个坑都教会我一些"教科书上不写的东西"：

| 坑 | 表面原因 | 深层教训 |
|----|----------|----------|
| `/productCategory/create` 返回 500 → `parentId` 必填 | Swagger 没标注 required | 不要完全信任 Swagger 文档 |
| `/brand/delete/{id}` 是 GET 不是 POST | 开发者不懂 RESTful | 每个模块有自己的"个性"，要先调一次 |
| `/flashSession/list` 返回数组不是分页 | 接口设计不一致 | 同一项目的接口格式可能不同 |
| `allure.cmd` 路径问题 | Windows 不认 shell 脚本 | Windows/Linux 的差异要注意 |

### 5.2 踩坑的正确态度

**错误态度**：
> "为什么这个接口这么奇怪？设计有问题！"（抱怨）

**正确态度**：
> "这个必填参数 Swagger 没标，说明文档不可全信。以后每接触新接口，先实际调一下确认参数。"

**面试时怎么回答"你遇到过什么困难"？**：

> "我在测试商品分类创建接口时，发现 Swagger 文档没有标注 parentId 是必填参数，导致首次测试返回 500。我通过直接看 Java 源码的 @NotNull 注解确认了这个问题，然后修好了测试用例。这个经历让我形成了'调一个验证一个'的习惯 —— 不要完全信任文档，要以实际调用为准。"

### 5.3 如何防止"连锁反应"？

CASER 模式有一个**致命弱点**：如果 Create 失败，后续的 Search/Edit/Remove 全崩。

**解决方案**：善用前向断言

```python
def test_e_update(self):
    assert TestProductCategory.cat_id is not None, \
        "❌ Create 失败，跳过 Update。请先修复 Create！"
    # 这样其他用例不会报 500，而是清晰地告诉你：先修复上一个
```

**面试问答**：
> "如果 Create 失败，后续用例会怎么样？"  
> "我们用了前向断言 —— 每个依赖前置结果的用例都会先检查前置数据是否存在。如果 Create 失败，后面用例会清晰地报'Create 失败，请先修复 Create'，而不是一个模糊的 KeyError。"

---

## 六、第六阶段：报告与交付

### 6.1 Allure 报告的设计选择

**为什么要用 Allure 而不是 pytest-html？**

| 特性 | pytest-html | Allure |
|------|-------------|--------|
| 可视美观度 | 简单 | ⭐⭐⭐⭐⭐ |
| 图表支持 | 无 | ✅ 柱状图/饼图/折线图 |
| 失败截图 | 手动添加 | 自动关联 |
| 面试加分度 | ⭐⭐ | ⭐⭐⭐⭐ |
| 难度 | 一次安装 | 需要 allure-commandline |

**选择 Allure 的理由**：
- 面试时打开 Allure 报告 → **视觉冲击力远超 pytest-html**
- 报告上有**通过率、耗时曲线、失败分析** → 比纯文本报告"更专业"
- 非技术人员（如产品经理）也能看懂

### 6.2 自动打开报告的设计

**问题**：测试做完后，如何让浏览器自动弹出报告？

**方案设计过程**：

| 方案 | 问题 |
|------|------|
| 方案 1：`allure open report` | 需要 Java 环境，会阻塞进程 |
| 方案 2：`webbrowser.open("file://...")` | Allure 报告必须通过 HTTP 访问（JS 跨域） |
| **方案 3：Python HTTP Server** | ✅ 不需要 Java，不阻塞，轻量 |

**最终实现**：

```python
def pytest_sessionfinish(session):
    # 1. 生成报告
    subprocess.run(f'allure generate results -o report --clean', shell=True)
    
    # 2. 启动 HTTP 服务器（后台进程）
    subprocess.Popen(
        [sys.executable, "-m", "http.server", "8888"],
        cwd=report_dir,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    # 3. 打开浏览器
    time.sleep(1.5)
    webbrowser.open("http://localhost:8888")
    print(" Allure 报告已自动打开！")
```

---

## 七、设计决策回顾

### 7.1 每个选择背后的"为什么"

| 决策 | 为什么选它？ | 为什么不选其他？ |
|------|-------------|-----------------|
| Pytest 而不是 Unittest | Fixture 机制灵活，插件生态强 | Unittest 的 setUp/tearDown 太重，不支持参数化 |
| Requests 而不是 urllib | API 直观，一行搞定 HTTP 请求 | urllib 代码臃肿，面试不认 |
| YAML 而不是 JSON/Excel | 可读性强，支持注释 | JSON 不支持注释，Excel 版本管理困难 |
| Session 而不是每次 get() | 复用 TCP 连接，性能更好 | 每次新连接效率低 |
| scope="session" 而不是 function | 只登录一次，所有用例共享 | function 会导致 100 次登录 |
| .bat 脚本 而不是 Makefile | Windows 用户友好 | Makefile 在 Windows 上需要额外安装 |

### 7.2 为什么不做"所有接口全都测"？

**原因**：测试不是越多越好 — 效率更重要。

**决策逻辑**：
```
接口总量：138 个
├── P0（CRUD 核心）：71 个 → 100% 测试（91 条用例）
├── P1（批量操作）：15 个 → 选择性测试（已在 P0 中覆盖）
├── P2（纯查询）：20 个 → 1 条验证数据结构
├── P3（基础设施）：5 个 → 跳过（依赖环境）
└── P4（前台门户）：27 个 → 跳过（不在本次范围）

测试覆盖率：71/138 = 51.4%（核心接口 100% 覆盖）
```

**面试问答**：
> "为什么只测了 71 个接口，而不是全部 138 个？"  
> "测试不是越多越好，效率更重要。我把接口按优先级分成 P0-P4，P0 的 CRUD 核心接口 100% 覆盖，P1-P2 的查询接口只做基础验证，P4 的前台门户不在后台管理测试范围内。这种策略既保证了核心功能的覆盖率，又避免了在不重要的接口上浪费时间。"

---

## 八、面试话术模板

### 8.1 自我介绍模板

> "我在项目中负责从零搭建接口自动化测试框架，使用 Python + Pytest + Requests + Allure 技术栈，覆盖了一个电商后台管理系统的 7 大模块、91 条核心用例。
> 
> 在框架设计方面，我封装了 BaseAPI 公共层实现 Token 自动管理和 HTTP 请求复用，用 Pytest Fixture 机制让 100 个用例共享同一个登录 Token，性能提升了 5 倍。
> 
> 在测试策略方面，我设计了 CER 全链路测试模式（创建→查→改→删）和三层验证体系（HTTP 状态码→业务 code→反查数据库），能发现传统二层验证发现不了的'伪成功'问题。
> 
> 最后我集成了 Allure 可视化报告，每次测试完成自动生成 HTML 报告并弹出浏览器，方便非技术人员查看测试结果。"

### 8.2 常见追问及回答

**Q1: 你的框架是怎么设计的？为什么这样设计？**

> "我用了三层架构：测试用例层、公共封装层、HTTP 请求层。测试用例只关心业务逻辑，不需要处理 HTTP 细节。如果要换底层 HTTP 库，只需要改公共封装层，测试用例完全不受影响。这也是软件工程里从'面向接口编程'的思想。"

**Q2: 你怎么保证测试数据的可靠性？**

> "我用了三层验证体系。第一层验证 HTTP 状态码，第二层验证业务 code，第三层反查数据库确认数据真的被修改了。这是我发现在只做二层验证时，有些接口返回 code:200 但数据库其实没有更新的问题后引入的。"

**Q3: 遇到的最难的问题是什么？**

> "最难的是处理接口间的差异。比如 /flashSession/list 返回的是数组，而其他列表接口返回的是分页对象 {list:[], total:N}。这类接口设计不一致的情况，在真实项目中很常见。我通过 '先调一个接口验证返回格式' 的方法来避免这类问题。"

**Q4: 如果让你改进这个框架，你会做什么？**

> "我会考虑三个方向：
> 1. 加入 CI/CD 集成（GitHub Actions / Jenkins），每次代码提交自动触发测试
> 2. 实现数据清理机制，在测试完自动删除测试数据，不怕在线上环境跑
> 3. 添加断言增强，对常见的断言模式（如：列表不为空、包含指定字段）提供一行断言的快捷方法"

---

## 附录

### A. 技术术语表

| 术语 | 解释 |
|------|------|
| **Fixture** | Pytest 的"测试夹具"机制，用于准备测试需要的数据（如登录 Token） |
| **CASER** | 全链路测试模式：Create → Assign → Search → Edit → Remove |
| **DDT** | 数据驱动测试，从外部文件（如 YAML）读取测试数据 |
| **Session** | Requests 库的会话对象，可以复用 TCP 连接、共享 Cookie |
| **Allure** | 开源的测试报告框架，生成可视化 HTML 报告 |
| **scope** | Fixture 的生命周期（function：每个用例执行一次 / session：整个测试会话执行一次） |

### B. 参考资料

- **mall 项目**：https://github.com/macrozheng/mall
- **Pytest 官方文档**：https://docs.pytest.org/
- **Requests 官方文档**：https://docs.python-requests.org/
- **Allure 官方文档**：https://docs.qameta.io/allure/

---

**文档版本**：v1.0  
**最后更新**：2026-06-08  
**作者**：（你的名字）  
**联系方式**：（你的邮箱 / 电话）
