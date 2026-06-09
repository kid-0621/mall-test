"""读取 YAML 测试数据文件的工具"""
import yaml
import os


def read_yaml(file_name):
    """
    读取 data/ 目录下的 YAML 文件
    file_name: 文件名，如 "login_data.yaml"
    返回: 解析后的 Python 字典/列表
    """
    # __file__ 是当前文件路径，往上两层到项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, "data", file_name)

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
