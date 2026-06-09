class TestBaseAPI:
    def test_get_admin_info(self, base_api):
        resp = base_api.get("/admin/info")
        result = base_api.assert_code_ok(resp)
        print(f"用户名: {result['data']['username']}")
