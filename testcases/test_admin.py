"""用户模块接口测试 - 角色/菜单/资源/管理员"""
import pytest
import time


class TestRole:
    """角色管理 CASER 测试"""

    role_id = None
    role_name = f"AutoTest角色_{int(time.time()) % 100000}"

    def test_c_create_role(self, base_api):
        """C: 创建角色"""
        body = {"name": self.role_name, "description": "测试角色", "adminCount": 0, "sort": 0, "status": 1}
        resp = base_api.post("/role/create", json=body)
        result = base_api.assert_code_ok(resp, "创建角色")

        # 反查获取 ID
        search_resp = base_api.get("/role/list", params={"keyword": self.role_name, "pageSize": 5, "pageNum": 1})
        roles = search_resp.json()["data"]["list"]
        assert len(roles) > 0, f"未查到角色: {self.role_name}"
        TestRole.role_id = roles[0]["id"]
        print(f"  创建角色 ID={TestRole.role_id}: {self.role_name}")

    def test_s_search_role(self, base_api):
        """S: 查询角色列表和详情"""
        assert TestRole.role_id is not None
        # 查列表
        resp = base_api.get("/role/listAll")
        result = base_api.assert_code_ok(resp, "获取所有角色")
        print(f"  角色总数: {len(result['data'])}")

        # 查分配菜单
        resp2 = base_api.get(f"/role/listMenu/{TestRole.role_id}")
        base_api.assert_code_ok(resp2, "获取角色菜单")
        print(f"  角色菜单获取正常")

    def test_e_update_role(self, base_api):
        """E: 更新角色状态和名称"""
        assert TestRole.role_id is not None
        # 更新状态为禁用
        resp = base_api.post(f"/role/updateStatus/{TestRole.role_id}", params={"status": 0})
        base_api.assert_code_ok(resp, "禁用角色")

        # 验证状态
        detail_resp = base_api.get("/role/listAll")
        roles = detail_resp.json()["data"]
        target = [r for r in roles if r["id"] == TestRole.role_id]
        assert len(target) > 0 and target[0]["status"] == 0, "状态未更新为0"
        print(f"  角色状态已切换为禁用")

    def test_a_assign_menu(self, base_api):
        """A: 给角色分配菜单"""
        assert TestRole.role_id is not None
        resp = base_api.post("/role/allocMenu", params={"roleId": TestRole.role_id, "menuIds": [1, 2]})
        base_api.assert_code_ok(resp, "分配菜单")

        # 第3层：反查验证 — 菜单确实挂上了
        verify_resp = base_api.get(f"/role/listMenu/{TestRole.role_id}")
        verify_result = base_api.assert_code_ok(verify_resp, "反查角色菜单")
        assigned_ids = [m["id"] for m in verify_result["data"]]
        assert 1 in assigned_ids, f"菜单1未分配成功，实际分配={assigned_ids}"
        assert 2 in assigned_ids, f"菜单2未分配成功，实际分配={assigned_ids}"
        print(f"  已为角色分配菜单 [1, 2]，反查确认: {assigned_ids}")

    def test_r_delete_role(self, base_api):
        """R: 删除角色"""
        assert TestRole.role_id is not None
        resp = base_api.post("/role/delete", params={"ids": [TestRole.role_id]})
        base_api.assert_code_ok(resp, "删除角色")

        # 第3层：反查验证 — 角色已不在列表里
        verify_resp = base_api.get("/role/listAll")
        roles = verify_resp.json()["data"]
        deleted_ids = [r["id"] for r in roles]
        assert TestRole.role_id not in deleted_ids, f"角色 ID={TestRole.role_id} 删除后仍存在"
        print(f"  角色 ID={TestRole.role_id} 已删除，反查确认不存在")


class TestMenu:
    """菜单管理测试"""

    menu_id = None
    menu_title = f"AutoTest菜单_{int(time.time()) % 100000}"

    def test_c_create_menu(self, base_api):
        body = {"parentId": 0, "title": self.menu_title, "name": "auto_menu", "icon": "test", "level": 0, "sort": 0,
                "hidden": 0}
        resp = base_api.post("/menu/create", json=body)
        base_api.assert_code_ok(resp, "创建菜单")

        # 反查
        search_resp = base_api.get("/menu/list/0", params={"pageSize": 50, "pageNum": 1})
        menus = search_resp.json()["data"]["list"]
        for m in menus:
            if m["title"] == self.menu_title:
                TestMenu.menu_id = m["id"]
                break
        assert TestMenu.menu_id is not None
        print(f"  创建菜单 ID={TestMenu.menu_id}: {self.menu_title}")

    def test_s_tree_list(self, base_api):
        resp = base_api.get("/menu/treeList")
        base_api.assert_code_ok(resp, "获取菜单树")
        print(f"  菜单树: {len(str(resp.json()['data']))} 字符")

    def test_e_toggle_hidden(self, base_api):
        assert TestMenu.menu_id is not None
        resp = base_api.post(f"/menu/updateHidden/{TestMenu.menu_id}", params={"hidden": 1})
        base_api.assert_code_ok(resp, "隐藏菜单")

        # 第3层：反查验证 — hidden 确实变成了 1
        verify_resp = base_api.get(f"/menu/{TestMenu.menu_id}")
        verify_result = base_api.assert_code_ok(verify_resp, "反查菜单详情")
        assert verify_result["data"]["hidden"] == 1, f"hidden值未更新，实际={verify_result['data']['hidden']}"
        print(f"  菜单已设为隐藏，反查确认 hidden={verify_result['data']['hidden']}")

    def test_e_update_menu(self, base_api):
        assert TestMenu.menu_id is not None
        new_title = self.menu_title + "_改"
        body = {"parentId": 0, "title": new_title, "name": "auto_menu", "icon": "new", "level": 0,
                "sort": 99, "hidden": 0}
        resp = base_api.post(f"/menu/update/{TestMenu.menu_id}", json=body)
        base_api.assert_code_ok(resp, "更新菜单")

        # 第3层：反查验证 — name 和 sort 确实变了
        verify_resp = base_api.get(f"/menu/{TestMenu.menu_id}")
        verify_result = base_api.assert_code_ok(verify_resp, "反查菜单详情")
        assert verify_result["data"]["title"] == new_title, f"title未更新，实际={verify_result['data']['title']}"
        assert verify_result["data"]["sort"] == 99, f"sort未更新，实际={verify_result['data']['sort']}"
        print(f"  菜单已更新，反查确认 title={verify_result['data']['title']} sort={verify_result['data']['sort']}")

    def test_r_delete_menu(self, base_api):
        assert TestMenu.menu_id is not None
        resp = base_api.post(f"/menu/delete/{TestMenu.menu_id}")
        base_api.assert_code_ok(resp, "删除菜单")

        # 第3层：反查验证 — 列表里找不到这个菜单
        verify_resp = base_api.get("/menu/list/0", params={"pageSize": 100, "pageNum": 1})
        menus = verify_resp.json()["data"]["list"]
        deleted_ids = [m["id"] for m in menus]
        assert TestMenu.menu_id not in deleted_ids, f"菜单 ID={TestMenu.menu_id} 删除后仍存在于列表中"
        print(f"  菜单 ID={TestMenu.menu_id} 已删除，反查确认不存在")


class TestMemberLevel:
    """会员等级 - 简单查询"""

    def test_list_show(self, base_api):
        resp = base_api.get("/memberLevel/list", params={"defaultStatus": 0})
        base_api.assert_code_ok(resp, "查会员等级")
        print(f"  会员等级: {len(resp.json()['data'])} 个")
