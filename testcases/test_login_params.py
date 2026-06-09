import requests
import pytest


class TestLoginParams:
    """登录接口参数化测试"""

    @pytest.mark.parametrize("username,password,expected_code,expect_success", [
        # 格式: (用户名, 密码, 期望HTTP状态码, 是否期望登录成功)
        ("admin",       "macro123",     200, True),   # 场景1: 正确登录
        ("admin",       "wrong_pwd",    200, False),  # 场景2: 密码错误
        ("",            "macro123",     200, False),  # 场景3: 用户名为空
        ("admin",       "",             200, False),  # 场景4: 密码为空
        ("no_such_user","123456",       200, False),  # 场景5: 用户不存在
    ])
    def test_login_multi_scenario(
        self, username, password, expected_code, expect_success
    ):
        """
        一个方法测 5 种登录场景
        parametrize 会自动把每组数据注入进来，执行 5 次
        """
        url = "http://localhost:8080/admin/login"
        data = {"username": username, "password": password}

        response = requests.post(url=url, json=data)
        result = response.json()

        # 断言 HTTP 状态码
        assert response.status_code == expected_code, \
            f"期望状态码 {expected_code}，实际 {response.status_code}"

        if expect_success:
            # 期望登录成功
            assert result["code"] == 200, f"期望成功，实际 code={result['code']}"
            assert "token" in result["data"]
            print(f"✅ 登录成功: {username} → token获取正常")
        else:
            # 期望登录失败
            assert result["code"] != 200, \
                f"期望登录失败，实际 code={result['code']}"
            print(f"❌ 登录失败(符合预期): {username} → {result['message']}")
