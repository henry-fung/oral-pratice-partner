# Oral Practice Partner - AI 口语练习助手

一个基于 AI 的个性化口语练习应用，通过 LLM 生成真实场景对话，帮助用户提升外语口语能力。

## 🌟 功能特点

- **个性化角色设定**：提供 9 种预设角色（雅思考生、留学生、外贸商务、程序员等），支持自定义角色
- **智能场景生成**：根据用户角色和目标语言，LLM 自动生成最实用的口语场景
- **情景化句子练习**：每个场景生成 2-5 轮实用对话，支持单词查询、中文翻译
- **多语言支持**：英语、日语、法语、西班牙语、德语、韩语
- **单词本功能**：收藏生词，随时复习
- **学习记录追踪**：记录每次练习，帮助持续进步

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI + SQLAlchemy
- **数据库**: SQLite（开发）/ PostgreSQL（生产，如 Supabase）
- **LLM 集成**: OpenAI SDK，支持多种 LLM 提供商
  - OpenAI / Azure OpenAI
  - Google Gemini
  - Custom API（如 Moonshot/Kimi）

### 前端
- **架构**: 原生 JavaScript SPA（单页应用）
- **样式**: Tailwind CSS（移动端优先）
- **路由**: 自研轻量级 Router 模块
- **状态管理**: localStorage 持久化

### 部署
- **平台**: Railway（静态资源 + FastAPI 后端）
- **环境变量**: 通过 `.env` 文件管理配置

## 📦 快速开始

### 环境要求

- Python 3.9+
- Node.js（可选，仅用于 Tailwind 构建）
- LLM API Key（OpenAI / Azure / Gemini / Kimi）

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/henry-fung/oral-pratice-partner.git
cd oral-pratice-partner
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# 例如：OPENAI_API_KEY=sk-your-api-key
```

4. **启动后端服务**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

5. **访问应用**
- 后端 API：http://localhost:8000
- API 文档（Swagger UI）：http://localhost:8000/docs
- 前端页面：http://localhost:8000（静态资源由 FastAPI 提供）

## 📚 API 端点

### 认证
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |

### 用户配置
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/users/profile` | GET | 获取个人配置 |
| `/api/users/profile` | POST | 创建/更新配置 |

### 场景管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/scenarios/generate` | POST | 生成 N 个口语场景 |
| `/api/scenarios` | GET | 获取场景列表 |
| `/api/scenarios/{id}` | GET | 获取场景详情 |
| `/api/scenarios/{id}/select` | POST | 选择场景进行练习 |
| `/api/scenarios/{id}` | DELETE | 删除场景 |

### 句子练习
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/sentences/generate` | POST | 生成场景下的句子 |
| `/api/sentences/{id}` | GET | 获取句子详情 |
| `/api/sentences/{id}/complete` | POST | 标记句子完成 |

### 单词本
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/vocabulary/lookup` | POST | 查询单词释义 |
| `/api/vocabulary` | GET | 获取单词本列表 |
| `/api/vocabulary` | POST | 添加单词到单词本 |
| `/api/vocabulary/{id}` | DELETE | 删除单词 |

## ⚙️ 配置说明

### LLM 配置

支持多种 LLM 提供商，通过 `LLM_PROVIDER` 环境变量切换：

```env
# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o

# 使用 Azure OpenAI
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_DEPLOYMENT_NAME=your-deployment

# 使用 Google Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-1.5-flash

# 使用 Kimi（Moonshot）
LLM_PROVIDER=custom
KIMI_API_KEY=your-api-key
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k
```

### 数据库配置

```env
# 本地开发（SQLite）
DATABASE_URL=sqlite:///./oral_practice.db

# 生产环境（PostgreSQL / Supabase）
DATABASE_URL=postgresql://user:password@host:port/database
```

### JWT 配置

```env
SECRET_KEY=your-secret-key-for-jwt-token-generation
```

## 📱 使用流程

1. **注册/登录** → 创建账户
2. **设置角色和语言** → 选择你的身份（如"程序员"）和目标语言（如"英语"）
3. **生成场景** → LLM 生成 5 个最实用的口语场景
4. **选择场景** → 选择一个场景开始练习
5. **句子练习** → 逐句练习，支持查看翻译、查询单词
6. **添加单词本** → 收藏生词，随时复习

## 🗂️ 项目结构

```
oral-pratice-partner/
├── backend/
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库连接
│   ├── models/                    # SQLAlchemy 模型
│   │   ├── user.py               # 用户表
│   │   ├── profile.py            # 用户配置表
│   │   ├── scenario.py           # 场景表
│   │   ├── sentence.py           # 句子表
│   │   ├── vocabulary.py         # 单词本表
│   │   └── learning_record.py    # 学习记录表
│   ├── schemas/                   # Pydantic 验证
│   ├── api/                       # API 路由
│   │   ├── auth.py               # 认证端点
│   │   ├── users.py              # 用户端点
│   │   ├── scenarios.py          # 场景端点
│   │   ├── sentences.py          # 句子端点
│   │   └── vocabulary.py         # 单词本端点
│   ├── services/                  # 业务逻辑
│   │   ├── llm_provider.py       # LLM 提供商抽象层
│   │   └── llm_service.py        # LLM 业务封装
│   └── utils/
│       ├── prompts.py            # LLM Prompt 模板
│       └── security.py           # JWT 和密码哈希
├── frontend/
│   ├── index.html                # SPA 入口
│   ├── js/
│   │   ├── app.js                # 应用初始化
│   │   ├── api.js                # API 调用封装
│   │   ├── router.js             # 路由模块
│   │   ├── storage.js            # localStorage 封装
│   │   └── pages/                # 页面组件
│   │       ├── auth.js           # 登录/注册页
│   │       ├── profile.js        # 角色语言选择页
│   │       ├── scenarios.js      # 场景列表页
│   │       ├── practice.js       # 核心练习页
│   │       └── vocabulary.js     # 单词本页
│   └── css/                      # 样式（Tailwind CDN）
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git 忽略文件
├── requirements.txt              # Python 依赖
├── railway.json                  # Railway 部署配置
└── README.md                     # 项目说明
```

## 🚀 部署到 Railway

1. **连接 GitHub 仓库** 到 Railway
2. **设置环境变量**：
   - `LLM_PROVIDER`
   - `OPENAI_API_KEY`（或其他 LLM 配置）
   - `DATABASE_URL`（建议使用 Supabase PostgreSQL）
   - `SECRET_KEY`
3. **部署**：Railway 自动构建并部署

## 📝 开发计划

### P0 核心功能（已完成）
- [x] 用户注册/登录
- [x] 角色和语言选择
- [x] 场景生成和选择
- [x] 句子练习
- [x] 单词查询

### P1 优化功能
- [ ] 移动端 UI 优化（深色模式）
- [ ] 语音输入支持（Web Speech API）
- [ ] 学习统计数据图表

### P2 扩展功能
- [ ] 多用户协作练习
- [ ] AI 语音评测
- [ ] 每日打卡提醒

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 联系。
