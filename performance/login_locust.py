"""
mall 商城 — Locust 登录脚本（教学用）

目标：学会用 Locust 模拟"登录后操作"
"""

from locust import HttpUser, task, between
import json


# ===========================================
# 第一部分：理解 on_start（用户启动时执行）
# ===========================================

class MallLoginUser(HttpUser):
    """
    模拟一个"已登录的管理员"

    关键点：
    1. wait_time = between(1, 2)  → 每次请求之间等 1~2 秒
    2. on_start()                   → 用户启动时自动调用（只执行 1 次）
    """

    wait_time = between(1, 2)

    def on_start(self):
        """
        登录逻辑：用 admin/macro123 登录，拿到 Token

        类比：你打开浏览器 → 输入账号密码 → 点击登录 → 拿到 Token
        """
        # 1. 准备登录数据
        login_data = {
            "username": "admin",
            "password": "macro123"
        }

        # 2. 发送 POST 请求（注意：用 self.client，不是 self.client.get）
        response = self.client.post(
            "/admin/login",
            json=login_data,  # 自动转成 JSON，自动加 Content-Type: application/json
            name="POST /admin/login"  # 给这个请求起个名字（报告里显示）
        )

        # 3. 检查登录是否成功
        if response.status_code != 200:
            print(f"❌ 登录失败！状态码：{response.status_code}")
            return

        # 4. 解析 JSON，拿到 Token
        result = response.json()
        if result.get("code") != 200:
            print(f"❌ 登录失败！code={result.get('code')}")
            return

        # 5. 提取 Token（注意 mall 的返回格式）
        #    返回格式：{"code":200,"data":{"token":"xxx","tokenHead":"Bearer "},"message":"操作成功"}
        token_data = result.get("data", {})
        token = token_data.get("token", "")
        token_head = token_data.get("tokenHead", "")

        # 6. 把 Token 加到所有后续请求的 Header 里
        #    self.client 是 locust 的 HTTP 客户端（类似 requests.Session）
        auth_value = f"{token_head}{token}" if token_head else token
        self.client.headers.update({
            "Authorization": auth_value
        })

        print(f"✅ 登录成功！Token 前 20 字符：{token[:20]}...")


    # ===========================================
    # 第二部分：定义"任务"（用户会做什么）
    # ===========================================

    @task(1)  # 数字 1 = 权重（后面会教权重）
    def visit_product_list(self):
        """
        访问商品列表（登录后才能访问）

        类比：登录后 → 点击"商品管理" → 看到商品列表
        """
        # 现在 self.client 会自动带上 Authorization header
        response = self.client.get(
            "/product/list",
            params={"pageNum": 1, "pageSize": 10},  # URL 参数：?pageNum=1&pageSize=10
            name="GET /product/list"
        )

        # 可选：打印响应（调试用）
        if response.status_code == 200:
            print(f"✅ 商品列表获取成功！状态码：{response.status_code}")
        else:
            print(f"❌ 商品列表获取失败！状态码：{response.status_code}")


# ===========================================
# 第三部分：本地测试（不用 Locust Web UI）
# ===========================================

if __name__ == "__main__":
    """
    这部分代码只在"直接运行 python login_locust.py"时执行
    用 Locust Web UI 时不执行（所以暂时不用管）
    """
    print("请用 Locust 运行：locust -f performance/login_locust.py --host=http://localhost:8080")
