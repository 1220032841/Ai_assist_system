# AI 教学系统阿里云公网部署指南

本指南按 Ubuntu 24.04 云服务器编写，目标是把当前项目部署到阿里云 ECS，并让你在答辩现场直接通过公网 IP 演示系统。

## 1. 部署前确认

在阿里云控制台确认以下信息：

- 已有一台 Ubuntu 24.04 ECS，且能通过公网 IP SSH 登录
- 安全组已放行 22 端口，供你远程连接
- 安全组已放行 80 端口，供浏览器访问系统
- 如果后续要配 HTTPS，再额外放行 443 端口

如果你打算只用公网 IP 演示，80 端口就够了。

## 2. 连接服务器

在你自己的电脑上执行：

```bash
ssh root@你的公网IP
```

如果你不是 root 用户，请把下面命令中的 sudo 保留。

## 3. 安装 Docker 与 Compose

首次部署时，在服务器上执行：

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
docker --version
docker compose version
```

## 4. 上传项目到服务器

你有两种常用方式。

方式 A：服务器直接拉 Git 仓库。

```bash
git clone 你的仓库地址 fyp
cd fyp
```

方式 B：从本地把项目目录上传到服务器。

```bash
scp -r 你的本地项目目录 root@你的公网IP:/root/fyp
ssh root@你的公网IP
cd /root/fyp
```

只要服务器上最后能进入项目根目录即可。

## 5. 配置线上环境变量

在服务器项目根目录执行：

```bash
cp .env.online.example .env.online
nano .env.online
```

至少修改这些字段：

- SECRET_KEY：改成一段足够长的随机字符串
- POSTGRES_PASSWORD：改成数据库强密码
- LLM_API_KEY：填你答辩时实际使用的大模型密钥

通常建议这样填：

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=你自己的数据库密码
POSTGRES_DB=app

SECRET_KEY=一段很长的随机字符串
ACCESS_TOKEN_EXPIRE_MINUTES=30

BACKEND_CORS_ORIGINS=

LLM_PROVIDER=deepseek
LLM_API_KEY=你的API密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_CHAT_MODEL=deepseek-chat
LLM_EMBEDDING_MODEL=
OPENAI_API_KEY=
```

说明：

- 当前部署是前端 Nginx 与后端同域反代，所以 BACKEND_CORS_ORIGINS 可以留空
- 如果 LLM_API_KEY 为空，系统仍可启动，但 AI 反馈能力会失败，不适合答辩演示

## 6. 执行部署

在服务器项目根目录执行：

```bash
chmod +x deploy_online.sh
./deploy_online.sh
```

脚本会自动完成：

- 构建并启动 db、backend、frontend 三个容器
- 执行 Alembic 数据库迁移

如果部署成功，你可以在浏览器访问：

```text
http://你的公网IP/
```

## 7. 初始化答辩演示数据

为了让你现场直接演示教师端和学生端，部署完成后继续执行：

```bash
chmod +x seed_demo_data.sh seed_assignment.sh
./seed_demo_data.sh
```

这个脚本会自动：

- 创建 1 个管理员账号
- 创建 1 个教师账号
- 创建 5 个学生账号
- 创建 1 个 C++ 示例作业

默认演示账号：

- 管理员：admin@example.com / admin123
- 教师：teacher1@teacher.com / teacher123
- 学生：student1@student.com 到 student5@student.com / student123

## 8. 验证公网访问

你可以在服务器上执行：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online ps
docker compose -f docker-compose.online.yml --env-file .env.online logs --tail=100
curl http://127.0.0.1/
curl http://127.0.0.1/api/v1/openapi.json
docker compose -f docker-compose.online.yml --env-file .env.online exec -T backend curl -f http://127.0.0.1:8000/health
```

然后再用你自己的电脑、手机热点下的其他设备，直接访问：

```text
http://你的公网IP/
```

这样能验证系统确实具备互联网可访问性。

## 9. 答辩当天建议流程

建议你在答辩前 30 分钟执行一次：

```bash
cd /root/fyp
docker compose -f docker-compose.online.yml --env-file .env.online ps
docker compose -f docker-compose.online.yml --env-file .env.online logs --tail=50
```

演示时可以按这个顺序：

1. 打开公网 IP，展示系统首页可从互联网访问。
2. 用教师账号登录，展示作业和结果看板。
3. 用学生账号登录并提交代码。
4. 返回教师端刷新，展示评分与反馈结果。

## 10. 常用维护命令

查看容器状态：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online ps
```

查看日志：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online logs -f
```

重启服务：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online restart
```

停止服务：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online down
```

重新构建上线：

```bash
docker compose -f docker-compose.online.yml --env-file .env.online up -d --build
docker compose -f docker-compose.online.yml --env-file .env.online exec -T backend alembic upgrade head
```

## 11. 当前线上结构

- frontend：Nginx 提供 Vue 静态页面，并将 /api 反代到 backend
- backend：FastAPI + Uvicorn，负责登录、作业、提交、评分与 AI 反馈
- db：PostgreSQL，存储用户、作业、提交记录与反馈结果

当前结构对外只暴露 80 端口，数据库和后端服务不会直接暴露到公网。

## 12. HTTPS 与域名

如果你答辩后还要长期展示，建议继续做：

1. 绑定域名到这台 ECS
2. 放行 443 端口
3. 用 Nginx + Certbot 或云产品证书启用 HTTPS

但如果只是答辩现场演示，先用公网 IP + 80 端口即可。
