import json
import re
import random
import string
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.services.llm_provider import LLMFactory, LLMProvider
from backend.utils.prompts import (
    SCENARIO_GENERATION_PROMPT,
    SCENARIO_ENRICH_PROMPT,
    SENTENCE_GENERATION_PROMPT,
    WORD_LOOKUP_PROMPT,
    ROLE_DESCRIPTIONS,
)


class ScenarioData(BaseModel):
    """场景数据模型"""
    title: str = Field(..., description="简短场景标题（10 字以内）")
    description: str = Field(..., description="一句话描述场景（20 字以内）")
    context: str = Field(..., description="详细的场景背景说明（50 字以内）")


class ScenarioList(BaseModel):
    """场景列表模型"""
    scenarios: List[ScenarioData] = Field(..., description="场景列表")


class SentenceData(BaseModel):
    """句子数据模型"""
    native: str = Field(..., description="句子的中文意思（实际翻译内容）")
    target: str = Field(..., description="目标语言原句")
    pronunciation: Optional[str] = Field(None, description="IPA 或拼音发音指导")
    context: Optional[str] = Field(None, description="对方说的话（仅 continuation 使用）")


class WordLookupData(BaseModel):
    """单词查询数据模型"""
    definition: str = Field(..., description="中文释义（50 字以内）")
    pronunciation: str = Field(..., description="IPA 发音或拼音")
    word_type: str = Field(..., description="词性")
    examples: List[str] = Field(..., description="例句列表")


class LLMService:
    """LLM 业务服务层"""

    def __init__(self):
        self.provider: LLMProvider = LLMFactory.create()

    def _parse_json_response(self, response: str) -> Any:
        """尝试从响应中提取 JSON"""
        # 尝试直接解析
        try:
            data = json.loads(response.strip())
            # 如果是 {"scenarios": [...]} 格式，提取数组
            if isinstance(data, dict) and "scenarios" in data:
                return data["scenarios"]
            # 如果是单个场景对象，放入数组
            if isinstance(data, dict) and "title" in data and "description" in data:
                return [data]
            return data
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*(.+?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, dict) and "scenarios" in data:
                    return data["scenarios"]
                if isinstance(data, dict) and "title" in data and "description" in data:
                    return [data]
                return data
            except json.JSONDecodeError:
                pass

        # 尝试提取第一个 { 或 [ 开始的内容
        start_idx = response.find('{')
        if start_idx == -1:
            start_idx = response.find('[')

        if start_idx != -1:
            # 找到匹配的结束位置
            bracket = response[start_idx]
            end_bracket = '}' if bracket == '{' else ']'
            end_idx = response.rfind(end_bracket)

            if end_idx > start_idx:
                try:
                    data = json.loads(response[start_idx:end_idx + 1])
                    if isinstance(data, dict) and "scenarios" in data:
                        return data["scenarios"]
                    if isinstance(data, dict) and "title" in data and "description" in data:
                        return [data]
                    return data
                except json.JSONDecodeError:
                    pass

        # 如果所有尝试都失败，返回原始响应
        return response

    def generate_scenarios(
        self,
        role: str,
        language: str,
        count: int = 5,
        proficiency_level: str = "intermediate",
        custom_role_name: str = None
    ) -> List[Dict]:
        """生成 N 个与角色相关的口语场景"""
        # 如果是自定义角色，使用自定义名称
        if role == "custom" and custom_role_name:
            role_description = f"{custom_role_name}（请根据该职业/身份自行推断典型的工作或生活场景）"
            role_display = custom_role_name
        else:
            role_description = ROLE_DESCRIPTIONS.get(role, role)
            role_display = role

        random_seed = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        prompt = SCENARIO_GENERATION_PROMPT.format(
            role=role_display,
            role_description=role_description,
            language=language,
            count=count,
            proficiency_level=proficiency_level,
            random_seed=random_seed
        )

        # 使用 Pydantic 模型强制 JSON 格式
        response = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            response_format=ScenarioList
        )

        # 解析响应
        try:
            data = json.loads(response.strip())
            if isinstance(data, dict) and "scenarios" in data:
                return [s.model_dump() if hasattr(s, 'model_dump') else s for s in data["scenarios"]]
            # 如果直接返回数组
            if isinstance(data, list):
                return data
            # 如果返回单个对象
            if isinstance(data, dict) and "title" in data:
                return [data]
        except (json.JSONDecodeError, Exception):
            pass

        # 回退到旧方法
        return self._parse_json_response(response)

    def enrich_scenario(
        self,
        scenario_input: str,
        role: str,
        language: str,
        proficiency_level: str = "intermediate",
        custom_role_name: str = None,
    ) -> Dict:
        """Turn a user's free-form scenario request into an editable scenario draft."""
        if role == "custom" and custom_role_name:
            role_display = custom_role_name
            role_description = f"{custom_role_name}（请据此推断典型的工作或生活场景）"
        else:
            role_display = role
            role_description = ROLE_DESCRIPTIONS.get(role, role)

        prompt = SCENARIO_ENRICH_PROMPT.format(
            role=role_display,
            role_description=role_description,
            language=language,
            proficiency_level=proficiency_level,
            scenario_input=scenario_input,
        )
        response = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            response_format=ScenarioData,
        )
        data = self._parse_json_response(response)
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            raise ValueError("LLM 未返回有效的场景数据")
        return data

    def generate_sentence(
        self,
        scenario: Dict,
        role: str,
        language: str,
        native_language: str = "zh",
        proficiency_level: str = "intermediate"
    ) -> Dict:
        """生成场景下的一句话"""
        prompt = SENTENCE_GENERATION_PROMPT.format(
            role=role,
            scenario_title=scenario.get("title", ""),
            scenario_description=scenario.get("description", ""),
            scenario_context=scenario.get("context", ""),
            language=language,
            proficiency_level=proficiency_level
        )

        response = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            response_format=SentenceData
        )

        return self._parse_json_response(response)

    def generate_continuation(
        self,
        scenario: Dict,
        previous_target: str,
        role: str,
        language: str,
        proficiency_level: str = "intermediate"
    ) -> Dict:
        from backend.utils.prompts import CONTINUATION_PROMPT
        prompt = CONTINUATION_PROMPT.format(
            role=role,
            scenario_title=scenario.get("title", ""),
            scenario_description=scenario.get("description", ""),
            scenario_context=scenario.get("context", ""),
            previous_target=previous_target,
            language=language,
            proficiency_level=proficiency_level,
        )
        response = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            response_format=SentenceData
        )
        return self._parse_json_response(response)

    def lookup_word(self, word: str, language: str) -> Dict:
        """查询单词详情"""
        prompt = WORD_LOOKUP_PROMPT.format(
            word=word,
            language=language
        )

        response = self.provider.generate(
            messages=[{"role": "user", "content": prompt}],
            json_mode=True
        )

        return self._parse_json_response(response)
