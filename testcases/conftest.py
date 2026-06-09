import os
import pytest
import requests
from common.base_api import BaseAPI

# ============================================
# 环境自适应配置
# ============================================

# BASE_URL：CI 里通过环境变量传入，本地默认 localhost:8080
BASE_URL = os.getenv("MALL_BASE_URL", "http://localhost:8080")

# 是否在 CI 环境（GitHub Actions / Jenkins / Docker）
IS_CI = bool(
    os.getenv("CI")                        # 通用 CI 标识
    or os.getenv("GITHUB_ACTIONS")         # GitHub Actions
    or os.getenv("JENKINS_HOME")           # Jenkins
)


@pytest.fixture(scope="session")
def login_token():
    """统一登录获取 token（所有测试类共享）"""
    url = f"{BASE_URL}/admin/login"
    data = {"username": "admin", "password": "macro123"}
    response = requests.post(url=url, json=data, timeout=10)
    result = response.json()
    token_head = result["data"]["tokenHead"]
    token = result["data"]["token"]
    return f"{token_head}{token}"


@pytest.fixture(scope="session")
def base_api(login_token):
    """
    返回封装好的 BaseAPI 对象
    每个测试类直接 def test_xxx(self, base_api): 即可
    """
    return BaseAPI(base_url=BASE_URL, token=login_token)


# ============================================
# Allure 报告自动生成（仅在非 CI 环境）
# ============================================

def _find_allure_cmd():
    """自动查找 allure 可执行文件路径"""
    # 优先从 PATH 中找
    import shutil
    path = shutil.which("allure")
    if path:
        return path
    # Windows 常见路径
    if os.name == "nt":
        candidates = [
            r"C:\ProgramData\WorkBuddy\chromium-env\135wvqi\.workbuddy\binaries\node\versions\22.22.2\allure.cmd",
            r"C:\Program Files\allure\bin\allure.bat",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
    return "allure"  # 最终兜底


def pytest_sessionfinish(session):
    """测试全部结束后自动生成 Allure 报告并打开浏览器（仅非 CI 环境）"""
    import sys
    import time
    import subprocess

    results_dir = os.path.join(session.config.rootdir, "results")
    report_dir = os.path.join(session.config.rootdir, "report")

    if not os.path.exists(results_dir):
        return

    # ── 1. 生成 Allure 报告 ──
    allure_path = _find_allure_cmd()
    use_shell = (os.name == "nt")  # Windows 需要 shell=True

    result = subprocess.run(
        [allure_path, "generate", results_dir, "-o", report_dir, "--clean"],
        shell=use_shell,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"\n⚠️  Allure 报告生成失败:\n{result.stderr[-500:]}")
        return

    print(f"\n✅ Allure 报告已生成: {report_dir}")

    # ── 2. CI 环境：只生成报告，不打开浏览器 ──
    if IS_CI:
        print("   (CI 环境，跳过浏览器自动打开)")
        return

    # ── 3. 本地环境：启动 HTTP 服务 + 打开浏览器 ──
    import webbrowser
    port = 8888

    if os.name == "nt":
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=report_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        server_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port)],
            cwd=report_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{port}")
    print(f"   浏览器已打开: http://localhost:{port}")
