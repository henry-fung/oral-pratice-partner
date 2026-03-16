# LLM Prompt 模板

# 可用角色列表
AVAILABLE_ROLES = [
    {"id": "ielts", "name": "雅思考生", "icon": "📝"},
    {"id": "toefl", "name": "托福考生", "icon": "📚"},
    {"id": "student", "name": "留学生", "icon": "🎓"},
    {"id": "business_trade", "name": "外贸", "icon": "🌐"},
    {"id": "business_dev", "name": "程序员", "icon": "💻"},
    {"id": "business_data", "name": "数据科学家", "icon": "📊"},
    {"id": "traveler", "name": "旅游者", "icon": "✈️"},
    {"id": "daily", "name": "日常生活", "icon": "🏠"},
    {"id": "custom", "name": "自定义", "icon": "✏️"},
]

# 可用语言列表
AVAILABLE_LANGUAGES = [
    {"id": "en", "name": "英语", "native_name": "English", "flag": "🇺🇸"},
    {"id": "ja", "name": "日语", "native_name": "日本語", "flag": "🇯🇵"},
    {"id": "fr", "name": "法语", "native_name": "Français", "flag": "🇫🇷"},
    {"id": "es", "name": "西班牙语", "native_name": "Español", "flag": "🇪🇸"},
    {"id": "de", "name": "德语", "native_name": "Deutsch", "flag": "🇩🇪"},
    {"id": "ko", "name": "韩语", "native_name": "한국어", "flag": "🇰🇷"},
]

# 角色描述（用于 LLM 生成场景）
ROLE_DESCRIPTIONS = {
    "ielts": "一名准备雅思考试的考生，需要练习学术英语、图表描述、观点表达、面试问答等场景",
    "toefl": "一名准备托福考试的考生，需要练习学术讲座、校园对话、课堂讨论、演讲陈述等场景",
    "student": "一名在国外留学的学生，需要应对课堂讨论、与同学交流、日常生活购物等场景",
    "business_trade": "一名从事外贸工作的商务人士，需要与客户沟通、产品报价、订单处理、跨境会议等场景",
    "business_dev": "一名程序员，需要参与技术会议、代码评审、项目汇报、团队协作、技术面试等场景",
    "business_data": "一名数据科学家，需要进行数据分析汇报、模型讲解、团队分享、学术会议等场景",
    "traveler": "一名旅游者，需要问路、点餐、酒店入住、购物、景点游览等场景",
    "daily": "日常生活中的各种场景，如与邻居交流、去医院、银行办事、社交聚会等",
    "custom": "根据个人自定义的职业或身份，生成相应的实用口语场景",
}

SCENARIO_GENERATION_PROMPT = """你是一位专业的{language}口语教师，专门为{role}设计口语练习场景。

角色描述：{role_description}

请生成{count}个最实用的口语场景，这些场景应该是：
1. {role}最可能遇到的真实情况
2. 每个场景有明确的交流目的
3. 适合进行 2-5 轮对话练习
4. 难度适合{proficiency_level}水平的学习者
5. 生成的场景的title，description和context以中文的形式输出

**重要：必须返回恰好{count}个场景，以 JSON 数组格式返回。**

返回格式示例：
```json
[
  {{
    "title": "简短场景标题（10 字以内）",
    "description": "一句话描述场景（20 字以内）",
    "context": "详细的场景背景说明（50 字以内）"
  }},
  {{
    "title": "第二个场景标题",
    "description": "第二个场景描述",
    "context": "第二个场景的上下文"
  }}
]
```

只返回 JSON 数组，不要有任何其他文字。确保 JSON 格式正确可以被解析。"""

SENTENCE_GENERATION_PROMPT = """现在你是{role}，正在经历这个场景：
【场景】{scenario_title}
【描述】{scenario_description}
【上下文】{scenario_context}

请用{language}说出你（作为{role}）在这种情况下最可能说的2-5句话。

要求：
1. 符合{proficiency_level}水平
2. 实用、地道、常用

返回严格的 JSON 格式：
{{
  "native": "中文翻译",
  "target": "{language}原句"
}}

只返回 JSON 对象，不要有任何其他文字。确保 JSON 格式正确可以被解析。"""

WORD_LOOKUP_PROMPT = """请查询单词 "{word}" ({language}) 的详细信息。

返回严格的 JSON 格式：
{{
  "definition": "中文释义（50 字以内）",
  "pronunciation": "IPA 发音或拼音",
  "word_type": "词性（如 noun, verb, adjective 等）",
  "examples": ["例句 1（{language}）", "例句 2（{language}）"]
}}

只返回 JSON 对象，不要有任何其他文字。确保 JSON 格式正确可以被解析。"""
