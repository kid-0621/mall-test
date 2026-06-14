"""
调试用：只运行 MallAdminUser 一个类，验证 Token 流程是否正常
"""
import os
import random
import time
from locust import HttpUser, task, between, events

ADMIN_USERNAME = os.getenv("MALL_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("MALL_ADMIN_PASS", "macro123")
SEARCH_KEYWORDS = ["小米", "华为", "苹果", "手机"]


class MallAdminUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        print(f"\n[DEBUG] {self.__class__.__name__} 正在登录...")
        resp = self.client.post("/admin/login", json={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, name="POST /admin/login")

        print(f"[DEBUG] 登录响应 status={resp.status_code}, body={resp.text[:200]}")

        data = resp.json()
        token_data = data.get("data", {})
        self.token = token_data.get("token", "")
        token_head = token_data.get("tokenHead", "")

        print(f"[DEBUG] token长度={len(self.token)}, tokenHead='{token_head}'")

        auth_value = self.token if not token_head else f"{token_head}{self.token}"
        print(f"[DEBUG] 设置 Authorization: {auth_value[:30]}...")

        self.client.headers.update({"Authorization": auth_value})

        # 验证：立即发一个带 token 的请求测试
        test_resp = self.client.get("/brand/list",
                                    params={"pageNum": 1, "pageSize": 5},
                                    name="[验证] GET /brand/list (带Token)")
        print(f"[DEBUG] 验证请求 status={test_resp.status_code}, body={test_resp.text[:150]}")

    @task(20)
    def browse_products(self):
        self.client.get(
            "/product/list",
            params={"pageNum": random.randint(1, 10), "pageSize": 10},
            name="GET /product/list"
        )

    @task(15)
    def browse_orders(self):
        self.client.get(
            "/order/list",
            params={"pageNum": 1, "pageSize": 10},
            name="GET /order/list"
        )

    @task(15)
    def search_products(self):
        keyword = random.choice(SEARCH_KEYWORDS)
        self.client.get(
            "/product/simpleList",
            params={"keyword": keyword},
            name="GET /product/simpleList"
        )

    @task(10)
    def browse_brands(self):
        self.client.get(
            "/brand/list",
            params={"pageNum": 1, "pageSize": 10},
            name="GET /brand/list"
        )

    @task(10)
    def browse_categories(self):
        self.client.get(
            "/productCategory/list/withChildren",
            name="GET /productCategory/list/withChildren"
        )

    @task(5)
    def browse_coupons(self):
        self.client.get(
            "/coupon/list",
            params={"pageNum": 1, "pageSize": 10},
            name="GET /coupon/list"
        )

    @task(5)
    def read_admin_info(self):
        self.client.get(
            "/admin/info",
            name="GET /admin/info"
        )
