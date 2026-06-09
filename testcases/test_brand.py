"""商品品牌模块 test_brand.py
PmsBrandController: 9个端点 → CASER 5条

端点清单:
  GET  /brand/listAll          — 全部品牌列表
  POST /brand/create           — 创建品牌 (name+logo 必填)
  POST /brand/update/{id}      — 更新品牌
  GET  /brand/delete/{id}      — 删除品牌 ⚠️ 注意: 这个接口是 GET 方法!
  GET  /brand/list             — 分页搜索
  GET  /brand/{id}             — 品牌详情
  POST /brand/delete/batch     — 批量删除
  POST /brand/update/showStatus    — 批量切换显示状态
  POST /brand/update/factoryStatus — 批量切换制造商状态
"""

import random
import pytest


class TestBrand:
    """品牌 CASER: 创建→查→改→状态→删"""

    brand_id = None
    brand_name = f"AutoTest品牌_{random.randint(10000, 99999)}"

    # ── C: 创建 ──────────────────────────────────
    def test_c_create_brand(self, base_api):
        """C: 创建品牌 — name + logo 必填"""
        body = {
            "name": self.brand_name,
            "firstLetter": "A",
            "sort": 10,
            "factoryStatus": 1,
            "showStatus": 1,
            "logo": "http://example.com/logo.png",
            "bigPic": "",
            "brandStory": "自动化测试品牌"
        }
        resp = base_api.post("/brand/create", json=body)
        base_api.assert_code_ok(resp, "创建品牌")

        # 反查: listAll 找到刚创建的ID
        search = base_api.get("/brand/listAll")
        for b in search.json()["data"]:
            if b["name"] == self.brand_name:
                TestBrand.brand_id = b["id"]
                break
        assert TestBrand.brand_id is not None
        print(f"  创建品牌 ID={TestBrand.brand_id}: {self.brand_name}")

    # ── S: 查询 ──────────────────────────────────
    def test_s_search_brand(self, base_api):
        """S: 查全部 → 查详情"""
        # 查全部
        resp = base_api.get("/brand/listAll")
        base_api.assert_code_ok(resp, "全部品牌")
        total = len(resp.json()["data"])
        print(f"  品牌总数: {total}")

        # 查分页
        resp2 = base_api.get("/brand/list", params={"pageSize": 5, "pageNum": 1})
        base_api.assert_code_ok(resp2, "品牌分页")
        print(f"  分页: total={resp2.json()['data']['total']}")

        # 查详情
        resp3 = base_api.get(f"/brand/{TestBrand.brand_id}")
        base_api.assert_code_ok(resp3, "品牌详情")
        detail = resp3.json()["data"]
        assert detail["name"] == self.brand_name
        print(f"  查详情: {self.brand_name} sort={detail['sort']}")

    # ── E: 更新 ──────────────────────────────────
    def test_e_update_brand(self, base_api):
        """E: 更新品牌名称+排序 → 反查确认"""
        assert TestBrand.brand_id is not None
        new_name = self.brand_name + "_改"
        body = {
            "name": new_name,
            "firstLetter": "B",
            "sort": 99,
            "factoryStatus": 1,
            "showStatus": 1,
            "logo": "http://example.com/logo2.png",
            "bigPic": "",
            "brandStory": "已更新的品牌"
        }
        resp = base_api.post(f"/brand/update/{TestBrand.brand_id}", json=body)
        base_api.assert_code_ok(resp, "更新品牌")

        # 反查确认
        verify = base_api.get(f"/brand/{TestBrand.brand_id}")
        verified = verify.json()["data"]
        assert verified["name"] == new_name
        assert verified["sort"] == 99
        print(f"  已更新: {new_name} sort={verified['sort']}")

    # ── E: 批量状态 ──────────────────────────────
    def test_e_toggle_show_status(self, base_api):
        """E: 批量关闭显示 → 反查确认"""
        assert TestBrand.brand_id is not None
        resp = base_api.post("/brand/update/showStatus",
                             params={"ids": str(TestBrand.brand_id), "showStatus": 0})
        base_api.assert_code_ok(resp, "关闭显示")

        # 反查
        verify = base_api.get(f"/brand/{TestBrand.brand_id}")
        assert verify.json()["data"]["showStatus"] == 0
        print(f"  品牌 ID={TestBrand.brand_id} 已下架")

    # ── R: 删除 ──────────────────────────────────
    def test_r_delete_brand(self, base_api):
        """R: 删除 → 反查确认不存在"""
        assert TestBrand.brand_id is not None
        # ⚠️ 这个接口是 GET 方法
        resp = base_api.get(f"/brand/delete/{TestBrand.brand_id}")
        base_api.assert_code_ok(resp, "删除品牌")

        # 反查: listAll 里不再出现
        verify = base_api.get("/brand/listAll")
        ids = [b["id"] for b in verify.json()["data"]]
        assert TestBrand.brand_id not in ids
        print(f"  品牌 ID={TestBrand.brand_id} 已删除，反查确认")
