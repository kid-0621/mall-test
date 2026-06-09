import requests
import pytest


class TestAdminInfo:

    def test_get_admin_info_with_token(self, login_token):
        """
        用例1：带 token 访问，应该成功获取用户信息
        login_token 是从 conftest.py 的 fixture 自动传入的
        """
        url = "http://localhost:8080/admin/info"
        headers = {"Authorization": login_token}

        response = requests.get(url=url, headers=headers)
        result = response.json()

        # 断言
        assert response.status_code == 200
        assert result["code"] == 200
        assert result["message"] == "操作成功"

        data = result["data"]
        assert data["username"] == "admin"
        assert "icon" in data
        assert "menus" in data
        assert "roles" in data

        print(f"用户名: {data['username']}")
        print(f"角色: {data['roles']}")
        print(f"菜单数量: {len(data['menus'])}")

    def test_get_admin_info_no_token(self):
        """
        用例2：不带 token 访问，应该返回 401
        """
        url = "http://localhost:8080/admin/info"

        response = requests.get(url=url)
        result = response.json()

        # 断言：不带 token → 应该被拦截
        assert result["code"] == 401
        assert "token" in result["message"].lower() or "登录" in result["message"]

        print(f"未登录响应: {result['message']}")
