@echo off
REM mall-test 自动化测试 + Allure 报告一键生成

echo ========================================
echo  第1步: 运行测试 & 收集结果
echo ========================================
python -m pytest testcases/ --alluredir=results -v -s

echo.
echo ========================================
echo  第2步: 生成 Allure HTML 报告
echo ========================================
allure generate results -o report --clean

echo.
echo ========================================
echo  第3步: 打开报告
echo ========================================
allure open report
