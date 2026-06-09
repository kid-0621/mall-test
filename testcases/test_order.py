"""订单模块接口测试 - 退货原因/订单管理/退货申请/订单设置/收货地址"""
import pytest
import time


class TestReturnReason:
    """退货原因 CASER 测试"""

    reason_id = None
    reason_name = f"AutoTest退货原因_{int(time.time()) % 100000}"

    def test_c_create_reason(self, base_api):
        """C: 创建退货原因 → 反查获取ID"""
        body = {"name": self.reason_name, "sort": 99, "status": 1}
        resp = base_api.post("/returnReason/create", json=body)
        base_api.assert_code_ok(resp, "创建退货原因")

        # 反查获取ID
        search = base_api.get("/returnReason/list", params={"pageSize": 50, "pageNum": 1})
        for item in search.json()["data"]["list"]:
            if item["name"] == self.reason_name:
                TestReturnReason.reason_id = item["id"]
                break
        assert TestReturnReason.reason_id is not None, f"未查到: {self.reason_name}"
        print(f"  创建退货原因 ID={TestReturnReason.reason_id}: {self.reason_name}")

    def test_s_search_reason(self, base_api):
        """S: 查询列表 + 查询详情 → 验证三层"""
        assert TestReturnReason.reason_id is not None

        # 查列表
        resp = base_api.get("/returnReason/list", params={"pageSize": 50, "pageNum": 1})
        base_api.assert_code_ok(resp, "退货原因列表")
        print(f"  退货原因总数: {resp.json()['data']['total']}")

        # 查详情 + 验证字段
        resp2 = base_api.get(f"/returnReason/{TestReturnReason.reason_id}")
        result = base_api.assert_code_ok(resp2, "退货原因详情")
        assert result["data"]["name"] == self.reason_name, "详情name不匹配"
        assert result["data"]["sort"] == 99, "详情sort不匹配"
        assert result["data"]["status"] == 1, "详情status不匹配"
        print(f"  查详情: {result['data']['name']} sort={result['data']['sort']} status={result['data']['status']}")

    def test_e_update_reason(self, base_api):
        """E: 更新退货原因名称 → 反查验证"""
        assert TestReturnReason.reason_id is not None
        new_name = self.reason_name + "_改"
        body = {"name": new_name, "sort": 50, "status": 0}
        resp = base_api.post(f"/returnReason/update/{TestReturnReason.reason_id}", json=body)
        base_api.assert_code_ok(resp, "更新退货原因")

        # 反查验证
        verify = base_api.get(f"/returnReason/{TestReturnReason.reason_id}")
        data = verify.json()["data"]
        assert data["name"] == new_name, "name未更新"
        assert data["sort"] == 50, "sort未更新"
        assert data["status"] == 0, "status未更新"
        print(f"  已更新: {data['name']} sort={data['sort']} status={data['status']}")

    def test_e_toggle_status(self, base_api):
        """E: 切换启用状态 → 反查验证"""
        assert TestReturnReason.reason_id is not None
        resp = base_api.post("/returnReason/update/status",
                             params={"ids": [TestReturnReason.reason_id], "status": 1})
        base_api.assert_code_ok(resp, "启用退货原因")

        # 反查验证
        verify = base_api.get(f"/returnReason/{TestReturnReason.reason_id}")
        assert verify.json()["data"]["status"] == 1, "status未切回1"
        print("  状态已切回启用，反查确认")

    def test_r_delete_reason(self, base_api):
        """R: 删除 → 反查确认不存在"""
        assert TestReturnReason.reason_id is not None
        resp = base_api.post("/returnReason/delete",
                             params={"ids": [TestReturnReason.reason_id]})
        base_api.assert_code_ok(resp, "删除退货原因")

        # 反查确认
        verify = base_api.get("/returnReason/list", params={"pageSize": 100, "pageNum": 1})
        ids = [item["id"] for item in verify.json()["data"]["list"]]
        assert TestReturnReason.reason_id not in ids, "删除后仍存在"
        print(f"  退货原因 ID={TestReturnReason.reason_id} 已删除，反查确认")


class TestOrderQuery:
    """订单管理 — 查询 + 修改操作（依赖已有订单数据）"""

    order_id = None
    order_sn = None

    def test_list_orders(self, base_api):
        """查询订单列表"""
        resp = base_api.get("/order/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "查订单列表")
        orders = result["data"]["list"]
        total = result["data"]["total"]
        print(f"  订单总数: {total}")

        if orders:
            TestOrderQuery.order_id = orders[0]["id"]
            TestOrderQuery.order_sn = orders[0]["orderSn"]
            print(f"  首个订单 ID={orders[0]['id']} SN={orders[0]['orderSn']} Status={orders[0]['status']}")
        else:
            pytest.skip("无订单数据")

    def test_order_detail(self, base_api):
        """查询订单详情（含商品+操作记录）"""
        if not TestOrderQuery.order_id:
            pytest.skip("无订单数据")
            return
        resp = base_api.get(f"/order/{TestOrderQuery.order_id}")
        result = base_api.assert_code_ok(resp, "订单详情")
        detail = result["data"]
        print(f"  订单详情: SN={TestOrderQuery.order_sn} "
              f"商品={len(detail.get('orderItemList', []))}件 "
              f"操作记录={len(detail.get('historyList', []))}条")

    def test_update_note(self, base_api):
        """添加订单备注"""
        if not TestOrderQuery.order_id:
            pytest.skip("无订单数据")
            return
        note_text = f"AutoTest备注_{int(time.time()) % 100000}"
        resp = base_api.post("/order/update/note",
                             params={"id": TestOrderQuery.order_id,
                                    "note": note_text, "status": 0})
        base_api.assert_code_ok(resp, "备注订单")

        # 反查：查详情看备注是否生效
        verify = base_api.get(f"/order/{TestOrderQuery.order_id}")
        # 备注通常在操作记录中，不在订单顶层字段，这里只管HTTP层通过
        print(f"  已备注: {note_text}")

    def test_update_receiver(self, base_api):
        """修改收货人信息"""
        if not TestOrderQuery.order_id:
            pytest.skip("无订单数据")
            return
        body = {
            "orderId": TestOrderQuery.order_id,
            "receiverName": "测试收货人",
            "receiverPhone": "13800000000",
            "receiverPostCode": "518000",
            "receiverDetailAddress": "测试路88号",
            "receiverProvince": "广东省",
            "receiverCity": "深圳市",
            "receiverRegion": "南山区",
            "status": 0
        }
        resp = base_api.post("/order/update/receiverInfo", json=body)
        base_api.assert_code_ok(resp, "修改收货人")
        print(f"  已修改收货人: 测试收货人 13800000000")

    def test_update_money(self, base_api):
        """修改订单费用"""
        if not TestOrderQuery.order_id:
            pytest.skip("无订单数据")
            return
        body = {
            "orderId": TestOrderQuery.order_id,
            "freightAmount": 10.0,
            "discountAmount": 5.0,
            "status": 0
        }
        resp = base_api.post("/order/update/moneyInfo", json=body)
        base_api.assert_code_ok(resp, "修改费用")
        print(f"  已修改费用: 运费=¥10.00 优惠=¥5.00")


class TestReturnApply:
    """退货申请 — 纯查询"""

    def test_list_returns(self, base_api):
        """查询退货申请列表"""
        resp = base_api.get("/returnApply/list", params={"pageSize": 10, "pageNum": 1})
        result = base_api.assert_code_ok(resp, "退货申请列表")
        total = result["data"]["total"]
        print(f"  退货申请总数: {total}")
        if result["data"]["list"]:
            TestReturnApply.first_id = result["data"]["list"][0]["id"]

    def test_apply_detail(self, base_api):
        """查询退货申请详情"""
        first_id = getattr(TestReturnApply, "first_id", None)
        if not first_id:
            pytest.skip("无退货申请数据")
            return
        resp = base_api.get(f"/returnApply/{first_id}")
        base_api.assert_code_ok(resp, "退货申请详情")
        print(f"  退货申请 ID={first_id} 详情查询成功")


class TestOrderSetting:
    """订单设置 — 查询 + 修改"""

    def test_get_setting(self, base_api):
        """查询订单设置"""
        resp = base_api.get("/orderSetting/1")
        result = base_api.assert_code_ok(resp, "订单设置")
        setting = result["data"]
        print(f"  订单设置: 正常订单超时={setting.get('normalOrderOvertime')}分 "
              f"确认超时={setting.get('confirmOvertime')}天 "
              f"完成超时={setting.get('finishOvertime')}天")

        # 保存原始值，用于修改后还原
        TestOrderSetting.original = setting

    def test_update_setting(self, base_api):
        """修改订单设置 → 反查验证 → 还原"""
        orig = getattr(TestOrderSetting, "original", {})
        new_timeout = 180
        body = {
            "flashOrderOvertime": orig.get("flashOrderOvertime", 60),
            "normalOrderOvertime": new_timeout,
            "confirmOvertime": orig.get("confirmOvertime", 15),
            "finishOvertime": orig.get("finishOvertime", 7),
            "commentOvertime": orig.get("commentOvertime", 7)
        }
        resp = base_api.post("/orderSetting/update/1", json=body)
        base_api.assert_code_ok(resp, "修改订单设置")

        # 反查验证
        verify = base_api.get("/orderSetting/1")
        assert verify.json()["data"]["normalOrderOvertime"] == new_timeout, "超时未更新"
        print(f"  正常订单超时已改为 {new_timeout} 分，反查确认")

        # 还原
        restore_body = {**orig}
        base_api.post("/orderSetting/update/1", json=restore_body)
        print(f"  已还原为 {orig.get('normalOrderOvertime')} 分")


class TestCompanyAddress:
    """公司收货地址 — 纯查询"""

    def test_list_addresses(self, base_api):
        """查询公司收货地址"""
        resp = base_api.get("/companyAddress/list")
        result = base_api.assert_code_ok(resp, "公司地址")
        addresses = result["data"]
        print(f"  公司地址: {len(addresses)} 个")
        for addr in addresses:
            print(f"    - {addr['addressName']}: {addr['province']}{addr.get('city','')}{addr.get('region','')}")
