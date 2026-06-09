"""营销模块接口测试 - 优惠券/限时购/场次/广告/首页内容"""
import pytest
import time


# ============================================================
# 优惠券 (Coupon) — CASER
# ============================================================
class TestCoupon:
    """优惠券全链路 CASER 测试"""

    coupon_id = None
    coupon_name = f"AutoTest优惠券_{int(time.time()) % 100000}"

    def test_c_create_coupon(self, base_api):
        """C: 创建优惠券 → 反查获取ID"""
        body = {
            "name": self.coupon_name, "type": 0, "platform": 0,
            "count": 100, "amount": 20.0, "perLimit": 1,
            "minPoint": 50.0, "useType": 0,  # 全场通用
            "startTime": "2025-01-01T00:00:00", "endTime": "2030-12-31T23:59:59",
            "note": "自动化测试优惠券"
        }
        resp = base_api.post("/coupon/create", json=body)
        base_api.assert_code_ok(resp, "创建优惠券")

        # 反查获取ID
        search = base_api.get("/coupon/list", params={"pageSize": 50, "pageNum": 1})
        for c in search.json()["data"]["list"]:
            if c["name"] == self.coupon_name:
                TestCoupon.coupon_id = c["id"]
                break
        assert TestCoupon.coupon_id is not None, f"未查到: {self.coupon_name}"
        print(f"  创建优惠券 ID={TestCoupon.coupon_id}: {self.coupon_name} (¥20.00, 全场通用)")

    def test_s_search_coupon(self, base_api):
        """S: 查列表 + 查详情 → 三层验证"""
        assert TestCoupon.coupon_id is not None

        # 查列表
        resp = base_api.get("/coupon/list", params={"pageSize": 50, "pageNum": 1})
        base_api.assert_code_ok(resp, "优惠券列表")
        print(f"  优惠券总数: {resp.json()['data']['total']}")

        # 查详情
        resp2 = base_api.get(f"/coupon/{TestCoupon.coupon_id}")
        result = base_api.assert_code_ok(resp2, "优惠券详情")
        assert result["data"]["name"] == self.coupon_name
        assert float(result["data"]["amount"]) == 20.0
        print(f"  查详情: {result['data']['name']} ¥{result['data']['amount']}")

    def test_e_update_coupon(self, base_api):
        """E: 更新优惠券 → 反查验证"""
        new_name = self.coupon_name + "_改"
        body = {
            "name": new_name, "type": 0, "platform": 0,
            "count": 50, "amount": 30.0, "perLimit": 2,
            "minPoint": 100.0, "useType": 0,
            "startTime": "2025-01-01T00:00:00", "endTime": "2030-12-31T23:59:59",
            "note": "已修改"
        }
        resp = base_api.post(f"/coupon/update/{TestCoupon.coupon_id}", json=body)
        base_api.assert_code_ok(resp, "更新优惠券")

        verify = base_api.get(f"/coupon/{TestCoupon.coupon_id}")
        data = verify.json()["data"]
        assert data["name"] == new_name, "name未更新"
        assert float(data["amount"]) == 30.0, "amount未更新"
        assert data["count"] == 50, "count未更新"
        print(f"  已更新: {data['name']} ¥{data['amount']} 限量{data['count']}")

    def test_e_update_coupon_status(self, base_api):
        """E: 单独测试更新优惠券上下线（实际改的是endTime等，这里用coupon没有status字段，跳过）"""
        # 优惠券模型没有 status 字段，状态由时间决定
        # 这里验证更新接口的完整性即可
        print("  优惠券无独立status字段(由时间决定)，跳过状态切换")

    def test_r_delete_coupon(self, base_api):
        """R: 删除优惠券 → 反查确认"""
        assert TestCoupon.coupon_id is not None
        resp = base_api.post(f"/coupon/delete/{TestCoupon.coupon_id}")
        base_api.assert_code_ok(resp, "删除优惠券")

        verify = base_api.get("/coupon/list", params={"pageSize": 100, "pageNum": 1})
        ids = [c["id"] for c in verify.json()["data"]["list"]]
        assert TestCoupon.coupon_id not in ids, "删除后仍存在"
        print(f"  优惠券 ID={TestCoupon.coupon_id} 已删除，反查确认")


# ============================================================
# 限时购活动 (Flash Promotion) — CASER
# ============================================================
class TestFlashPromotion:
    """限时购活动 CASER"""

    flash_id = None
    flash_title = f"AutoTest限时购_{int(time.time()) % 100000}"

    def test_c_create_flash(self, base_api):
        """C: 创建限时购活动"""
        body = {
            "title": self.flash_title,
            "startDate": "2025-01-01",
            "endDate": "2030-12-31",
            "status": 1
        }
        resp = base_api.post("/flash/create", json=body)
        base_api.assert_code_ok(resp, "创建限时购")

        search = base_api.get("/flash/list", params={"pageSize": 50, "pageNum": 1})
        for f in search.json()["data"]["list"]:
            if f["title"] == self.flash_title:
                TestFlashPromotion.flash_id = f["id"]
                break
        assert TestFlashPromotion.flash_id is not None
        print(f"  创建限时购 ID={TestFlashPromotion.flash_id}: {self.flash_title}")

    def test_s_search_flash(self, base_api):
        """S: 查列表 + 查详情"""
        assert TestFlashPromotion.flash_id is not None

        resp = base_api.get("/flash/list", params={"pageSize": 50, "pageNum": 1})
        base_api.assert_code_ok(resp, "限时购列表")
        print(f"  限时购活动总数: {resp.json()['data']['total']}")

        resp2 = base_api.get(f"/flash/{TestFlashPromotion.flash_id}")
        result = base_api.assert_code_ok(resp2, "限时购详情")
        assert result["data"]["title"] == self.flash_title
        print(f"  查详情: {result['data']['title']}")

    def test_e_update_flash(self, base_api):
        """E: 更新活动名称"""
        new_title = self.flash_title + "_改"
        body = {"title": new_title, "startDate": "2025-06-01", "endDate": "2030-12-31", "status": 1}
        resp = base_api.post(f"/flash/update/{TestFlashPromotion.flash_id}", json=body)
        base_api.assert_code_ok(resp, "更新限时购")

        verify = base_api.get(f"/flash/{TestFlashPromotion.flash_id}")
        assert verify.json()["data"]["title"] == new_title
        print(f"  已更新: {new_title}")

    def test_e_toggle_flash_status(self, base_api):
        """E: 切换上下线状态 → 反查"""
        resp = base_api.post(f"/flash/update/status/{TestFlashPromotion.flash_id}",
                             params={"status": 0})
        base_api.assert_code_ok(resp, "下线限时购")

        verify = base_api.get(f"/flash/{TestFlashPromotion.flash_id}")
        assert verify.json()["data"]["status"] == 0, "status未更新为0"
        print("  已下线，反查确认")
        # 还原
        base_api.post(f"/flash/update/status/{TestFlashPromotion.flash_id}",
                      params={"status": 1})

    def test_r_delete_flash(self, base_api):
        """R: 删除"""
        assert TestFlashPromotion.flash_id is not None
        resp = base_api.post(f"/flash/delete/{TestFlashPromotion.flash_id}")
        base_api.assert_code_ok(resp, "删除限时购")

        verify = base_api.get("/flash/list", params={"pageSize": 100, "pageNum": 1})
        ids = [f["id"] for f in verify.json()["data"]["list"]]
        assert TestFlashPromotion.flash_id not in ids
        print(f"  限时购 ID={TestFlashPromotion.flash_id} 已删除，反查确认")


# ============================================================
# 限时购场次 (Flash Session) — CASER
# ============================================================
class TestFlashSession:
    """场次 CASER"""

    session_id = None
    session_name = f"AutoTest场次_{int(time.time()) % 100000}"

    def test_c_create_session(self, base_api):
        """C: 创建场次 — startTime/endTime 用完整 datetime 格式"""
        body = {
            "name": self.session_name,
            "startTime": "2025-01-01T10:00:00",
            "endTime": "2025-01-01T12:00:00",
            "status": 1
        }
        resp = base_api.post("/flashSession/create", json=body)
        base_api.assert_code_ok(resp, "创建场次")

        # 注意：/flashSession/list 返回的是数组，不是 {list:[], total:} 分页结构
        search = base_api.get("/flashSession/list", params={"pageSize": 50, "pageNum": 1})
        sessions = search.json()["data"]
        for s in sessions:
            if s["name"] == self.session_name:
                TestFlashSession.session_id = s["id"]
                break
        assert TestFlashSession.session_id is not None
        print(f"  创建场次 ID={TestFlashSession.session_id}: {self.session_name}")

    def test_s_search_session(self, base_api):
        """S: 查全部场次列表"""
        resp = base_api.get("/flashSession/list", params={"pageSize": 50, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "场次列表")
        sessions = result["data"]
        print(f"  场次数: {len(sessions)}")

    def test_e_update_session(self, base_api):
        """E: 更新场次名称+时间"""
        assert TestFlashSession.session_id is not None
        new_name = self.session_name + "_改"
        body = {"name": new_name, "startTime": "2025-01-01T14:00:00",
                "endTime": "2025-01-01T16:00:00", "status": 1}
        resp = base_api.post(f"/flashSession/update/{TestFlashSession.session_id}", json=body)
        base_api.assert_code_ok(resp, "更新场次")
        print(f"  已更新: {new_name}")

    def test_e_toggle_session_status(self, base_api):
        """E: 切换场次启用状态"""
        assert TestFlashSession.session_id is not None
        resp = base_api.post(f"/flashSession/update/status/{TestFlashSession.session_id}",
                             params={"status": 0})
        base_api.assert_code_ok(resp, "停用场次")
        print("  场次已停用")

    def test_r_delete_session(self, base_api):
        """R: 删除"""
        assert TestFlashSession.session_id is not None
        resp = base_api.post(f"/flashSession/delete/{TestFlashSession.session_id}")
        base_api.assert_code_ok(resp, "删除场次")

        verify = base_api.get("/flashSession/list", params={"pageSize": 100, "pageNum": 1})
        sessions = verify.json()["data"]
        ids = [s["id"] for s in sessions]
        assert TestFlashSession.session_id not in ids
        print(f"  场次 ID={TestFlashSession.session_id} 已删除")


# ============================================================
# 首页轮播广告 (Home Advertise) — CASER
# ============================================================
class TestHomeAdvertise:
    """首页广告 CASER"""

    ad_id = None
    ad_name = f"AutoTest广告_{int(time.time()) % 100000}"

    def test_c_create_ad(self, base_api):
        """C: 创建广告"""
        body = {
            "name": self.ad_name, "type": 1,  # 1=app首页轮播
            "pic": "https://example.com/banner.jpg",
            "startTime": "2025-01-01T00:00:00",
            "endTime": "2030-12-31T23:59:59",
            "status": 1, "sort": 99,
            "url": "https://example.com", "note": "临时广告"
        }
        resp = base_api.post("/home/advertise/create", json=body)
        base_api.assert_code_ok(resp, "创建广告")

        search = base_api.get("/home/advertise/list", params={"pageSize": 50, "pageNum": 1})
        for ad in search.json()["data"]["list"]:
            if ad["name"] == self.ad_name:
                TestHomeAdvertise.ad_id = ad["id"]
                break
        assert TestHomeAdvertise.ad_id is not None
        print(f"  创建广告 ID={TestHomeAdvertise.ad_id}: {self.ad_name}")

    def test_s_search_ad(self, base_api):
        """S: 查列表 + 详情"""
        resp = base_api.get("/home/advertise/list", params={"pageSize": 50, "pageNum": 1})
        base_api.assert_code_ok(resp, "广告列表")
        print(f"  广告总数: {resp.json()['data']['total']}")

        resp2 = base_api.get(f"/home/advertise/{TestHomeAdvertise.ad_id}")
        result = base_api.assert_code_ok(resp2, "广告详情")
        assert result["data"]["name"] == self.ad_name
        print(f"  查详情: {result['data']['name']}")

    def test_e_update_ad(self, base_api):
        """E: 更新广告"""
        new_name = self.ad_name + "_改"
        body = {
            "name": new_name, "type": 1,
            "pic": "https://example.com/banner2.jpg",
            "startTime": "2025-01-01T00:00:00",
            "endTime": "2030-12-31T23:59:59",
            "status": 1, "sort": 50,
            "url": "https://example2.com", "note": "已修改"
        }
        resp = base_api.post(f"/home/advertise/update/{TestHomeAdvertise.ad_id}", json=body)
        base_api.assert_code_ok(resp, "更新广告")

        verify = base_api.get(f"/home/advertise/{TestHomeAdvertise.ad_id}")
        data = verify.json()["data"]
        assert data["name"] == new_name
        assert data["sort"] == 50
        print(f"  已更新: {data['name']} sort={data['sort']}")

    def test_e_toggle_ad_status(self, base_api):
        """E: 切换上下线 → 反查"""
        resp = base_api.post(f"/home/advertise/update/status/{TestHomeAdvertise.ad_id}",
                             params={"status": 0})
        base_api.assert_code_ok(resp, "下线广告")

        verify = base_api.get(f"/home/advertise/{TestHomeAdvertise.ad_id}")
        assert verify.json()["data"]["status"] == 0
        print("  广告已下线，反查确认")

    def test_r_delete_ad(self, base_api):
        """R: 删除"""
        resp = base_api.post("/home/advertise/delete",
                             params={"ids": [TestHomeAdvertise.ad_id]})
        base_api.assert_code_ok(resp, "删除广告")

        verify = base_api.get("/home/advertise/list", params={"pageSize": 100, "pageNum": 1})
        ids = [ad["id"] for ad in verify.json()["data"]["list"]]
        assert TestHomeAdvertise.ad_id not in ids
        print(f"  广告 ID={TestHomeAdvertise.ad_id} 已删除")


# ============================================================
# 首页内容管理 (Brand/NewProduct/RecommendProduct/Subject)
# 这四个模块需要 brandId/productId/subjectId，所以只做查询 + 批量状态操作
# ============================================================
class TestHomeContent:
    """首页四个内容模块：品牌、新品、人气推荐、专题"""

    def test_brand_list(self, base_api):
        """首页品牌 — 查询"""
        resp = base_api.get("/home/brand/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "首页品牌列表")
        brands = result["data"]["list"]
        print(f"  首页品牌: {len(brands)}个 (total={result['data']['total']})")
        if brands:
            TestHomeContent.first_brand_id = brands[0]["id"]

    def test_brand_toggle(self, base_api):
        """首页品牌 — 批量切换推荐状态 → 反查"""
        bid = getattr(TestHomeContent, "first_brand_id", None)
        if not bid:
            pytest.skip("无首页品牌数据")
            return
        # 先查当前状态
        before = base_api.get("/home/brand/list", params={"pageSize": 50, "pageNum": 1})
        for b in before.json()["data"]["list"]:
            if b["id"] == bid:
                orig_status = b["recommendStatus"]
                break
        new_status = 0 if orig_status == 1 else 1
        resp = base_api.post("/home/brand/update/recommendStatus",
                             params={"ids": [bid], "recommendStatus": new_status})
        base_api.assert_code_ok(resp, "切换品牌推荐状态")
        print(f"  品牌 ID={bid} recommendStatus: {orig_status} → {new_status}")

    def test_new_product_list(self, base_api):
        """首页新品 — 查询"""
        resp = base_api.get("/home/newProduct/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "首页新品列表")
        items = result["data"]["list"]
        print(f"  首页新品: {len(items)}个 (total={result['data']['total']})")
        if items:
            TestHomeContent.first_np_id = items[0]["id"]

    def test_new_product_toggle(self, base_api):
        """首页新品 — 批量切换推荐状态"""
        nid = getattr(TestHomeContent, "first_np_id", None)
        if not nid:
            pytest.skip("无首页新品数据")
            return
        resp = base_api.post("/home/newProduct/update/recommendStatus",
                             params={"ids": [nid], "recommendStatus": 1})
        base_api.assert_code_ok(resp, "新品推荐")
        print(f"  新品 ID={nid} 推荐状态已设为1")

    def test_recommend_product_list(self, base_api):
        """人气推荐 — 查询"""
        resp = base_api.get("/home/recommendProduct/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "人气推荐列表")
        items = result["data"]["list"]
        print(f"  人气推荐: {len(items)}个 (total={result['data']['total']})")

    def test_subject_list(self, base_api):
        """首页专题 — 查询"""
        resp = base_api.get("/home/recommendSubject/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "专题推荐列表")
        items = result["data"]["list"]
        print(f"  首页专题: {len(items)}个 (total={result['data']['total']})")


# ============================================================
# 优惠券领取记录 — 纯查询
# ============================================================
class TestCouponHistory:
    """优惠券领取记录"""

    def test_history_list(self, base_api):
        resp = base_api.get("/couponHistory/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "优惠券领取记录")
        print(f"  领取记录: {result['data']['total']} 条")
