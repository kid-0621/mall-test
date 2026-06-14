# ============================================
# mall 商城后端 — Docker 镜像
# ============================================
# 构建步骤（在 mall 后端项目根目录执行）：
#   1. mvn clean package -DskipTests
#   2. docker build -t mall-backend:latest .
#   3. docker tag mall-backend:latest your-dockerhub/mall-backend:latest
#   4. docker push your-dockerhub/mall-backend:latest
# ============================================

# FROM openjdk:8-jdk-alpine
FROM eclipse-temurin:8-jre-alpine


# 设置时区（可选）
RUN apk add --no-cache tzdata curl \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apk del tzdata

COPY target/mall-admin-*.jar /app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app.jar"]
