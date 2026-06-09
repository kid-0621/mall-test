"""数据驱动测试 —— 从 YAML 读取测试数据"""
import requests
import pytest
import sys
import os

# 把项目根目录加到 sys.path，让 common 模块可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.yaml_reader import read_yaml

# 读取 YAML 测试数据
test_data = read_yaml("login_data.yaml")["login_test_data"]


class TestLoginDDT:
    """数据驱动登录测试"""

    @pytest.mark.parametrize("case", test_data,
        ids=[item["case_name"] for item in test_data])
    def test_login_data_driven(self, case):
        """
        case: YAML 中的每一组数据
        ids: 给每组数据起个中文名，运行时更好看
        """
        url = "http://localhost:8080/admin/login"
        data = {"username": case["username"], "password": case["password"]}

        response = requests.post(url=url, json=data)
        result = response.json()

        if case["expect_success"]:
            assert result["code"] == 200
            assert "token" in result["data"]
            print(f"  ✅ PASS: {case['desc']}")
        else:
            assert result["code"] != 200
            print(f"  ❌ PASS: {case['desc']} → {result['message']}")
