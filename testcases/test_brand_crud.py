import requests
import pytest
import time


class TestBrandCRUD:
    """品牌管理接口自动化测试：新增 → 查询 → 更新 → 删除"""

    brand_id = None  # 类变量，存储创建后拿到的品牌ID，供后续用例使用

    # ==================== 用例1：创建品牌 ====================
    def test_01_create_brand(self, login_token):
        """
        流程：
        1. 发送 POST 创建品牌
        2. 通过分页查询关键字反查，拿到创建出来的品牌 ID
        """
        url = "http://localhost:8080/brand/create"
        headers = {"Authorization": login_token}

        # 用时间戳后缀保证品牌名不重复
        suffix = str(int(time.time()))[-6:]
        body = {
            "name": f"AutoTest品牌_{suffix}",
            "logo": "https://example.com/logo.png",
            "firstLetter": "A",
            "sort": 0,
            "factoryStatus": 1,
            "showStatus": 1,
            "brandStory": "自动化测试临时品牌，用例结束后删除"
        }

        response = requests.post(url=url, headers=headers, json=body)
        result = response.json()

        assert response.status_code == 200
        assert result["code"] == 200
        print(f"✅ 创建品牌: {body['name']}")

        # 反查获取 ID
        search_url = "http://localhost:8080/brand/list"
        params = {"keyword": body["name"], "pageNum": 1, "pageSize": 5}
        search_resp = requests.get(url=search_url, headers=headers, params=params)
        search_result = search_resp.json()

        brand_list = search_result["data"]["list"]
        assert len(brand_list) > 0, f"未查到刚创建的品牌: {body['name']}"

        TestBrandCRUD.brand_id = brand_list[0]["id"]
        print(f"   获取到 ID: {TestBrandCRUD.brand_id}")

    # ==================== 用例2：根据ID查询 ====================
    def test_02_get_brand_by_id(self, login_token):
        """
        用创建用例得到的 ID，通过 GET /brand/{id} 查询品牌详情
        """
        assert TestBrandCRUD.brand_id is not None, "请先运行 test_01_create_brand"

        url = f"http://localhost:8080/brand/{TestBrandCRUD.brand_id}"
        headers = {"Authorization": login_token}

        response = requests.get(url=url, headers=headers)
        result = response.json()

        assert response.status_code == 200
        assert result["code"] == 200

        brand = result["data"]
        assert brand["id"] == TestBrandCRUD.brand_id
        assert "AutoTest" in brand["name"]

        print(f"✅ 查询品牌: {brand['name']} | logo={brand['logo']} | sort={brand['sort']}")

    # ==================== 用例3：更新品牌 ====================
    def test_03_update_brand(self, login_token):
        """
        更新品牌的名称和排序，然后立即查询验证更新是否生效
        """
        assert TestBrandCRUD.brand_id is not None

        url = f"http://localhost:8080/brand/update/{TestBrandCRUD.brand_id}"
        headers = {"Authorization": login_token}
        body = {
            "name": "AutoTest品牌_已更新",
            "logo": "https://example.com/logo_updated.png",
            "firstLetter": "A",
            "sort": 99,
            "factoryStatus": 1,
            "showStatus": 1
        }

        response = requests.post(url=url, headers=headers, json=body)
        result = response.json()

        assert response.status_code == 200
        assert result["code"] == 200
        print(f"✅ 更新品牌: {body['name']} | sort={body['sort']}")

        # 验证更新是否写入数据库
        verify_url = f"http://localhost:8080/brand/{TestBrandCRUD.brand_id}"
        verify_resp = requests.get(url=verify_url, headers=headers)
        verify_result = verify_resp.json()

        assert verify_result["data"]["name"] == body["name"]
        assert verify_result["data"]["sort"] == 99
        print(f"   验证通过: name={verify_result['data']['name']}")

    # ==================== 用例4：删除品牌 ====================
    def test_04_delete_brand(self, login_token):
        """删除品牌，然后验证已不存在"""
        assert TestBrandCRUD.brand_id is not None

        url = f"http://localhost:8080/brand/delete/{TestBrandCRUD.brand_id}"
        headers = {"Authorization": login_token}

        response = requests.get(url=url, headers=headers)
        result = response.json()

        assert response.status_code == 200
        assert result["code"] == 200
        print(f"✅ 删除品牌 ID={TestBrandCRUD.brand_id}")

        # 验证已删除
        verify_url = f"http://localhost:8080/brand/{TestBrandCRUD.brand_id}"
        verify_resp = requests.get(url=verify_url, headers=headers)
        verify_result = verify_resp.json()
        assert verify_result["data"] is None
        print("   验证通过: 品牌已不存在")
