# 心守AI (Heart Guardian AI) - 心理健康支持平台

一个基于 AI 的心理健康支持平台，专为政治创伤幸存者（难民、异议人士等）设计，提供情绪支持对话、健康追踪、心理评估、医患协作等功能。

## 特性亮点

- **AI 情绪支持**: 24/7 流式 AI 对话，基于 Anthropic Claude，提供即时情绪支持
- **多层级风险检测**: 自动检测对话中的 CRITICAL/HIGH/MEDIUM/LOW 风险内容，支持多语言（中/英/波斯语/土耳其语/西班牙语）
- **政治创伤特异检测**: 针对流亡绝望、幸存者内疚、迫害恐惧等特殊创伤模式
- **健康追踪**: 每日打卡记录心情评分、睡眠质量、服药情况
- **专业评估**: 支持 PHQ-9、GAD-7、PSS、ISI、PCL-5 等标准化心理评估量表
- **医患协作**: 安全的数据共享、实时消息、预约管理、报告生成
- **数据导出**: GDPR 友好的多格式数据导出（JSON/CSV/PDF）
- **多语言支持**: 支持 12+ 种语言
- **PWA 离线支持**: 渐进式 Web 应用，支持离线使用
- **响应式设计**: 移动端优先，支持暗色/亮色主题切换

## 技术栈

### 后端
- **框架**: FastAPI 0.109 (Python 异步 Web 框架)
- **ORM**: SQLAlchemy 2.0 (异步支持)
- **数据库**: PostgreSQL 15 (生产) / SQLite (开发)
- **缓存**: Redis 7
- **对象存储**: MinIO (S3 兼容)
- **AI**: Anthropic Claude API
- **认证**: JWT (python-jose) + bcrypt
- **PDF 生成**: ReportLab
- **邮件**: aiosmtplib + Jinja2 模板

### 前端
- **框架**: Next.js 14.1 (App Router)
- **语言**: TypeScript 5.3
- **样式**: Tailwind CSS 3.4 + CSS 变量主题
- **UI 组件**: Radix UI + Headless UI
- **动画**: Framer Motion
- **状态管理**: Zustand
- **国际化**: next-intl
- **PWA**: @ducanh2912/next-pwa

## 项目结构

```
docAI/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # API 路由模块
│   │   │   ├── auth.py         # 认证 (登录/注册/密码管理)
│   │   │   ├── chat.py         # AI 对话 (流式SSE)
│   │   │   ├── clinical.py     # 临床数据 (打卡/评估/医患连接)
│   │   │   ├── messaging.py    # 消息系统 (医患通信)
│   │   │   ├── appointments.py # 预约管理
│   │   │   ├── reports.py      # 报告生成
│   │   │   └── data_export.py  # 数据导出
│   │   ├── models/             # SQLAlchemy ORM 模型
│   │   │   ├── user.py         # 用户 (PATIENT/DOCTOR/ADMIN)
│   │   │   ├── patient.py      # 患者档案
│   │   │   ├── doctor.py       # 医生档案
│   │   │   ├── conversation.py # AI 对话记录
│   │   │   ├── checkin.py      # 每日打卡
│   │   │   ├── assessment.py   # 心理评估
│   │   │   ├── risk_event.py   # 风险事件
│   │   │   ├── appointment.py  # 预约
│   │   │   └── messaging.py    # 直接消息
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── ai/             # AI 服务
│   │   │   │   ├── risk_detector.py          # 多语言风险检测
│   │   │   │   ├── hybrid_chat_engine.py     # 混合聊天引擎
│   │   │   │   ├── doctor_chat_engine.py     # 医生 AI 助手
│   │   │   │   ├── patient_context_aggregator.py # 患者上下文
│   │   │   │   └── prompts.py                # AI 提示词
│   │   │   ├── reports/        # 报告生成服务
│   │   │   ├── email/          # 邮件服务
│   │   │   └── storage.py      # S3/MinIO 存储
│   │   ├── utils/              # 工具函数
│   │   │   ├── security.py     # JWT/密码
│   │   │   ├── deps.py         # 依赖注入
│   │   │   └── rate_limit.py   # 速率限制
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   └── main.py             # 应用入口
│   ├── alembic/                # 数据库迁移 (10个版本)
│   └── requirements.txt
├── frontend/                   # Next.js 前端
│   └── src/
│       ├── app/
│       │   ├── (patient)/      # 患者端路由组
│       │   │   ├── dashboard/  # 首页仪表板
│       │   │   ├── chat/       # AI 情绪支持
│       │   │   ├── health/     # 健康中心
│       │   │   ├── checkin/    # 每日打卡
│       │   │   ├── assessment/ # 心理评估
│       │   │   ├── conversations/ # 对话历史
│       │   │   ├── messages/   # 医生消息
│       │   │   ├── my-appointments/ # 预约
│       │   │   ├── profile/    # 个人档案
│       │   │   └── data-export/ # 数据导出
│       │   ├── (doctor)/       # 医生端路由组
│       │   │   ├── patients/   # 患者列表
│       │   │   ├── patients/[id]/ # 患者详情
│       │   │   ├── risk-queue/ # 风险队列
│       │   │   ├── appointments/ # 预约管理
│       │   │   ├── doctor-messages/ # 消息中心
│       │   │   ├── pending-requests/ # 连接请求
│       │   │   └── my-profile/ # 医生档案
│       │   ├── login/          # 登录页
│       │   └── change-password/ # 密码修改
│       ├── lib/
│       │   ├── api.ts          # API 客户端 (完整类型定义)
│       │   ├── auth.ts         # 认证管理
│       │   ├── i18n.ts         # 国际化
│       │   └── theme.ts        # 主题管理
│       └── components/
│           ├── ui/             # 基础 UI 组件库
│           ├── chat/           # 聊天组件
│           ├── doctor/         # 医生专用组件
│           ├── messaging/      # 消息组件
│           └── landing/        # 登录页组件
├── docker-compose.yml          # 容器编排
└── README.md
```

## 快速开始

### 1. 启动基础服务

```bash
docker-compose up -d
```

这会启动:
- **PostgreSQL 15** (端口 5432) - 主数据库
- **Redis 7** (端口 6379) - 缓存和会话
- **MinIO** (端口 9000, 控制台 9001) - 对象存储

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (复制 .env.example 或创建 .env)
# 必需: ANTHROPIC_API_KEY

# 运行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端服务将在 http://localhost:8000 运行
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 运行

## 功能模块

### 患者端功能

| 功能 | 描述 |
|------|------|
| **AI 情绪支持** | 流式 AI 对话，实时风险检测，个性化回应 |
| **健康中心** | 每日打卡（心情0-10、睡眠、服药）、心理评估入口 |
| **心理评估** | PHQ-9(抑郁)、GAD-7(焦虑)、PSS(压力)、ISI(失眠)、PCL-5(创伤) |
| **对话历史** | 查看历史 AI 对话记录 |
| **医患连接** | 接受/拒绝医生连接请求 |
| **消息系统** | 与医生安全通信，支持文本/图片/文件 |
| **预约管理** | 查看预约、添加备注、取消预约 |
| **数据导出** | 导出个人数据（JSON/CSV/PDF） |
| **个人档案** | 管理个人信息、医疗信息、心理背景 |

### 医生端功能

| 功能 | 描述 |
|------|------|
| **患者列表** | 患者概览，支持按风险/心情/名字排序 |
| **风险队列** | 处理 AI 检测的风险事件，添加审查备注 |
| **患者详情** | 查看打卡趋势、评估记录、AI 对话 |
| **AI 辅助分析** | 与 AI 讨论患者，自动聚合临床上下文 |
| **报告生成** | 生成预访视摘要 PDF |
| **消息系统** | 与患者安全通信 |
| **预约管理** | 创建/确认/完成预约，日历视图 |
| **连接请求** | 发送连接请求给新患者 |
| **创建患者** | 为患者创建账户（首次登录需改密码） |

## API 接口

### 认证 `/api/v1/auth`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录，返回 JWT |
| GET | `/me` | 获取当前用户信息 |
| POST | `/change-password` | 修改密码 |
| POST | `/request-reset` | 请求密码重置邮件 |
| POST | `/reset-password` | 确认密码重置 |

### 对话 `/api/v1/chat`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 发送消息（单次响应） |
| POST | `/stream` | 流式对话（SSE） |
| GET | `/conversations` | 获取对话列表 |
| GET | `/conversations/{id}` | 获取对话详情 |
| POST | `/conversations/{id}/end` | 结束对话 |

### 临床数据 `/api/v1/clinical`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/checkin` | 提交每日打卡 |
| GET | `/checkin/today` | 获取今日打卡 |
| GET | `/checkins` | 获取打卡历史 |
| POST | `/assessment` | 提交心理评估 |
| GET | `/assessments` | 获取评估列表 |

### 医生功能 `/api/v1/clinical/doctor`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/patients` | 患者列表 |
| GET | `/risk-queue` | 风险队列 |
| POST | `/risk-events/{id}/review` | 审查风险事件 |
| GET | `/patients/{id}/profile` | 患者详情 |
| GET | `/patients/{id}/checkins` | 患者打卡 |
| GET | `/patients/{id}/assessments` | 患者评估 |
| POST | `/patients/{id}/ai-chat` | AI 辅助分析 |
| GET | `/patients/{id}/ai-conversations` | AI 对话列表 |
| POST | `/connection-requests` | 发送连接请求 |

### 消息系统 `/api/v1/messaging`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/threads` | 获取消息线程 |
| GET | `/threads/{id}` | 线程详情和消息 |
| POST | `/threads/{id}/messages` | 发送消息 |
| POST | `/upload` | 上传附件 |
| GET | `/unread` | 未读消息计数 |

### 预约 `/api/v1/appointments`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/doctor` | 创建预约（医生） |
| GET | `/doctor/calendar` | 医生日历视图 |
| GET | `/doctor/list` | 医生预约列表 |
| PUT | `/doctor/{id}` | 更新预约 |
| POST | `/doctor/{id}/complete` | 完成预约 |
| GET | `/patient/list` | 患者预约列表 |
| GET | `/patient/upcoming` | 即将到来的预约 |

### 报告 `/api/v1/reports`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/pre-visit-summary/{id}/pdf` | 生成预访视 PDF |
| GET | `/{id}` | 获取报告 |
| GET | `/` | 报告列表 |

### 数据导出 `/api/v1/data-export`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/request` | 请求数据导出 |
| GET | `/requests` | 导出请求列表 |
| GET | `/requests/{id}` | 导出状态 |
| GET | `/download/{token}` | 下载导出文件 |

## 数据库架构

### 主要数据表

| 表名 | 描述 |
|------|------|
| `users` | 用户账户 (PATIENT/DOCTOR/ADMIN) |
| `patients` | 患者档案 (医疗信息、心理背景) |
| `doctors` | 医生档案 (执业信息、专业) |
| `conversations` | AI 对话记录 |
| `daily_checkins` | 每日打卡 (心情、睡眠、服药) |
| `assessments` | 心理评估 (PHQ9/GAD7/PSS/ISI/PCL5) |
| `risk_events` | 风险事件 (级别、类型、AI置信度) |
| `doctor_patient_threads` | 医患消息线程 |
| `direct_messages` | 直接消息 |
| `appointments` | 预约记录 |
| `connection_requests` | 医患连接请求 |
| `pre_visit_summaries` | 预访视摘要 |
| `generated_reports` | 生成的报告 |
| `data_exports` | 数据导出请求 |

## 环境变量

### 后端 (.env)

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/xinshoucai
# 本地开发可用 SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./xinshoucai.db

# Redis
REDIS_URL=redis://localhost:6379/0

# S3 / MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=xinshoucai

# 认证
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 应用
DEBUG=true
APP_NAME=心守AI
API_V1_PREFIX=/api/v1

# 邮件 (可选)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@xinshoucai.com
FRONTEND_URL=http://localhost:3000
EMAIL_ENABLED=false
```

### 前端 (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 风险检测系统

### 风险级别
| 级别 | 描述 | 处理 |
|------|------|------|
| CRITICAL | 立即危险（今晚自杀、已准备好） | 紧急通知医生 |
| HIGH | 严重关切（想要死亡、生活无意义） | 优先通知 |
| MEDIUM | 需要关注（厌世、持续低落） | 常规通知 |
| LOW | 轻微关切 | 记录观察 |

### 风险类型
- **SUICIDAL**: 自杀风险
- **SELF_HARM**: 自伤行为
- **VIOLENCE**: 暴力倾向
- **PERSECUTION_FEAR**: 迫害恐惧（政治创伤特异）
- **OTHER**: 其他风险

### 多语言支持
风险检测支持：中文、英文、波斯语、土耳其语、西班牙语

## 前端页面结构

### 患者端 `/app/(patient)/`
```
/dashboard        - 首页仪表板
/chat             - AI 情绪支持对话
/health           - 健康中心
/checkin          - 每日打卡
/assessment       - 心理评估
/conversations    - 对话历史
/messages         - 与医生消息
/my-appointments  - 预约管理
/profile          - 个人档案
/data-export      - 数据导出
```

### 医生端 `/app/(doctor)/`
```
/patients         - 患者列表
/patients/[id]    - 患者详情
/risk-queue       - 风险队列
/appointments     - 预约管理
/doctor-messages  - 消息中心
/pending-requests - 连接请求
/my-profile       - 医生档案
```

## 部署

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 生产环境注意事项

1. **安全配置**
   - 更换 `SECRET_KEY` 为强随机字符串
   - 更换数据库密码
   - 配置 HTTPS
   - 设置正确的 CORS 域名

2. **数据库**
   - 使用 PostgreSQL（不是 SQLite）
   - 配置数据库备份
   - 运行迁移: `alembic upgrade head`

3. **AI 功能**
   - 配置 `ANTHROPIC_API_KEY`
   - 考虑 API 调用速率限制

4. **邮件服务**
   - 配置 SMTP 设置
   - 设置 `EMAIL_ENABLED=true`

5. **对象存储**
   - 生产环境建议使用 AWS S3 或独立 MinIO 集群

## 注意事项

1. **首次登录**: 医生创建的患者账户首次登录需修改密码
2. **新用户引导**: 患者首次登录显示 5 步引导流程
3. **风险检测**: AI 会自动检测对话风险并通知医生
4. **数据隐私**: 支持 GDPR 友好的数据导出功能
5. **离线支持**: PWA 技术支持基本离线功能

## 许可证

MIT License
