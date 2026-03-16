# 口语练习助手应用 - 详细实现计划

## 项目概述

一个移动端优先的口语练习助手应用，帮助用户通过角色扮演和场景模拟来练习外语口语。

---

## 1. 项目结构设计

```
OralPraticePartner2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 应用入口
│   │   ├── config.py               # 配置管理（数据库、API 密钥等）
│   │   ├── database.py             # 数据库连接和会话管理
│   │   ├── models/                 # SQLAlchemy 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # 用户表
│   │   │   ├── user_profile.py     # 用户配置表
│   │   │   ├── scenario.py         # 场景表
│   │   │   ├── sentence.py         # 句子表
│   │   │   ├── vocabulary.py       # 单词本表
│   │   │   └── learning_record.py  # 学习记录表
│   │   ├── schemas/                # Pydantic 数据验证模式
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── scenario.py
│   │   │   ├── sentence.py
│   │   │   └── vocabulary.py
│   │   ├── api/                    # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # 认证相关端点
│   │   │   ├── users.py            # 用户配置端点
│   │   │   ├── scenarios.py        # 场景相关端点
│   │   │   ├── sentences.py        # 句子相关端点
│   │   │   └── vocabulary.py       # 单词本端点
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # 认证服务（JWT）
│   │   │   ├── llm_service.py      # LLM 调用服务
│   │   │   ├── scenario_service.py # 场景生成服务
│   │   │   ├── sentence_service.py # 句子生成服务
│   │   │   └── vocabulary_service.py # 单词本服务
│   │   └── utils/                  # 工具函数
│   │       ├── __init__.py
│   │       ├── security.py         # 密码哈希、JWT
│   │       └── prompts.py          # LLM prompts 模板
│   ├── tests/                      # 测试文件
│   ├── requirements.txt            # Python 依赖
│   └── .env.example                # 环境变量示例
├── frontend/
│   ├── index.html                  # 主页面（移动端适配）
│   ├── css/
│   │   ├── main.css                # 主样式文件
│   │   └── components.css          # 组件样式
│   ├── js/
│   │   ├── app.js                  # 主应用逻辑
│   │   ├── auth.js                 # 认证相关
│   │   ├── scenario.js             # 场景选择逻辑
│   │   ├── practice.js             # 练习页面逻辑
│   │   └── vocabulary.js           # 单词本逻辑
│   └── assets/                     # 静态资源
├── design/
│   ├── uiux.pen                    # Pencil 设计文件
│   └── IMPLEMENTATION_PLAN.md      # 本计划文档
├── railway.json                    # Railway 部署配置
├── Dockerfile                      # Docker 容器配置
└── README.md
```

---

## 2. 数据库设计

### 2.1 用户表 (users)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PostgreSQL (Supabase) 版本
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.2 用户配置表 (user_profiles)

```sql
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,           -- 留学生、商务人士、旅游者等
    target_language VARCHAR(50) NOT NULL, -- 英语、日语、法语等
    proficiency_level VARCHAR(20) DEFAULT 'intermediate', -- beginner/intermediate/advanced
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2.3 场景表 (scenarios)

```sql
CREATE TABLE scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    target_language VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,         -- 场景标题
    description TEXT,                     -- 场景描述
    context TEXT,                         -- 场景上下文
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_scenarios_user ON scenarios(user_id);
```

### 2.4 句子表 (sentences)

```sql
CREATE TABLE sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    sentence_order INTEGER NOT NULL,      -- 句子顺序
    chinese TEXT NOT NULL,                -- 中文提示
    target_text TEXT NOT NULL,            -- 目标语言句子
    target_language VARCHAR(50) NOT NULL,
    pronunciation_guide TEXT,             -- 发音指南（可选）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX idx_sentences_scenario ON sentences(scenario_id);
```

### 2.5 单词本表 (vocabulary)

```sql
CREATE TABLE vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    word VARCHAR(100) NOT NULL,
    translation TEXT NOT NULL,
    target_language VARCHAR(50) NOT NULL,
    example_sentence TEXT,
    pronunciation TEXT,
    difficulty_level VARCHAR(20) DEFAULT 'unknown',
    times_reviewed INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, word, target_language)
);

CREATE INDEX idx_vocabulary_user ON vocabulary(user_id);
```

### 2.6 学习记录表 (learning_records)

```sql
CREATE TABLE learning_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sentence_id INTEGER,
    scenario_id INTEGER,
    session_id VARCHAR(100),
    user_recording_url TEXT,              -- 用户录音 URL（如有）
    accuracy_score INTEGER,               -- 准确度评分（0-100）
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (sentence_id) REFERENCES sentences(id) ON DELETE SET NULL,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
);

CREATE INDEX idx_records_user ON learning_records(user_id);
CREATE INDEX idx_records_session ON learning_records(session_id);
```

---

## 3. API 端点设计

### 3.1 认证相关

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/auth/register` | 用户注册 | `{email, password}` | `{user_id, token}` |
| POST | `/api/auth/login` | 用户登录 | `{email, password}` | `{user_id, token, profile}` |
| POST | `/api/auth/logout` | 用户登出 | - | `{success: true}` |
| GET | `/api/auth/me` | 获取当前用户 | - | `{user, profile}` |

### 3.2 用户配置相关

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/users/profile` | 获取用户配置 | - | `{role, target_language, proficiency}` |
| POST | `/api/users/profile` | 设置用户配置 | `{role, target_language, proficiency?}` | `{success, profile}` |
| PUT | `/api/users/profile` | 更新用户配置 | `{role?, target_language?, proficiency?}` | `{success, profile}` |

### 3.3 场景生成与选择

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/scenarios/generate` | 生成 N 个场景 | `{count?}` (默认 5) | `{scenarios: [{id, title, description}]}` |
| GET | `/api/scenarios` | 获取用户场景列表 | - | `{scenarios}` |
| POST | `/api/scenarios/:id/select` | 选择场景 | - | `{success, scenario}` |
| DELETE | `/api/scenarios/:id` | 删除场景 | - | `{success: true}` |

### 3.4 句子生成与展示

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/sentences/generate` | 生成下一句 | `{scenario_id}` | `{sentence}` |
| GET | `/api/sentences/next` | 获取下一句（当前场景） | - | `{sentence}` |
| POST | `/api/sentences/:id/complete` | 标记句子完成 | `{accuracy_score?}` | `{success, next_available}` |

### 3.5 单词查询与单词本管理

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/vocabulary/lookup` | 查询单词 | `{word, language}` | `{translation, pronunciation, examples}` |
| POST | `/api/vocabulary` | 添加单词到单词本 | `{word, translation, language, example?}` | `{success, vocab_id}` |
| GET | `/api/vocabulary` | 获取单词本 | `?page=1&limit=20` | `{vocabularies, total, page}` |
| PUT | `/api/vocabulary/:id` | 更新单词 | `{translation?, example?, difficulty?}` | `{success, vocabulary}` |
| DELETE | `/api/vocabulary/:id` | 删除单词 | - | `{success: true}` |
| POST | `/api/vocabulary/:id/review` | 标记复习 | `{correct: boolean}` | `{success, next_review}` |

---

## 4. 前端页面设计

### 4.1 页面结构

```
前端页面路由（纯前端，无框架）：
- #/login       → 登录页
- #/register    → 注册页
- #/setup       → 角色和语言选择页
- #/scenarios   → 场景选择页
- #/practice    → 练习页面（核心）
- #/vocabulary  → 单词本页面
```

### 4.2 各页面详细设计

#### 4.2.1 登录/注册页 (`#/login`, `#/register`)

**HTML 结构：**
```html
<div class="auth-container">
  <div class="auth-header">
    <h1>口语练习助手</h1>
    <p>开始你的口语练习之旅</p>
  </div>

  <form id="auth-form" class="auth-form">
    <div class="form-group">
      <label for="email">邮箱</label>
      <input type="email" id="email" required>
    </div>

    <div class="form-group">
      <label for="password">密码</label>
      <input type="password" id="password" required>
    </div>

    <button type="submit" class="btn-primary">登录</button>
  </form>

  <p class="auth-switch">
    还没有账号？<a href="#/register">立即注册</a>
  </p>
</div>
```

**JavaScript 逻辑：**
- 表单提交时调用 `/api/auth/login` 或 `/api/auth/register`
- 存储 JWT token 到 localStorage
- 成功后跳转到 `#/setup` 或主页

#### 4.2.2 角色和语言选择页 (`#/setup`)

**HTML 结构：**
```html
<div class="setup-container">
  <h2>选择你的角色</h2>
  <div class="role-grid">
    <div class="role-card" data-role="student">
      <div class="role-icon">🎓</div>
      <h3>留学生</h3>
      <p>适应海外学习生活</p>
    </div>
    <div class="role-card" data-role="business">
      <div class="role-icon">💼</div>
      <h3>商务人士</h3>
      <p>商务沟通和谈判</p>
    </div>
    <div class="role-card" data-role="traveler">
      <div class="role-icon">✈️</div>
      <h3>旅游者</h3>
      <p>旅行中的日常交流</p>
    </div>
    <div class="role-card" data-role="daily">
      <div class="role-icon">🏠</div>
      <h3>日常生活</h3>
      <p>日常社交和生活场景</p>
    </div>
  </div>

  <h2>选择目标语言</h2>
  <div class="language-list">
    <button class="lang-btn" data-lang="en">英语</button>
    <button class="lang-btn" data-lang="ja">日语</button>
    <button class="lang-btn" data-lang="fr">法语</button>
    <button class="lang-btn" data-lang="es">西班牙语</button>
    <button class="lang-btn" data-lang="de">德语</button>
  </div>

  <button id="save-setup" class="btn-primary btn-large">开始练习</button>
</div>
```

#### 4.2.3 场景选择页 (`#/scenarios`)

**HTML 结构：**
```html
<div class="scenarios-container">
  <div class="scenarios-header">
    <h2>选择练习场景</h2>
    <button id="refresh-scenarios" class="btn-icon">🔄</button>
  </div>

  <div id="loading" class="loading">
    <div class="spinner"></div>
    <p>正在生成场景...</p>
  </div>

  <div id="scenarios-list" class="scenarios-list">
    <!-- 场景卡片由 JS 动态生成 -->
  </div>

  <template id="scenario-template">
    <div class="scenario-card" data-id="{{id}}">
      <h3>{{title}}</h3>
      <p>{{description}}</p>
      <button class="btn-select">开始练习</button>
    </div>
  </template>
</div>
```

#### 4.2.4 练习页面 (`#/practice`) - 核心页面

**HTML 结构：**
```html
<div class="practice-container">
  <!-- 顶部进度条 -->
  <div class="practice-header">
    <div class="progress-bar">
      <div class="progress-fill" style="width: 30%"></div>
    </div>
    <span class="sentence-count">3/10</span>
  </div>

  <!-- 中文提示区域 -->
  <div class="chinese-prompt-card">
    <div class="prompt-label">请表达：</div>
    <div id="chinese-text" class="chinese-text">
      你想问服务员菜单在哪里
    </div>
  </div>

  <!-- 练习区域 -->
  <div class="practice-area">
    <div class="recording-status" id="recording-status">
      <span class="status-text">点击下方按钮开始练习</span>
    </div>

    <div class="practice-controls">
      <button id="record-btn" class="btn-record">
        <span class="record-icon">🎤</span>
        <span>按住说话</span>
      </button>
    </div>
  </div>

  <!-- 答案区域（初始隐藏） -->
  <div id="answer-section" class="answer-section hidden">
    <div class="answer-card">
      <div class="answer-label">参考表达：</div>
      <div id="target-text" class="target-text">
        <!-- 单词可点击 -->
        <span class="word" data-word="Excuse">Excuse</span>
        <span class="word" data-word="me">me</span>,
        <span class="word" data-word="where">where</span>
        <span class="word" data-word="is">is</span>
        <span class="word" data-word="the">the</span>
        <span class="word" data-word="menu">menu</span>?
      </div>
      <div class="word-lookup-hint">点击单词查看详情</div>
    </div>
  </div>

  <!-- 底部操作按钮 -->
  <div class="practice-actions">
    <button id="show-answer-btn" class="btn-primary btn-large">
      显示答案
    </button>
    <button id="next-sentence-btn" class="btn-secondary btn-large hidden">
      下一句 →
    </button>
    <button id="next-scenario-btn" class="btn-outline hidden">
      换个场景
    </button>
  </div>

  <!-- 单词详情弹窗 -->
  <div id="word-modal" class="modal hidden">
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="modal-word">Word</h3>
        <button class="modal-close">×</button>
      </div>
      <div class="modal-body">
        <p class="translation" id="modal-translation">翻译</p>
        <p class="pronunciation" id="modal-pronunciation">/prəˌnʌnsiˈeɪʃən/</p>
        <p class="example" id="modal-example">Example sentence</p>
      </div>
      <div class="modal-actions">
        <button class="btn-add-vocab">添加到单词本</button>
        <button class="btn-play-audio">🔊 播放发音</button>
      </div>
    </div>
  </div>
</div>
```

**JavaScript 逻辑：**
```javascript
// practice.js 主要逻辑
class PracticeSession {
  constructor() {
    this.currentSentence = null;
    this.isRecording = false;
    this.hasCompleted = false;
    this.init();
  }

  async init() {
    await this.loadNextSentence();
    this.bindEvents();
  }

  async loadNextSentence() {
    const response = await fetch('/api/sentences/next');
    this.currentSentence = await response.json();
    this.render();
  }

  render() {
    document.getElementById('chinese-text').textContent =
      this.currentSentence.chinese;
    document.getElementById('target-text').innerHTML =
      this.renderTargetText(this.currentSentence.target_text);
  }

  renderTargetText(text) {
    // 将句子拆分为单词，每个单词可点击
    return text.split(/\s+/).map(word =>
      `<span class="word" data-word="${word}">${word}</span>`
    ).join(' ');
  }

  bindEvents() {
    // 显示答案按钮
    document.getElementById('show-answer-btn').onclick = () => {
      document.getElementById('answer-section').classList.remove('hidden');
      document.getElementById('next-sentence-btn').classList.remove('hidden');
    };

    // 单词点击查询
    document.querySelectorAll('.word').forEach(word => {
      word.onclick = () => this.lookupWord(word.dataset.word);
    });

    // 下一句按钮
    document.getElementById('next-sentence-btn').onclick = () => {
      this.completeSentence();
      this.loadNextSentence();
    };
  }

  async lookupWord(word) {
    const response = await fetch('/api/vocabulary/lookup', {
      method: 'POST',
      body: JSON.stringify({ word, language: currentLanguage })
    });
    const data = await response.json();
    this.showWordModal(word, data);
  }

  showWordModal(word, data) {
    document.getElementById('modal-word').textContent = word;
    document.getElementById('modal-translation').textContent = data.translation;
    document.getElementById('word-modal').classList.remove('hidden');
  }
}
```

#### 4.2.5 单词本页面 (`#/vocabulary`)

**HTML 结构：**
```html
<div class="vocabulary-container">
  <div class="vocab-header">
    <h2>我的单词本</h2>
    <div class="vocab-stats">
      <span>已学：<strong id="total-count">0</strong></span>
    </div>
  </div>

  <div class="vocab-filters">
    <input type="search" id="search-vocab" placeholder="搜索单词...">
    <select id="filter-difficulty">
      <option value="">全部难度</option>
      <option value="easy">简单</option>
      <option value="medium">中等</option>
      <option value="hard">困难</option>
    </select>
  </div>

  <div id="vocab-list" class="vocab-list">
    <!-- 单词卡片由 JS 生成 -->
  </div>

  <template id="vocab-template">
    <div class="vocab-card" data-id="{{id}}">
      <div class="vocab-main">
        <h3 class="vocab-word">{{word}}</h3>
        <button class="btn-play">🔊</button>
      </div>
      <p class="vocab-translation">{{translation}}</p>
      <div class="vocab-meta">
        <span class="vocab-lang">{{language}}</span>
        <span class="vocab-review">复习：<strong>{{times_reviewed}}</strong>次</span>
      </div>
    </div>
  </template>
</div>
```

---

## 5. UI/UX 设计建议

### 5.1 移动端优先布局

**视口设置：**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
```

**CSS 框架选择：**

推荐使用 **Pico CSS** (轻量级，语义化 HTML) 或 **Tailwind CSS** (高度可定制)

**Pico CSS 方案（推荐，简单）：**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
```

**Tailwind CSS 方案（推荐，灵活）：**
```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
tailwind.config = {
  theme: {
    extend: {
      colors: {
        primary: '#6366F1',
        secondary: '#32D583',
        accent: '#E85A4F',
        dark: '#0B0B0E',
        surface: '#16161A'
      }
    }
  }
}
</script>
```

### 5.2 配色方案（基于深色主题）

```css
:root {
  /* 背景色 */
  --bg-primary: #0B0B0E;
  --bg-surface: #16161A;
  --bg-elevated: #1A1A1E;

  /* 文字色 */
  --text-primary: #FAFAF9;
  --text-secondary: #6B6B70;
  --text-muted: #8E8E93;

  /* 强调色 */
  --accent-green: #32D583;
  --accent-indigo: #6366F1;
  --accent-coral: #E85A4F;
  --accent-amber: #FFB547;

  /* 边框 */
  --border-subtle: #2A2A2E;
  --border-strong: #3A3A40;

  /* 间距 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-pill: 9999px;
}
```

### 5.3 组件风格

**按钮组件：**
```css
.btn-primary {
  background: var(--accent-indigo);
  color: white;
  padding: 14px 24px;
  border-radius: var(--radius-pill);
  border: none;
  font-weight: 600;
  font-size: 16px;
}

.btn-secondary {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
}

.btn-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}
```

**卡片组件：**
```css
.card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}
```

---

## 6. 部署配置

### 6.1 Railway 部署配置

**railway.json：**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 6.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backend/ ./backend/

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite+aiosqlite:///./oral_practice.db

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.3 环境变量管理

**.env.example：**
```bash
# 应用配置
APP_NAME=OralPracticePartner
DEBUG=false
SECRET_KEY=your-secret-key-here

# 数据库配置 (开发用 SQLite)
DATABASE_URL=sqlite+aiosqlite:///./oral_practice.db

# 部署时切换到 Supabase (PostgreSQL)
# DATABASE_URL=postgresql://user:password@host:5432/dbname

# LLM 配置
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选：其他 LLM 提供商
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com
GEMINI_API_KEY=xxx

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# 跨域配置（前端地址）
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

### 6.4 SQLite 到 Supabase 切换方案

**1. 开发阶段 (SQLite)：**
```python
# config.py
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./oral_practice.db")
```

**2. 部署阶段 (Supabase PostgreSQL)：**
```bash
# 在 Railway 环境变量中设置
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
```

**3. 数据库迁移脚本：**
```python
# migrate.py
import asyncio
from sqlalchemy import create_engine, MetaData, schema

# SQLite 导出
sqlite_engine = create_engine("sqlite:///oral_practice.db")
metadata = MetaData()
metadata.reflect(bind=sqlite_engine)

# Supabase 导入
supabase_engine = create_engine(os.getenv("DATABASE_URL"))

# 创建所有表
metadata.create_all(supabase_engine)
```

---

## 7. 与现有代码集成

### 7.1 复用 llm_provider.py

假设 `llm_provider.py` 已有以下接口：

```python
# llm_provider.py 使用示例
from llm_provider import LLMProvider

provider = LLMProvider(
    provider="openai",  # 或 "azure", "gemini", "custom"
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

async def generate_scenarios(role: str, language: str, count: int = 5) -> list:
    prompt = f"""你是一位专业的语言学习场景设计师。
请为以下角色生成{count}个实用的口语练习场景：

角色：{role}
目标语言：{language}

每个场景需要：
1. 一个简短的标题（10 字以内）
2. 一段场景描述（50 字以内，说明场景背景和对话目的）

请以 JSON 格式返回，格式如下：
[
  {{"title": "场景标题", "description": "场景描述"}},
  ...
]
"""
    response = await provider.chat(prompt)
    return parse_json(response)

async def generate_sentence(role: str, language: str, scenario: str) -> dict:
    prompt = f"""你是一位专业的语言教师。
请为以下场景生成一句实用的口语句子：

角色：{role}
目标语言：{language}
场景：{scenario}

请返回：
1. 中文提示：用户需要表达的意思
2. 目标语言句子：地道的表达方式
3. （可选）发音指南：IPA 音标或谐音

请以 JSON 格式返回：
{{
  "chinese": "中文提示内容",
  "target_text": "Target language sentence",
  "pronunciation_guide": "/prəˌnʌnsiˈeɪʃən/"
}}
"""
    response = await provider.chat(prompt)
    return parse_json(response)
```

### 7.2 LLM Prompt 设计建议

**场景生成 Prompt 模板：**
```python
SCENARIO_GENERATION_PROMPT = """
你是一位专业的语言学习场景设计师，擅长为不同角色的学习者设计实用的口语练习场景。

学习者角色：{role}
目标语言：{language}
学习者水平：{proficiency}

请生成{count}个与该角色高度相关的口语练习场景。

要求：
1. 场景必须真实、实用，符合该角色的日常需求
2. 场景描述清晰，让用户一眼就能理解情境
3. 难度适中，适合{proficiency}水平的学习者

返回 JSON 格式：
[
  {{
    "title": "场景标题（简洁明了）",
    "description": "场景描述（包含背景、对话对象、沟通目的）"
  }}
]
"""
```

**句子生成 Prompt 模板：**
```python
SENTENCE_GENERATION_PROMPT = """
你是一位经验丰富的语言教师，擅长设计循序渐进的口语练习句子。

角色：{role}
目标语言：{language}
当前场景：{scenario_title} - {scenario_description}
学习者水平：{proficiency}

请生成一句在该场景下角色可能会说的话：

要求：
1. 句子地道、自然，符合母语者表达习惯
2. 难度匹配学习者水平
3. 实用性强，学习者能在真实场景中复用
4. 长度适中（初学者 5-10 词，进阶 10-20 词）

返回 JSON 格式：
{{
  "chinese": "这句话要表达的中文意思",
  "target_text": "The target language sentence",
  "pronunciation_guide": "可选的发音指南",
  "difficulty": "beginner/intermediate/advanced"
}}
"""
```

**单词查询 Prompt 模板：**
```python
WORD_LOOKUP_PROMPT = """
请为以下单词提供详细的学习信息：

单词：{word}
目标语言：{language}
中文母语者学习

请返回：
1. 准确的中文翻译
2. IPA 音标
3. 词性（名词/动词/形容词等）
4. 一个实用的例句（附带中文翻译）
5. 常见搭配或短语（如有）

返回 JSON 格式：
{{
  "translation": "中文翻译",
  "pronunciation": "/IPA/",
  "part_of_speech": "词性",
  "example_sentence": "Example with this word",
  "example_translation": "例句中文翻译",
  "collocations": ["常见搭配 1", "常见搭配 2"]
}}
"""
```

---

## 8. 实施步骤

### 阶段 1：基础架构搭建（预计 1-2 天）

**目标：** 完成项目骨架，可运行 Hello World

**任务：**
- [ ] 创建项目目录结构
- [ ] 配置 Python 虚拟环境
- [ ] 创建 FastAPI 基础应用 (`main.py`)
- [ ] 配置 SQLAlchemy 数据库连接
- [ ] 创建所有数据模型（暂不实现业务逻辑）
- [ ] 编写基础测试验证数据库连接
- [ ] 创建前端 HTML 骨架

**里程碑：** `GET /api/health` 返回 `{"status": "ok"}`，前端显示空白页面

---

### 阶段 2：认证功能（预计 2-3 天）

**目标：** 用户可以注册和登录

**任务：**
- [ ] 实现用户模型（含密码哈希）
- [ ] 实现 JWT 认证服务
- [ ] 实现注册 API (`POST /api/auth/register`)
- [ ] 实现登录 API (`POST /api/auth/login`)
- [ ] 实现用户信息 API (`GET /api/auth/me`)
- [ ] 前端实现登录/注册页面
- [ ] 前端实现 token 存储和认证状态管理

**里程碑：** 用户可以注册账号、登录、保持登录状态

---

### 阶段 3：用户配置（预计 1 天）

**目标：** 用户可以设置角色和语言偏好

**任务：**
- [ ] 实现用户配置模型
- [ ] 实现配置 API (`GET/POST /api/users/profile`)
- [ ] 前端实现角色和语言选择页面
- [ ] 保存用户选择到数据库

**里程碑：** 用户可以设置并保存角色和语言偏好

---

### 阶段 4：场景生成（预计 2-3 天）

**目标：** LLM 生成场景，用户可以选择

**任务：**
- [ ] 集成 `llm_provider.py`
- [ ] 实现场景生成服务
- [ ] 实现场景 API (`POST /api/scenarios/generate`, `GET /api/scenarios`)
- [ ] 实现场景选择 API (`POST /api/scenarios/:id/select`)
- [ ] 前端实现场景选择页面
- [ ] 前端实现加载状态和错误处理

**里程碑：** 用户可以生成并选择练习场景

---

### 阶段 5：句子生成与练习（预计 3-4 天）

**目标：** 核心练习功能可用

**任务：**
- [ ] 实现句子生成服务
- [ ] 实现句子 API (`GET /api/sentences/next`, `POST /api/sentences/:id/complete`)
- [ ] 前端实现练习页面核心布局
- [ ] 前端实现中文提示展示
- [ ] 前端实现答案显示功能
- [ ] 前端实现"下一句"和"换个场景"功能
- [ ] （可选）录音功能调研与实现

**里程碑：** 用户可以完成完整的口语练习流程

---

### 阶段 6：单词查询与单词本（预计 2-3 天）

**目标：** 单词学习功能完整

**任务：**
- [ ] 实现单词查询服务（调用 LLM）
- [ ] 实现单词本模型
- [ ] 实现单词本 API (`POST /api/vocabulary/lookup`, `GET/POST/DELETE /api/vocabulary`)
- [ ] 前端实现单词详情弹窗
- [ ] 前端实现单词本页面
- [ ] 前端实现添加到单词本功能

**里程碑：** 用户可以查询单词并保存到单词本

---

### 阶段 7：优化与部署（预计 2-3 天）

**目标：** 应用可部署上线

**任务：**
- [ ] 完善错误处理和日志
- [ ] 添加输入验证
- [ ] 优化前端性能和体验
- [ ] 配置 Railway 部署
- [ ] 配置 Supabase 数据库
- [ ] 设置环境变量
- [ ] 端到端测试
- [ ] 编写 README 和使用说明

**里程碑：** 应用成功部署到 Railway，可通过公网访问

---

## 9. 优先级总结

按照 **核心功能 > 美观度 > 额外功能** 的优先级：

### P0 - 核心功能（必须有）
- [ ] 用户注册/登录
- [ ] 角色和语言选择
- [ ] 场景生成与选择
- [ ] 句子生成与展示
- [ ] 显示答案功能
- [ ] 下一句/下一个场景

### P1 - 重要功能（应该有）
- [ ] 单词查询
- [ ] 单词本管理
- [ ] 学习记录追踪
- [ ] 移动端响应式设计

### P2 - 额外功能（可以有）
- [ ] 录音功能
- [ ] 发音评分
- [ ] 学习统计
- [ ] 复习提醒
- [ ] 主题切换

---

## 10. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| LLM API 成本高 | 高 | 使用 gpt-4o-mini 等经济模型；缓存生成的场景/句子 |
| 录音功能复杂 | 中 | 第一版可省略；使用浏览器 Web Audio API |
| Supabase 迁移问题 | 中 | 提前测试迁移脚本；保留 SQLite 备份 |
| 前端状态管理复杂 | 低 | 保持简单，使用 localStorage + 事件总线 |

---

## 11. 技术选型理由

| 技术 | 选择理由 |
|------|----------|
| FastAPI | 异步支持好，自动文档，类型安全 |
| SQLite (开发) | 零配置，文件型数据库，开发方便 |
| Supabase (生产) | 免费额度够用，PostgreSQL 兼容，自带备份 |
| 原生 JS (前端) | 无构建步骤，简单直接，适合单人项目 |
| Tailwind/Pico CSS | 快速样式开发，响应式支持好 |
| Railway | 部署简单，支持 Docker，免费额度 |

---

## 12. 下一步行动

1. **立即开始：** 阶段 1 - 项目结构搭建
2. **第一个里程碑：** 运行 Hello World API
3. **第一个可用版本：** 完成阶段 5（核心练习流程）
4. **上线版本：** 完成阶段 7

---

*文档最后更新：2026-03-15*
