# ============================================
# mall 接口测试 — Docker 运行器（可选）
# ============================================
# 把测试代码也打包成 Docker，一键跑测试：
#   docker build -t mall-test-runner .
#   docker run --network host mall-test-runner
# ============================================

FROM python:3.9-slim

WORKDIR /app

# 安装 Java（Allure 依赖）
RUN apt-get update && apt-get install -y default-jre-headless wget curl && rm -rf /var/lib/apt/lists/*

# 安装 Allure CLI
RUN wget -q https://github.com/allure-framework/allure2/releases/download/2.32.0/allure-2.32.0.tgz \
    && tar -zxvf allure-2.32.0.tgz -C /opt/ \
    && ln -s /opt/allure-2.32.0/bin/allure /usr/local/bin/allure \
    && rm allure-2.32.0.tgz

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制测试代码
COPY . .

# 默认命令：运行测试 + 生成报告
CMD ["pytest", "testcases/", "-v", "--alluredir=allure-results"]
