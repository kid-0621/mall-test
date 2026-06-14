"""
mall 商城后台管理系统 — Locust 性能测试脚本

架构说明：
  - Locust 基于 gevent 协程实现并发（非操作系统线程），
    单进程可支撑数千并发用户，资源消耗远低于 JMeter 线程模型。
  - 本脚本同时支持两种用户行为模型：
    1. MallAdminUser   — 按权重随机执行接口（模拟真实后台运营）
    2. BusinessChainUser — 按固定顺序执行核心业务链路（登录→搜索→浏览→查看→监控）

运行方式：
  # Web UI 模式（调试）
  locust -f locustfile.py --host=http://localhost:8080

  # Headless 模式（正式压测）
  locust -f locustfile.py --host=http://localhost:8080 \
      --headless --users 100 --spawn-rate 10 --run-time 5m \
      --html=report/report.html --csv=report/result

  # 指定用户类（业务链路场景）
  locust -f locustfile.py --host=http://localhost:8080 \
      --headless --users 50 --spawn-rate 10 --run-time 5m \
      -u BusinessChainUser \
      --html=report/chain_report.html

  # 环境变量切换场景
  SCENARIO=stress locust -f locustfile.py --host=http://localhost:8080 --headless \
      --users 500 --spawn-rate 50 --run-time 10m --html=report/stress_report.html
"""

import os
import random
import time
from locust import HttpUser, task, between, events, TaskSet
from locust.exception import StopUser


# ============================================
# 全局配置
# ============================================

ADMIN_USERNAME = os.getenv("MALL_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("MALL_ADMIN_PASS", "macro123")
SCENARIO = os.getenv("SCENARIO", "mixed")  # mixed | read-only | spike | chain

# 常用商品关键词（用于搜索）
SEARCH_KEYWORDS = ["小米", "华为", "苹果", "手机", "笔记本电脑", "耳机", "衣服", "食品", "电器"]

# 默认分页大小
PAGE_SIZES = [5, 10, 20, 50]


# ============================================
# 自定义事件：收集请求失败数和慢请求
# ============================================

FAIL_COUNT = 0
SLOW_COUNT = 0
SLOW_THRESHOLD_MS = 3000  # RT > 3s 视为慢请求


@events.request.add_listener
def on_request(request_type, name, response_time, response_length,
               exception, context, **kwargs):
    """每个请求完成后回调"""
    global FAIL_COUNT, SLOW_COUNT
    if exception:
        FAIL_COUNT += 1
    if response_time > SLOW_THRESHOLD_MS:
        SLOW_COUNT += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时输出汇总"""
    global FAIL_COUNT, SLOW_COUNT
    stats = environment.stats
    print("\n" + "=" * 60)
    print("  mall 商城性能测试 — 测试结束汇总")
    print("=" * 60)
    print(f"  总请求数:     {stats.total.num_requests}")
    print(f"  失败请求数:   {stats.total.num_failures}")
    print(f"  失败率:       {stats.total.fail_ratio * 100:.2f}%")
    print(f"  平均 RT:      {stats.total.avg_response_time:.0f} ms")
    print(f"  P50 RT:       {stats.total.get_response_time_percentile(0.5):.0f} ms")
    print(f"  P95 RT:       {stats.total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  P99 RT:       {stats.total.get_response_time_percentile(0.99):.0f} ms")
    print(f"  最大 RT:      {stats.total.max_response_time:.0f} ms")
    print(f"  当前 RPS:     {stats.total.current_rps:.1f}")
    print(f"  慢请求(>3s):  {SLOW_COUNT}")
    print("=" * 60)


# ============================================
# 用户行为定义
# ============================================

class MallAdminUser(HttpUser):
    """
    模拟 mall 后台管理员用户

    行为权重设计（参考电商后台操作频率）：
    - 商品浏览/搜索  ~45%  （最高频）
    - 订单查看        ~25%
    - 分类/品牌浏览   ~15%
    - 营销数据查看    ~10%
    - 用户信息        ~5%
    """

    # 每个用户请求间隔（模拟真人操作间隔）
    wait_time = between(1, 3)

    # 登录态
    token = None
    admin_id = None

    def on_start(self):
        """每个虚拟用户启动时：登录获取 token"""
        resp = self.client.post("/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, name="POST /admin/login")

        if resp.status_code != 200:
            print(f"[ERROR] 登录失败: HTTP {resp.status_code}, body={resp.text[:200]}")
            raise StopUser()

        data = resp.json()
        if data.get("code") != 200:
            print(f"[ERROR] 登录失败: code={data.get('code')}, msg={data.get('message')}")
            raise StopUser()

        token_data = data.get("data", {})
        self.token = token_data.get("token", "")
        self.token_head = token_data.get("tokenHead", "")

        if not self.token:
            raise StopUser()

        # 设置全局认证头
        auth_value = self.token if not self.token_head else f"{self.token_head}{self.token}"
        self.client.headers.update({"Authorization": auth_value})

    # ──────── 商品相关 (权重 ~45%) ────────

    @task(25)
    def browse_products(self):
        """浏览商品列表 — 最高频操作"""
        page = random.randint(1, 10)
        page_size = random.choice(PAGE_SIZES)

        with self.client.get(
            "/product/list",
            params={"pageNum": page, "pageSize": page_size},
            name="GET /product/list",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(10)
    def search_products(self):
        """搜索商品"""
        keyword = random.choice(SEARCH_KEYWORDS)

        with self.client.get(
            "/product/simpleList",
            params={"keyword": keyword},
            name="GET /product/simpleList",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(5)
    def view_product_detail(self):
        """查看商品详情（使用随机 ID）"""
        product_id = random.randint(1, 100)

        with self.client.get(
            f"/product/updateInfo/{product_id}",
            name="GET /product/updateInfo/{id}",
            catch_response=True
        ) as resp:
            # 商品可能不存在（404），这在压测中是正常场景
            if resp.status_code in [200, 404, 400]:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(5)
    def browse_brands(self):
        """浏览品牌列表"""
        page_size = random.choice(PAGE_SIZES)

        with self.client.get(
            "/brand/list",
            params={"pageNum": 1, "pageSize": page_size},
            name="GET /brand/list",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ──────── 分类相关 (权重 ~12%) ────────

    @task(7)
    def browse_categories(self):
        """浏览商品分类树"""
        with self.client.get(
            "/productCategory/list/withChildren",
            name="GET /productCategory/list/withChildren",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(5)
    def browse_category_list(self):
        """浏览一级分类列表"""
        parent_id = random.choice([0, 1, 2, 3])
        page_size = random.choice(PAGE_SIZES)

        with self.client.get(
            f"/productCategory/list/{parent_id}",
            params={"pageSize": page_size, "pageNum": 1},
            name="GET /productCategory/list/{parentId}",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ──────── 订单相关 (权重 ~25%) ────────

    @task(15)
    def browse_orders(self):
        """浏览订单列表"""
        page = random.randint(1, 5)
        page_size = random.choice(PAGE_SIZES)

        with self.client.get(
            "/order/list",
            params={"pageNum": page, "pageSize": page_size},
            name="GET /order/list",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(10)
    def view_order_detail(self):
        """查看订单详情"""
        order_id = random.randint(1, 500)

        with self.client.get(
            f"/order/{order_id}",
            name="GET /order/{id}",
            catch_response=True
        ) as resp:
            if resp.status_code in [200, 404, 400]:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ──────── 营销相关 (权重 ~13%) ────────

    @task(8)
    def browse_coupons(self):
        """浏览优惠券列表"""
        page_size = random.choice(PAGE_SIZES)

        with self.client.get(
            "/coupon/list",
            params={"pageNum": 1, "pageSize": page_size},
            name="GET /coupon/list",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(5)
    def browse_flash_promotions(self):
        """浏览秒杀活动"""
        with self.client.get(
            "/flash/list",
            params={"pageNum": 1, "pageSize": 10},
            name="GET /flash/list",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ──────── 系统/用户 (权重 ~5%) ────────

    @task(3)
    def view_admin_info(self):
        """查看当前管理员信息"""
        with self.client.get(
            "/admin/info",
            name="GET /admin/info",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    resp.success()
                else:
                    resp.failure(f"业务错误: {data.get('message')}")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    @task(2)
    def browse_menus(self):
        """获取菜单树"""
        with self.client.get(
            "/menu/treeList",
            name="GET /menu/treeList",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")


# ============================================
# 按场景提供不同用户类（可选切换）
# ============================================

class MallReadOnlyUser(HttpUser):
    """
    纯读场景 — 只做查询操作，不写数据
    用于测试数据库读承载能力
    """
    wait_time = between(0.5, 1.5)
    token = None

    def on_start(self):
        resp = self.client.post("/admin/login", json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD
        }, name="POST /admin/login")
        data = resp.json() if resp.status_code == 200 else {}
        token_data = data.get("data", {})
        self.token = token_data.get("token", "")
        token_head = token_data.get("tokenHead", "")
        auth = self.token if not token_head else f"{token_head}{self.token}"
        self.client.headers.update({"Authorization": auth})

    @task(30)
    def read_products(self):
        self.client.get("/product/list",
                        params={"pageNum": random.randint(1, 5), "pageSize": 10},
                        name="GET /product/list")

    @task(20)
    def read_orders(self):
        self.client.get("/order/list",
                        params={"pageNum": 1, "pageSize": 10},
                        name="GET /order/list")

    @task(15)
    def read_brands(self):
        self.client.get("/brand/list",
                        params={"pageNum": 1, "pageSize": 10},
                        name="GET /brand/list")

    @task(15)
    def read_categories(self):
        self.client.get("/productCategory/list/withChildren",
                        name="GET /productCategory/list/withChildren")

    @task(10)
    def read_coupons(self):
        self.client.get("/coupon/list",
                        params={"pageNum": 1, "pageSize": 10},
                        name="GET /coupon/list")

    @task(10)
    def read_admin_info(self):
        self.client.get("/admin/info", name="GET /admin/info")


# ============================================
# 核心业务链路用户 — 按简历描述"核心业务链路实施压测"
# 模拟管理员完整的日常操作流程（串行执行，非随机权重）
# ============================================

class BusinessChainUser(HttpUser):
    """
    核心业务链路场景（Core Business Chain）

    行为序列（每个虚拟用户按顺序执行）：
      1. 登录（on_start）
      2. 浏览商品列表
      3. 搜索商品
      4. 查看商品详情
      5. 浏览订单列表
      6. 查看订单详情
      7. 浏览优惠券列表
      8. 查看分类树
      9. 查看管理员信息
      → 循环回到第 2 步

    与 MallAdminUser（随机权重）的区别：
      - MallAdminUser：模拟多用户并发时的随机访问模式
      - BusinessChainUser：模拟单个用户的完整操作流程（链路追踪）
    """
    wait_time = between(1, 2)  # 每步之间思考 1~2 秒
    token = None
    _chain_step = 0  # 链路步骤计数器（用于串行执行）

    def on_start(self):
        """登录获取 token（链路起点）"""
        resp = self.client.post("/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, name="POST /admin/login (chain)")

        if resp.status_code != 200:
            raise StopUser()

        data = resp.json()
        if data.get("code") != 200:
            raise StopUser()

        token_data = data.get("data", {})
        self.token = token_data.get("token", "")
        token_head = token_data.get("tokenHead", "")
        auth = self.token if not token_head else f"{token_head}{self.token}"
        self.client.headers.update({"Authorization": auth})

    @task
    def run_chain(self):
        """
        按顺序执行核心业务链路中的每一步。
        每次被调度时执行一步，轮询所有步骤。
        """
        self._chain_step = (self._chain_step + 1) % 8

        if self._chain_step == 1:
            # 步骤 2：浏览商品列表
            self.client.get(
                "/product/list",
                params={"pageNum": random.randint(1, 5), "pageSize": 10},
                name="CHAIN: GET /product/list"
            )

        elif self._chain_step == 2:
            # 步骤 3：搜索商品
            keyword = random.choice(SEARCH_KEYWORDS)
            self.client.get(
                "/product/simpleList",
                params={"keyword": keyword},
                name="CHAIN: GET /product/simpleList"
            )

        elif self._chain_step == 3:
            # 步骤 4：查看商品详情
            product_id = random.randint(1, 100)
            self.client.get(
                f"/product/updateInfo/{product_id}",
                name="CHAIN: GET /product/updateInfo/{id}"
            )

        elif self._chain_step == 4:
            # 步骤 5：浏览订单列表
            self.client.get(
                "/order/list",
                params={"pageNum": 1, "pageSize": 10},
                name="CHAIN: GET /order/list"
            )

        elif self._chain_step == 5:
            # 步骤 6：查看订单详情
            order_id = random.randint(1, 500)
            self.client.get(
                f"/order/{order_id}",
                name="CHAIN: GET /order/{id}"
            )

        elif self._chain_step == 6:
            # 步骤 7：浏览优惠券列表
            self.client.get(
                "/coupon/list",
                params={"pageNum": 1, "pageSize": 10},
                name="CHAIN: GET /coupon/list"
            )

        elif self._chain_step == 7:
            # 步骤 8：查看分类树
            self.client.get(
                "/productCategory/list/withChildren",
                name="CHAIN: GET /productCategory/list/withChildren"
            )

        else:
            # 步骤 9：查看管理员信息（每轮结束）
            self.client.get(
                "/admin/info",
                name="CHAIN: GET /admin/info"
            )


# ============================================
# 峰值场景用户 — Spike Test（简历中"峰值"阶段）
# 模拟瞬时高并发脉冲（用户数短时间内暴增）
# ============================================

class SpikeUser(HttpUser):
    """
    峰值场景（Spike Test）—— 模拟流量突增

    使用方式（在 locustfile.py 同级目录执行）：
      # 方式 1：在 Web UI 中选择 SpikeUser 类
      locust -f locustfile.py --host=http://localhost:8080

      # 方式 2：命令行指定用户类
      locust -f locustfile.py -u SpikeUser --host=http://localhost:8080 \
          --headless --users 1000 --spawn-rate 500 --run-time 2m \
          --html=report/spike_report.html

    场景设计：
      - spawn-rate 设置很高（500/sec），模拟瞬时流量脉冲
      - 只执行轻量级读操作（商品列表 + 订单列表）
      - 观察系统是否能优雅降级（返回 429/503）而非崩溃
    """
    wait_time = between(0, 0.5)  # 几乎无思考时间，制造最大压力
    token = None

    def on_start(self):
        resp = self.client.post("/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, name="POST /admin/login (spike)")
        data = resp.json() if resp.status_code == 200 else {}
        token_data = data.get("data", {})
        self.token = token_data.get("token", "")
        token_head = token_data.get("tokenHead", "")
        auth = self.token if not token_head else f"{token_head}{self.token}"
        self.client.headers.update({"Authorization": auth})

    @task(70)
    def spike_product_list(self):
        """峰值主力请求：商品列表（读操作最频繁）"""
        self.client.get(
            "/product/list",
            params={"pageNum": random.randint(1, 10), "pageSize": 10},
            name="SPIKE: GET /product/list"
        )

    @task(30)
    def spike_order_list(self):
        """峰值辅助请求：订单列表"""
        self.client.get(
            "/order/list",
            params={"pageNum": 1, "pageSize": 10},
            name="SPIKE: GET /order/list"
        )

    @task(10)
    def spike_admin_info(self):
        """峰值保底请求：管理员信息（轻量接口）"""
        self.client.get(
            "/admin/info",
            name="SPIKE: GET /admin/info"
        )

    @task(5)
    def spike_category_tree(self):
        """峰值辅助请求：分类树（只读，无参数）"""
        self.client.get(
            "/productCategory/list/withChildren",
            name="SPIKE: GET /productCategory/list/withChildren"
        )

    @task(5)
    def spike_coupon_list(self):
        """峰值辅助请求：优惠券列表"""
        self.client.get(
            "/coupon/list",
            params={"pageNum": 1, "pageSize": 10},
            name="SPIKE: GET /coupon/list"
        )

    @task(3)
    def spike_flash_list(self):
        """峰值辅助请求：秒杀活动列表"""
        self.client.get(
            "/flash/list",
            params={"pageNum": 1, "pageSize": 10},
            name="SPIKE: GET /flash/list"
        )

    @task(2)
    def spike_brand_list(self):
        """峰值辅助请求：品牌列表"""
        self.client.get(
            "/brand/list",
            params={"pageNum": 1, "pageSize": 10},
            name="SPIKE: GET /brand/list"
        )

    @task(1)
    def spike_menu_tree(self):
        """峰值最低频：菜单树"""
        self.client.get(
            "/menu/treeList",
            name="SPIKE: GET /menu/treeList"
        )

    @task(1)
    def spike_product_detail(self):
        """峰值最低频：商品详情（有可能 404，正常）"""
        product_id = random.randint(1, 100)
        self.client.get(
            f"/product/updateInfo/{product_id}",
            name="SPIKE: GET /product/updateInfo/{{id}}"
        )

    @task(1)
    def spike_order_detail(self):
        """峰值最低频：订单详情（有可能 404，正常）"""
        order_id = random.randint(1, 500)
        self.client.get(
            f"/order/{order_id}",
            name="SPIKE: GET /order/{{id}}"
        )
