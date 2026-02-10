# SaiLi AI

基于前后端分离的竞赛信息聚合与推荐平台。

## 技术栈
- 前端：Vue 3 + Vite + Vue Router
- 后端：Python + FastAPI + SQLAlchemy
- 数据库：SQLite（默认）
- 认证：JWT
- 契约：OpenAPI（`contracts/openapi.yaml`）

## 目录结构
- `backend/` 后端服务
- `frontend/` 前端项目
- `contracts/` OpenAPI 契约

## 本地启动

### 1) 启动后端
```bash
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) 启动前端
```bash
cd frontend
npm install
npm run dev
```

## 默认管理员
- 用户名：`admin`
- 密码：`admin123`

## 关键配置
- `DATABASE_URL`
- `JWT_SECRET`
- `API_PROVIDER_CONFIG_PATH`（默认 `backend/config/api_providers.yaml`）
- `STABLE_SOURCE_PATH`
- `FALLBACK_SOURCE_PATH`
- `ENABLE_INGEST_SCHEDULER`
- `INGEST_INTERVAL_SECONDS`
- `INGEST_FAILURE_THRESHOLD`

## 管理接口（示例）
- `POST /api/v1/admin/ingest/source` 触发入库
- `GET /api/v1/admin/ingest/sources` 查看数据源状态
- `GET /api/v1/admin/config/api-providers` 读取 YAML 配置
- `PUT /api/v1/admin/config/api-providers` 更新 YAML 配置

## 测试
```bash
cd backend
pytest
```
