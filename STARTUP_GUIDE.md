# AI 教学系统 - 启动指南

本文档将指导您如何启动整个 AI 辅助教学系统（前后端）。

## 📋 前置要求

在启动之前，请确保您的电脑上安装了以下软件：

1.  **Docker Desktop**: 用于运行后端服务和数据库。[下载地址](https://www.docker.com/products/docker-desktop/)
    *   *安装后请务必启动 Docker Desktop。*
2.  **Node.js**: 用于运行前端项目。[下载地址](https://nodejs.org/) (建议版本 v18 或更高)

---

## 🚀 极简启动 (推荐)

我们为您准备了一键启动脚本。

1.  **确保 Docker Desktop 正在运行**。
2.  双击项目根目录下的 **`start_all.bat`** 文件。

脚本会自动：
- 检查 Docker 状态
- 在新窗口中启动后端服务 (Docker Compose)
- 等待后端初始化
- 在新窗口中启动前端服务

启动成功后，浏览器访问：**http://localhost:5173**

---

## 🛠️ 分步启动 (手动)

如果一键脚本无法使用，您可以尝试分步启动。

### 1. 启动后端

打开终端 (PowerShell 或 CMD)，进入项目根目录：

```powershell
# 运行部署脚本
powershell -ExecutionPolicy Bypass -File deploy.ps1
```

或者直接使用 Docker Compose (需要进入 backend 目录):

```bash
cd backend
docker-compose up -d --build
```

*后端启动成功后，API 文档地址: http://localhost:8000/docs*

### 2. 启动前端

打开一个新的终端窗口，进入项目根目录：

```bash
# 运行前端启动脚本
run_frontend.bat
```

或者手动运行命令：

```bash
cd frontend
npm install  # 第一次运行时需要
npm run dev
```

*前端启动成功后，访问地址: http://localhost:5173*

---

## 🔑 测试账号

系统预置了以下测试账号：

- **用户名**: `student1`
- **密码**: `student123`

---

## ❓ 常见问题

**Q: 启动脚本提示 "Docker is NOT running"**
A: 请打开 Docker Desktop 应用程序，等待左下角状态变为绿色 (Engine running)，然后再运行脚本。

**Q: 前端显示 "Network Error" 或无法登录**
A: 请检查后端窗口是否有报错。确保后端服务已完全启动（通常需要几十秒初始化数据库）。您可以尝试刷新前端页面。

**Q: 端口被占用**
A: 
- 后端占用端口: `8000` (API), `5432` (PostgreSQL), `6379` (Redis)
- 前端占用端口: `5173`
- 请确保这些端口没有被其他程序占用。

---

## 🌐 公网访问部署

如果你需要让学生和老师在家中登录使用，请按公网部署文档操作：

- 参考 `ONLINE_DEPLOYMENT.md`
- 使用 `deploy_online.ps1` + `docker-compose.online.yml` 在服务器一键启动
