"""商品模块接口测试 - 商品分类/属性分类/商品属性/商品/SKU/专题/优选"""
import pytest
import time


class TestProductCategory:
    """商品分类 CASER 测试"""

    cat_id = None
    cat_name = f"AutoTest分类_{int(time.time()) % 100000}"

    def test_c_create_category(self, base_api):
        """C: 创建商品分类"""
        body = {"parentId": 0, "name": self.cat_name, "productUnit": "件", "navStatus": 1,
                "showStatus": 1, "sort": 0, "keywords": "测试", "description": "临时分类"}
        resp = base_api.post("/productCategory/create", json=body)
        base_api.assert_code_ok(resp, "创建分类")

        # 反查获取ID
        search_resp = base_api.get("/productCategory/list/0", params={"pageSize": 50, "pageNum": 1})
        for c in search_resp.json()["data"]["list"]:
            if c["name"] == self.cat_name:
                TestProductCategory.cat_id = c["id"]
                break
        assert TestProductCategory.cat_id is not None, f"未查到: {self.cat_name}"
        print(f"  创建分类 ID={TestProductCategory.cat_id}: {self.cat_name}")

    def test_s_search_category(self, base_api):
        """S: 查询分类"""
        assert TestProductCategory.cat_id is not None
        resp = base_api.get("/productCategory/list/withChildren")
        base_api.assert_code_ok(resp, "查分类树")
        print(f"  分类树: {len(resp.json()['data'])} 个一级分类")

        resp2 = base_api.get(f"/productCategory/{TestProductCategory.cat_id}")
        result = base_api.assert_code_ok(resp2, "查详情")
        assert result["data"]["name"] == self.cat_name
        print(f"  查详情: {result['data']['name']}")

    def test_e_toggle_nav_status(self, base_api):
        """E: 切换导航栏状态 → 反查验证"""
        assert TestProductCategory.cat_id is not None
        resp = base_api.post("/productCategory/update/navStatus",
                             params={"ids": [TestProductCategory.cat_id], "navStatus": 0})
        base_api.assert_code_ok(resp, "关闭导航显示")

        verify_resp = base_api.get(f"/productCategory/{TestProductCategory.cat_id}")
        assert verify_resp.json()["data"]["navStatus"] == 0, "navStatus未更新为0"
        print("  导航显示已关闭，反查确认")

    def test_e_update_category(self, base_api):
        """E: 更新分类名称 → 反查验证"""
        assert TestProductCategory.cat_id is not None
        new_name = self.cat_name + "_改"
        body = {"parentId": 0, "name": new_name, "productUnit": "箱", "navStatus": 0, "showStatus": 1, "sort": 99}
        resp = base_api.post(f"/productCategory/update/{TestProductCategory.cat_id}", json=body)
        base_api.assert_code_ok(resp, "更新分类")

        verify = base_api.get(f"/productCategory/{TestProductCategory.cat_id}")
        data = verify.json()["data"]
        assert data["name"] == new_name
        assert data["sort"] == 99
        print(f"  已更新: {data['name']} sort={data['sort']}")

    def test_r_delete_category(self, base_api):
        """R: 删除 → 反查确认不存在"""
        assert TestProductCategory.cat_id is not None
        resp = base_api.post(f"/productCategory/delete/{TestProductCategory.cat_id}")
        base_api.assert_code_ok(resp, "删除")

        verify = base_api.get("/productCategory/list/0", params={"pageSize": 100, "pageNum": 1})
        ids = [c["id"] for c in verify.json()["data"]["list"]]
        assert TestProductCategory.cat_id not in ids, "删除后仍存在"
        print(f"  分类 ID={TestProductCategory.cat_id} 已删除，反查确认")


class TestAttributeCategory:
    """商品属性分类 CASER"""

    ac_id = None
    ac_name = f"AutoTest属性分类_{int(time.time()) % 100000}"

    def test_c_create_attr_category(self, base_api):
        resp = base_api.post("/productAttribute/category/create", params={"name": self.ac_name})
        base_api.assert_code_ok(resp, "创建属性分类")

        search = base_api.get("/productAttribute/category/list", params={"pageSize": 50})
        for a in search.json()["data"]["list"]:
            if a["name"] == self.ac_name:
                TestAttributeCategory.ac_id = a["id"]
                break
        assert TestAttributeCategory.ac_id is not None
        print(f"  创建属性分类 ID={TestAttributeCategory.ac_id}: {self.ac_name}")

    def test_s_search_attr_category(self, base_api):
        resp = base_api.get("/productAttribute/category/list/withAttr")
        base_api.assert_code_ok(resp, "查属性分类+属性")
        print(f"  属性分类(含属性): {len(resp.json()['data'])} 个")

    def test_e_update_attr_category(self, base_api):
        new_name = self.ac_name + "_改"
        resp = base_api.post(f"/productAttribute/category/update/{TestAttributeCategory.ac_id}",
                             params={"name": new_name})
        base_api.assert_code_ok(resp, "更新属性分类")
        print(f"  已更新: {new_name}")

    def test_r_delete_attr_category(self, base_api):
        assert TestAttributeCategory.ac_id is not None
        resp = base_api.get(f"/productAttribute/category/delete/{TestAttributeCategory.ac_id}")
        base_api.assert_code_ok(resp, "删除属性分类")

        verify = base_api.get("/productAttribute/category/list", params={"pageSize": 100})
        ids = [a["id"] for a in verify.json()["data"]["list"]]
        assert TestAttributeCategory.ac_id not in ids
        print(f"  属性分类 ID={TestAttributeCategory.ac_id} 已删除，反查确认")


class TestProductAttribute:
    """商品属性 CRUD — 依赖属性分类"""

    attr_id = None
    attr_name = f"AutoTest属性_{int(time.time()) % 100000}"

    @pytest.fixture(scope="class")
    def attr_category_id(self, base_api):
        """准备测试用的属性分类"""
        name = f"temp_attr_cat_{int(time.time()) % 100000}"
        base_api.post("/productAttribute/category/create", params={"name": name})
        search = base_api.get("/productAttribute/category/list", params={"pageSize": 50})
        for a in search.json()["data"]["list"]:
            if a["name"] == name:
                cat_id = a["id"]
                yield cat_id
                base_api.get(f"/productAttribute/category/delete/{cat_id}")
                return

    def test_c_create_attr(self, base_api, attr_category_id):
        body = {"productAttributeCategoryId": attr_category_id, "name": self.attr_name,
                "selectType": 1, "inputType": 0, "inputList": "选项A,选项B",
                "sort": 0, "filterType": 0, "searchType": 0, "type": 0}
        resp = base_api.post("/productAttribute/create", json=body)
        base_api.assert_code_ok(resp, "创建属性")

        search = base_api.get(f"/productAttribute/list/{attr_category_id}",
                              params={"type": 0, "pageSize": 50})
        items = search.json()["data"]["list"]
        for item in items:
            if item["name"] == self.attr_name:
                TestProductAttribute.attr_id = item["id"]
                break
        assert TestProductAttribute.attr_id is not None
        print(f"  创建属性 ID={TestProductAttribute.attr_id}")

    def test_s_search_attr(self, base_api, attr_category_id):
        resp = base_api.get(f"/productAttribute/attrInfo/{attr_category_id}")
        base_api.assert_code_ok(resp, "查属性+分类")
        print("  属性关联查询正常")

    def test_e_update_attr(self, base_api):
        body = {"name": self.attr_name + "_改", "selectType": 2, "inputType": 1,
                "inputList": "X,Y,Z", "sort": 99, "type": 0}
        resp = base_api.post(f"/productAttribute/update/{TestProductAttribute.attr_id}", json=body)
        base_api.assert_code_ok(resp, "更新属性")
        print(f"  已更新: {self.attr_name}_改")

    def test_r_delete_attr(self, base_api):
        resp = base_api.post("/productAttribute/delete", params={"ids": [TestProductAttribute.attr_id]})
        base_api.assert_code_ok(resp, "删除属性")
        print(f"  属性 ID={TestProductAttribute.attr_id} 已删除")


class TestProductManagement:
    """商品管理 — 查询 + 批量状态操作（需要数据库已有商品）"""

    def test_list_products(self, base_api):
        """查询商品列表"""
        resp = base_api.get("/product/list", params={"pageSize": 5})
        result = base_api.assert_code_ok(resp, "查商品列表")
        products = result["data"]["list"]
        print(f"  商品数量: {len(products)}")
        # 如果有商品，存第一个供后续批量操作使用
        if products:
            TestProductManagement.first_id = products[0]["id"]
            print(f"  首个商品 ID={products[0]['id']}: {products[0]['name']}")

    def test_simple_list(self, base_api):
        """模糊搜索商品"""
        resp = base_api.get("/product/simpleList", params={"keyword": "小米"})
        base_api.assert_code_ok(resp, "模糊查商品")
        print(f"  搜索'小米': {len(resp.json()['data'])} 条")

    def test_toggle_recommend(self, base_api):
        """批量切换推荐状态"""
        # 用已知 ID 或跳过
        product_ids = getattr(TestProductManagement, 'first_id', None)
        if not product_ids:
            pytest.skip("无商品数据，跳过批量操作")
            return
        resp = base_api.post("/product/update/recommendStatus",
                             params={"ids": [product_ids], "recommendStatus": 1})
        base_api.assert_code_ok(resp, "设为推荐")
        print(f"  已推荐商品 ID={product_ids}")

    def test_toggle_new_status(self, base_api):
        """批量切换新品状态"""
        product_ids = getattr(TestProductManagement, 'first_id', None)
        if not product_ids:
            pytest.skip("无商品数据，跳过批量操作")
            return
        resp = base_api.post("/product/update/newStatus",
                             params={"ids": [product_ids], "newStatus": 1})
        base_api.assert_code_ok(resp, "设为新品")
        print(f"  已设新品 ID={product_ids}")


class TestContentQueries:
    """内容模块 — 纯查询"""

    def test_subject_list(self, base_api):
        resp = base_api.get("/subject/listAll")
        base_api.assert_code_ok(resp, "查专题")
        print(f"  专题: {len(resp.json()['data'])} 个")

    def test_prefrence_area(self, base_api):
        resp = base_api.get("/prefrenceArea/listAll")
        base_api.assert_code_ok(resp, "查优选")
        print(f"  优选: {len(resp.json()['data'])} 个")
