# SaiLi AI

基于前后端分离的高校竞赛信息聚合与协作平台，包含竞赛检索、个性化推荐、收藏订阅、提醒、组队任务、论坛、简历导出和后台管理能力。

## 技术栈

- 前端：`Vue 3` + `Vite` + `Vue Router`
- 后端：`FastAPI` + `SQLAlchemy` + `Pydantic`
- 数据库：`SQLite`（默认）
- 鉴权：`JWT`
- 测试：`pytest`
- 契约：`contracts/openapi.yaml`

## 已实现功能（与当前代码一致）

- 用户注册/登录、`/auth/me` 当前用户信息
- 竞赛列表筛选（关键词/标签/等级）与详情、报名、提交
- 国家认可/学校认可分级展示
- 收藏与订阅（按标签、按竞赛）
- 个性化推荐（专业、兴趣标签、订阅标签 + 可调权重）
- 截止提醒设置（默认注册后创建“提前 3 天”提醒）
- 竞赛简历（获奖记录 + PDF 导出）
- 组队协作（技能标签、成员管理、任务打卡、逾期审计、成员信用）
- 校园论坛（按学校隔离，管理员可置顶/删除）
- 管理后台（竞赛审核发布、报名导出 CSV、数据源导入、配置中心）
- 数据源导入与健康指标（主源/兜底源、去重、失败降级）

## 项目结构

```text
Saili_AI/
├── backend/                 # FastAPI 服务
│   ├── app/
│   │   ├── core/            # 配置、鉴权、DB、调度、导入、模块加载
│   │   └── modules/         # 业务模块（auth/competitions/...）
│   ├── config/              # 运行时 provider 配置 YAML
│   ├── data/                # SQLite 与导入源数据文件
│   └── tests/               # 后端测试
├── frontend/                # Vue3 前端
└── contracts/               # OpenAPI 契约
```

## 本地启动

### 1) 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

后端默认地址：`http://localhost:8000`

- Swagger UI：`http://localhost:8000/docs`
- Health：`http://localhost:8000/api/v1/health`

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://localhost:5173`

## 默认账号

首次启动会自动种子化平台管理员：

- 用户名：`admin`
- 密码：`admin123`

建议上线前通过环境变量覆盖：`DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` / `DEFAULT_ADMIN_EMAIL`。

## 配置说明

### 环境变量（后端）

- `DATABASE_URL`（默认：`sqlite:///backend/data/app.db`）
- `JWT_SECRET`（默认：`change-me`，生产务必修改）
- `ACCESS_TOKEN_EXPIRE_MINUTES`（默认 `120`）
- `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` / `DEFAULT_ADMIN_EMAIL`
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM`
- `ENABLE_REMINDER_SCHEDULER`（默认 `true`）
- `ENABLE_INGEST_SCHEDULER`（默认 `false`）
- `INGEST_INTERVAL_SECONDS`（默认 `900`）
- `STABLE_SOURCE_PATH`（默认 `backend/data/competition_source.json`）
- `FALLBACK_SOURCE_PATH`（默认 `backend/data/competition_fallback.json`）
- `INGEST_FAILURE_THRESHOLD`（默认 `3`）
- `API_PROVIDER_CONFIG_PATH`（默认 `backend/config/api_providers.yaml`）
- `CORS_ORIGINS` / `CORS_ORIGIN_REGEX`

### 运行时 Provider 配置

系统启动会自动确保 `backend/config/api_providers.yaml` 存在，并支持通过后台接口在线更新：

- `GET /api/v1/admin/config/api-providers`
- `PUT /api/v1/admin/config/api-providers`

包含三类配置：

- `ai_extraction`：导入时是否启用 AI 抽取（含 `base_url/model/api_key/timeout_seconds`）
- `ingestion`：主源/兜底源路径、失败阈值、调度间隔
- `auth`：JWT 过期时长

> 安全提示：不要把真实 API Key 提交到 Git 仓库。

## 数据导入机制（Ingestion）

- 默认数据源：
  - `stable_primary`（主源）
  - `fallback_file`（兜底源）
- 导入入口：`POST /api/v1/admin/ingest/source`
- 指标查询：`GET /api/v1/admin/ingest/sources`
- 关键行为：
  - 按 `source_item_id`（或 `external_id`）识别条目
  - 基于 payload checksum 幂等跳过重复数据
  - 跨源去重：优先依据 `source link`，其次 `title + signup_end`
  - 主源失败可自动切换兜底源并记录 `fallback_used/degraded_from`
  - 缺标题或关键字段不足会标记 `needs_review`

## 权限模型

- `platform_admin`：平台管理员（可跨校管理、系统配置）
- `school_admin`：学校管理员（可审核/发布本校竞赛）
- `student_admin`：学生管理员（可维护本校且自己上传的竞赛）
- `student`：普通用户

## 主要 API 一览

所有接口前缀均为：`/api/v1`

- `auth`：`/auth/register`、`/auth/login`、`/auth/me`
- `competitions`：列表/详情、`/school/current`、报名 `/enroll`、提交 `/submit`
- `favorites`：`/favorites`、`/subscriptions`
- `recommendations`：`/recommendations`
- `profile`：`GET/PUT /profile`
- `reminders`：`GET/POST /reminders/settings`
- `resume`：`/resume/records`、`/resume/pdf`
- `teams`：技能标签、建队、成员增删、信用、任务创建/打卡/逾期审计
- `forum`：帖子与回复、置顶、删除
- `admin`：竞赛审核发布、报名导出 CSV、导入控制、配置中心、推荐权重、手动提醒

## 前端路由模块

- 公开：`/`、`/competitions`、`/competitions/national`、`/competitions/:id`、`/login`、`/register`
- 登录后：`/favorites`、`/subscriptions`、`/recommendations`、`/reminders/settings`、`/profile`、`/resume`、`/teams`、`/forum`
- 管理：`/admin`（学校管理及以上）、`/admin/managers`（平台管理员）、`/admin/api-config`（平台管理员）

## 测试

```bash
cd backend
pytest
```

当前测试覆盖包含：鉴权、竞赛流程、导入与降级、配置持久化、资料模块、平台核心流程、健康检查、模块加载等。

## 备注

- 后端采用模块注册 + 依赖拓扑排序加载（`ModuleDefinition` / `ModuleRegistry`）。
- SQLite 启动时会执行兼容性字段补齐（轻量迁移逻辑）。
- 前端可通过 `VITE_API_BASE_URL` 覆盖默认 API 地址（默认会推断为 `http://<当前主机>:8000/api/v1`）。
