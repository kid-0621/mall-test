"""
登录接口测试用例
"""

import requests
import pytest


class TestLogin:
    """测试登录接口"""

    def test_login_success(self):
        """
        测试场景：正常登录
        """
        # 1. 准备数据
        url = "http://localhost:8080/admin/login"
        data = {
            "username": "admin",
            "password": "macro123"
        }

        # 2. 发送请求
        response = requests.post(url=url, json=data)

        # 3. 断言验证
        # 3.1 验证 HTTP 状态码是否为 200
        assert response.status_code == 200
        print(f"状态码: {response.status_code}")

        # 3.2 解析 JSON 响应
        result = response.json()
        print(f"响应体: {result}")

        # 3.3 验证业务状态码是否为 200
        assert result["code"] == 200

        # 3.4 验证返回了 token
        assert "token" in result["data"]
        print(f"获取到 token: {result['data']['token'][:20]}...")

    def test_login_wrong_password(self):
        """
        测试场景：密码错误
        """
        url = "http://localhost:8080/admin/login"
        data = {
            "username": "admin",
            "password": "wrong_password"
        }

        response = requests.post(url=url, json=data)
        result = response.json()

        # 密码错误时业务码应该不是 200
        assert result["code"] != 200
        print(f"密码错误响应: {result['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
