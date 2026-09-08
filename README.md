# Life Assistant

一个面向个人使用的多 Agent 生活助手 MVP。它把自然语言对话、待办管理、邮件提醒、出行路线、实时天气和长期偏好记忆放在同一个工作流中：普通问题按聊天模型回答，只有识别到对应意图时才调用路线、天气或待办 Agent。

## 能做什么

- **自然聊天**：没有触发任务时，直接由通义千问结合当前会话上下文回答。
- **待办与提醒**：用“明天 8 点提醒我带伞”“十分钟后提醒我吃药”等表达创建待办；待办变更先生成确认卡片，确认后写入数据库。
- **出行规划**：识别出发地和目的地后调用高德地图；路线卡片只在路线请求触发时显示。
- **天气与出行建议**：调用和风天气；“适合出门吗/需要带什么”会把天气结果交给对话模型生成建议，而不是只展示原始天气字段。
- **位置辅助**：前端可授权浏览器定位，未授权时仍可手动输入城市或地址。
- **长期记忆**：对话结束后异步提炼稳定偏好；对话开始只读取已启用的记忆，用户可在“我的习惯”中编辑、禁用或删除。
- **会话历史**：每轮用户消息、助手回复以及路线/天气结构化卡片都会保存；左侧栏支持新建、切换和删除会话。
- **可追踪提醒**：163 邮箱发送结果、重试次数和错误信息写入 `notification_logs`；成功发送后会清理已过期待办，失败任务保留以便重试。

## 技术栈与协作流程

- 后端：Python 3.11+、FastAPI、SQLAlchemy、Alembic、LangGraph、Celery、Redis、MySQL/SQLite。
- 模型与外部服务：通义千问兼容 OpenAI API、高德 Web 服务 API、和风天气 API、网易 163 SMTP。
- 前端：React、TypeScript、Vite、SSE。

核心 LangGraph 流程如下：

```text
请求 → 加载会话/记忆上下文 → Supervisor 意图路由
   ├─ Todo Agent     → 待确认动作 → 用户确认 → MySQL 待办
   ├─ Travel Agent   → 高德路线
   ├─ Weather Agent  → 和风天气
   ├─ Memory Agent   → 异步提炼/管理偏好
   └─ General Chat   → 普通问答
路线与天气可并行执行 → 汇总 Agent → 生成回复/结构化卡片 → 保存会话与审计

Celery Beat/Worker（或本机开发扫描器）→ 到期提醒 → 163 SMTP → 投递日志/重试/过期清理
```

## 项目结构

```text
life-assistant/
├─ backend/
│  ├─ app/
│  │  ├─ agents/       # Supervisor、专业 Agent、LangGraph 状态与工具
│  │  ├─ api/v1/       # chat、conversation、todo、action、memory、dashboard
│  │  ├─ models/       # todo、memory、conversation、action、notification
│  │  ├─ providers/    # Qwen、高德、和风、SMTP 客户端
│  │  ├─ repositories/ # 数据访问
│  │  ├─ services/     # 业务规则与幂等执行
│  │  └─ tasks/        # reminder、memory、cleanup 任务
│  └─ tests/           # unit、integration、e2e 目录
├─ frontend/
│  └─ src/             # 对话、会话侧栏、待办、路线/天气卡片、偏好页面
├─ infra/mysql/init.sql
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 环境要求

### 本机开发

- Python 3.11 或更高版本（推荐 3.12/3.13）
- Node.js 18 或更高版本、npm
- Redis（提醒本机扫描器也建议运行 Redis）
- MySQL 8（可选；默认 `.env.example` 使用 SQLite，便于快速体验）

### Docker

安装 Docker Desktop 后，可直接启动 API、前端、MySQL、Redis、Celery Worker 和 Beat。

## 配置 API Key 与 163 邮箱

复制配置模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`：

| 变量 | 用途 | 获取方式 |
| --- | --- | --- |
| `QWEN_API_KEY` | 对话、意图识别、出行建议 | 阿里云百炼/DashScope 控制台创建 |
| `AMAP_API_KEY` | 地点解析与驾车路线 | 高德开放平台创建 Web 服务 Key |
| `QWEATHER_API_KEY` | 实时天气 | 和风天气控制台创建 API Key |
| `QWEATHER_API_HOST` | 和风项目专属 Host | 和风控制台“项目设置”复制，形如 `xxx.re.qweatherapi.com`；不要填公共示例域名 |
| `SMTP_USERNAME` | 163 发件账号 | 你的 `xxx@163.com` 邮箱 |
| `SMTP_PASSWORD` | SMTP 登录凭据 | 163 邮箱“设置 → POP3/SMTP/IMAP”开启 SMTP 后生成的**授权码**，不是网页登录密码 |
| `SMTP_FROM` | 发件人 | 通常与 `SMTP_USERNAME` 相同 |
| `REMINDER_EMAIL_TO` | 收件人 | 接收提醒的邮箱，可先填自己的 163 邮箱 |

163 邮箱默认配置为 `smtp.163.com:465`（SSL）。授权码不要提交到 Git；`.env` 已被 `.gitignore` 忽略。

如果暂时没有某个第三方 Key，服务仍可启动，对应 Agent 会返回可解释的降级信息。路线/天气卡片只有在相关请求触发时才显示。

## 本机启动

在项目根目录执行：

```powershell
# 1. 安装并启动后端
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload
```

另开一个终端启动前端：

```powershell
cd frontend
npm install
npm run dev
```

访问 <http://localhost:5173>，后端 API 文档在 <http://localhost:8000/docs>。

开发环境 `REMINDER_LOCAL_RUNNER=true` 时，API 进程每 30 秒扫描一次到期提醒；这样不需要先启动 Celery，也便于本机验证。生产或 Docker 模式应设为 `false`，由 Beat/Worker 执行：

```powershell
celery -A app.core.celery_app.celery_app worker --loglevel=INFO
celery -A app.core.celery_app.celery_app beat --loglevel=INFO
```

## Docker 启动

```powershell
Copy-Item .env.example .env
# 编辑 .env 填入 Key 和 163 授权码
docker compose up --build
```

服务地址：前端 <http://localhost:5173>，API <http://localhost:8000>，MySQL `localhost:3306`，Redis `localhost:6379`。首次启动会创建 `life_assistant` 数据库；数据保存在 Docker volume `mysql_data`。

## 常用接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/chat/stream` | SSE 对话流，返回文本、路线/天气/建议卡片和待确认动作 |
| `GET/POST` | `/api/v1/conversations` | 查询或创建会话 |
| `GET/DELETE` | `/api/v1/conversations/{id}` | 查看会话消息或删除会话 |
| `GET/POST` | `/api/v1/todos` | 查询或手动创建待办 |
| `PATCH` | `/api/v1/todos/{id}` | 编辑待办 |
| `POST` | `/api/v1/todos/{id}/complete` | 完成待办 |
| `POST` | `/api/v1/actions/{id}/confirm` | 确认并幂等执行动作 |
| `POST` | `/api/v1/actions/{id}/reject` | 拒绝待确认动作 |
| `GET/PATCH/DELETE` | `/api/v1/memories/{id}` | 管理偏好记忆 |
| `GET` | `/api/v1/dashboard/today` | 今日待办、待确认动作与提醒概览 |

## 对话示例

```text
明天早上 8 点提醒我带伞
从公司到首都机场怎么走？顺便看看目的地天气
现在适合出门跑步吗？需要带什么？
我平时更喜欢地铁，今后规划路线优先考虑地铁
```

创建/编辑待办时，聊天窗口会先显示确认卡片；点击确认后才真正写库并进入提醒队列。普通问答不会显示地图或天气组件。

## 测试与构建

```powershell
# 后端
cd backend
pytest -q

# 前端
cd ..\frontend
npm run build
```

单元测试覆盖意图路由、上下文记忆、中文时间解析、提醒过期清理；集成测试使用 SQLite/Provider Mock 验证 API。接入真实服务前，建议先用“十秒后提醒我……”验证扫描、邮件和日志链路。

## 安全与排障

- 不要把 `.env`、邮箱授权码或任何 API Key 提交到仓库；如果曾经公开过，请立即在对应平台轮换。
- 和风天气返回 403 通常是 Key、项目权限或 `QWEATHER_API_HOST` 不匹配；返回 400 `No Such Location` 通常是地点文本未转换成城市/经纬度，建议输入城市名或坐标。
- 前端加载失败时先确认后端 `http://localhost:8000/health` 可访问，再检查 Vite 终端和浏览器 Network 面板。
- 提醒不发送时确认 `REMINDER_TIMEZONE=Asia/Shanghai`、SMTP 授权码、Redis/Celery 状态，以及任务是否已经被标记完成；成功发送的过期待办会自动清理，失败会保留并重试。

## 当前边界

第一版按单用户、本机 Docker、`Asia/Shanghai` 时区设计，暂不接入第三方日历、飞书或微信。项目保留 GraphRAG 的扩展位置，但当前长期记忆采用 MySQL 持久化和关键词检索；后续可替换为向量库/知识图谱检索而不改变 Agent 接口。
