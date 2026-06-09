"""BaseAPI - 对 requests 的二次封装，统一加 token、统一断言"""
import requests


class BaseAPI:
    """封装 HTTP 请求，自动携带 token"""

    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": token}
        self.session = requests.Session()
        # Session 复用连接，比每次 requests.get 更高效

    def get(self, path, params=None):
        """封装 GET 请求"""
        url = self.base_url + path
        return self.session.get(url=url, headers=self.headers, params=params)

    def post(self, path, data=None, json=None, params=None):
        """封装 POST 请求，支持 URL 参数（@RequestParam 用 params）"""
        url = self.base_url + path
        return self.session.post(url=url, headers=self.headers, data=data, json=json, params=params)

    def post_form(self, path, data):
        """POST 表单格式（非 JSON）"""
        url = self.base_url + path
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        return self.session.post(url=url, headers=headers, data=data)

    def put(self, path, json=None):
        """封装 PUT 请求"""
        url = self.base_url + path
        return self.session.put(url=url, headers=self.headers, json=json)

    def delete(self, path, params=None):
        """封装 DELETE 请求"""
        url = self.base_url + path
        return self.session.delete(url=url, headers=self.headers, params=params)

    # ───── 常用断言封装 ─────

    def assert_code_ok(self, response, msg=""):
        """断言 HTTP 200 + 业务 code 200"""
        result = response.json()
        assert response.status_code == 200, f"{msg} | HTTP状态码非200"
        assert result["code"] == 200, f"{msg} | 业务code非200, 实际={result['code']}, msg={result['message']}"
        return result

    def assert_code_fail(self, response, msg=""):
        """断言业务层返回失败（code != 200）"""
        result = response.json()
        assert result["code"] != 200, f"{msg} | 期望失败但实际code={result['code']}"
        return result
