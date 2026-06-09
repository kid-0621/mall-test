"""系统管理模块 test_system.py
UmsResourceCategoryController + UmsResourceController + UmsAdminController

端点清单:
  GET  /resourceCategory/listAll     — 全部资源分类
  POST /resourceCategory/create       — 创建分类
  POST /resourceCategory/update/{id}  — 更新分类
  POST /resourceCategory/delete/{id}  — 删除分类

  GET  /resource/listAll              — 全部资源
  GET  /resource/list                 — 分页搜索
  GET  /resource/{id}                 — 资源详情
  POST /resource/create               — 创建资源 (categoryId必填)
  POST /resource/update/{id}          — 更新资源
  POST /resource/delete/{id}          — 删除资源

  GET  /admin/list                    — 管理员分页
  GET  /admin/{id}                    — 管理员详情
  GET  /admin/role/{adminId}          — 管理员角色
  POST /admin/updateStatus/{id}       — 切换状态
  ⚠️ 不测 admin 的 create/delete/updatePassword，避免影响登录账号
"""

import random
import pytest


# ═══════════════════════════════════════════════
#  资源分类 CASER
# ═══════════════════════════════════════════════
class TestResourceCategory:
    """权限资源分类: 创建→查→改→删"""

    cat_id = None
    cat_name = f"AutoTest分类_{random.randint(10000, 99999)}"

    def test_c_create_category(self, base_api):
        """C: 创建资源分类"""
        body = {"name": self.cat_name, "sort": 0}
        resp = base_api.post("/resourceCategory/create", json=body)
        base_api.assert_code_ok(resp, "创建资源分类")

        # 反查
        search = base_api.get("/resourceCategory/listAll")
        for c in search.json()["data"]:
            if c["name"] == self.cat_name:
                TestResourceCategory.cat_id = c["id"]
                break
        assert TestResourceCategory.cat_id is not None
        print(f"  创建分类 ID={TestResourceCategory.cat_id}: {self.cat_name}")

    def test_s_list_all(self, base_api):
        """S: 查全部"""
        resp = base_api.get("/resourceCategory/listAll")
        base_api.assert_code_ok(resp, "分类列表")
        cats = resp.json()["data"]
        print(f"  分类数: {len(cats)}")
        assert any(c["id"] == TestResourceCategory.cat_id for c in cats)

    def test_e_update_category(self, base_api):
        """E: 更新分类名称+排序"""
        assert TestResourceCategory.cat_id is not None
        new_name = self.cat_name + "_改"
        body = {"name": new_name, "sort": 99}
        resp = base_api.post(f"/resourceCategory/update/{TestResourceCategory.cat_id}", json=body)
        base_api.assert_code_ok(resp, "更新分类")

        # 反查
        verify = base_api.get("/resourceCategory/listAll")
        for c in verify.json()["data"]:
            if c["id"] == TestResourceCategory.cat_id:
                assert c["name"] == new_name
                assert c["sort"] == 99
                break
        print(f"  已更新: {new_name} sort=99")

    def test_r_delete_category(self, base_api):
        """R: 删除 → 反查确认"""
        assert TestResourceCategory.cat_id is not None
        resp = base_api.post(f"/resourceCategory/delete/{TestResourceCategory.cat_id}")
        base_api.assert_code_ok(resp, "删除分类")

        verify = base_api.get("/resourceCategory/listAll")
        ids = [c["id"] for c in verify.json()["data"]]
        assert TestResourceCategory.cat_id not in ids
        print(f"  分类 ID={TestResourceCategory.cat_id} 已删除")


# ═══════════════════════════════════════════════
#  资源 CASER
# ═══════════════════════════════════════════════
class TestResource:
    """权限资源: 创建→查→改→删 (挂靠已有分类)"""

    res_id = None
    res_name = f"AutoTest资源_{random.randint(10000, 99999)}"
    # 挂靠在第一个已有分类上
    parent_cat_id = None

    def test_c_create_resource(self, base_api):
        """C: 创建资源 — 需要 categoryId"""
        # 先查一个已有分类
        cats = base_api.get("/resourceCategory/listAll")
        cat_list = cats.json()["data"]
        assert len(cat_list) > 0
        TestResource.parent_cat_id = cat_list[0]["id"]

        body = {
            "name": self.res_name,
            "url": "/autoTest/**",
            "description": "自动化测试资源",
            "categoryId": TestResource.parent_cat_id
        }
        resp = base_api.post("/resource/create", json=body)
        base_api.assert_code_ok(resp, "创建资源")

        # 反查
        search = base_api.get("/resource/listAll")
        for r in search.json()["data"]:
            if r["name"] == self.res_name:
                TestResource.res_id = r["id"]
                break
        assert TestResource.res_id is not None
        print(f"  创建资源 ID={TestResource.res_id}: {self.res_name} (分类ID={TestResource.parent_cat_id})")

    def test_s_search_resource(self, base_api):
        """S: 查全部 + 查详情"""
        # 全部列表
        resp = base_api.get("/resource/listAll")
        base_api.assert_code_ok(resp, "全部资源")
        total = len(resp.json()["data"])
        print(f"  资源总数: {total}")

        # 分页列表
        resp2 = base_api.get("/resource/list", params={"pageSize": 5, "pageNum": 1})
        base_api.assert_code_ok(resp2, "资源分页")
        print(f"  分页: total={resp2.json()['data']['total']}")

        # 详情
        resp3 = base_api.get(f"/resource/{TestResource.res_id}")
        base_api.assert_code_ok(resp3, "资源详情")
        detail = resp3.json()["data"]
        assert detail["name"] == self.res_name
        assert detail["categoryId"] == TestResource.parent_cat_id
        print(f"  查详情: {self.res_name} url={detail['url']}")

    def test_e_update_resource(self, base_api):
        """E: 更新资源 → 反查确认"""
        assert TestResource.res_id is not None
        new_name = self.res_name + "_改"
        body = {
            "name": new_name,
            "url": "/autoTest_updated/**",
            "description": "已更新的资源",
            "categoryId": TestResource.parent_cat_id
        }
        resp = base_api.post(f"/resource/update/{TestResource.res_id}", json=body)
        base_api.assert_code_ok(resp, "更新资源")

        # 反查
        verify = base_api.get(f"/resource/{TestResource.res_id}")
        verified = verify.json()["data"]
        assert verified["name"] == new_name
        assert verified["url"] == "/autoTest_updated/**"
        print(f"  已更新: {new_name}")

    def test_r_delete_resource(self, base_api):
        """R: 删除 → 反查确认"""
        assert TestResource.res_id is not None
        resp = base_api.post(f"/resource/delete/{TestResource.res_id}")
        base_api.assert_code_ok(resp, "删除资源")

        verify = base_api.get("/resource/listAll")
        ids = [r["id"] for r in verify.json()["data"]]
        assert TestResource.res_id not in ids
        print(f"  资源 ID={TestResource.res_id} 已删除")


# ═══════════════════════════════════════════════
#  管理员查询
# ═══════════════════════════════════════════════
class TestAdminQuery:
    """管理员: 查列表+详情+角色+状态切换 (不测增删改，保护登录账号)"""

    target_admin_id = None
    target_original_status = None
    current_admin_id = None       # 当前登录用户ID

    def test_admin_list(self, base_api):
        """查管理员分页列表"""
        resp = base_api.get("/admin/list", params={"pageSize": 10, "pageNum": 1})
        base_api.assert_code_ok(resp, "管理员列表")
        admins = resp.json()["data"]["list"]
        total = resp.json()["data"]["total"]
        print(f"  管理员: {total} 个")
        for a in admins:
            print(f"    id={a['id']} username={a['username']} status={a['status']}")
            # 记录当前登录的 admin 用户ID
            if a["username"] == "admin":
                TestAdminQuery.current_admin_id = a["id"]
            # 找一个非 admin 用户做后续状态切换测试
            elif TestAdminQuery.target_admin_id is None:
                TestAdminQuery.target_admin_id = a["id"]
                TestAdminQuery.target_original_status = a["status"]

    def test_admin_detail(self, base_api):
        """查管理员详情"""
        assert TestAdminQuery.current_admin_id is not None
        resp = base_api.get(f"/admin/{TestAdminQuery.current_admin_id}")
        base_api.assert_code_ok(resp, "管理员详情")
        detail = resp.json()["data"]
        assert detail.get("username") is not None
        print(f"  当前用户: {detail['username']} nickname={detail.get('nickName','')}")

    def test_admin_roles(self, base_api):
        """查管理员角色列表"""
        assert TestAdminQuery.current_admin_id is not None
        resp = base_api.get(f"/admin/role/{TestAdminQuery.current_admin_id}")
        base_api.assert_code_ok(resp, "管理员角色")
        roles = resp.json()["data"]
        role_names = [r["name"] for r in roles] if roles else []
        print(f"  角色: {role_names}")

    def test_admin_toggle_status(self, base_api):
        """切换非admin用户状态 → 还原"""
        if TestAdminQuery.target_admin_id is None:
            pytest.skip("没有找到可切换状态的非admin用户")
            return

        # 切换
        new_status = 0 if TestAdminQuery.target_original_status == 1 else 1
        resp = base_api.post(f"/admin/updateStatus/{TestAdminQuery.target_admin_id}",
                             params={"status": new_status})
        base_api.assert_code_ok(resp, f"切换状态到{new_status}")

        # 还原
        resp2 = base_api.post(f"/admin/updateStatus/{TestAdminQuery.target_admin_id}",
                              params={"status": TestAdminQuery.target_original_status})
        base_api.assert_code_ok(resp2, f"还原状态到{TestAdminQuery.target_original_status}")
        print(f"  ID={TestAdminQuery.target_admin_id} 状态: {TestAdminQuery.target_original_status} → {new_status} → {TestAdminQuery.target_original_status} ✅")
