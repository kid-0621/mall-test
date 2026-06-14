"""
mall 商城 — Locust Hello World

目标：用最简单的代码验证 Locust 能正常工作
"""

from locust import HttpUser, task, between


class HelloWorldUser(HttpUser):
    """
    最简单的 Locust 用户类
    只做一件事：请求首页（会返回 401，但没关系）
    """
    # 每次请求之间等 1~2 秒（模拟人类操作间隔）
    wait_time = between(1, 2)

    @task
    def visit_homepage(self):
        """访问后台首页"""
        self.client.get("/", name="GET / (首页)")
