import os
import traceback
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import OpenAI, AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def generate_with_image(self, system_prompt: str, image_url: str, text: str) -> str:
        """Generate a response from the LLM using image input (vision model).
        
        Args:
            system_prompt: System instructions for the model
            image_url: Data URL or URL of the image
            text: User text prompt accompanying the image
            
        Returns:
            Generated text response
        """
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        kwargs = {
            "model": self.model,
            "input": messages,
            "timeout": 60,
            "temperature": 0,
            "reasoning": {"effort": "none"},
        }
        if json_mode:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "person",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "PERSON",
                                                "PHONE",
                                                "EMAIL",
                                                "ID_CARD",
                                                "CREDIT_CARD",
                                                "ADDRESS",
                                                "ORG",
                                                "MEDICAL_HISTORY",
                                                "HEALTH_INSURANCE_ID",
                                                "POLICY_NUMBER",
                                                "CLAIM_NUMBER",
                                                "INSURANCE_PLAN",
                                            ],
                                        },
                                        "value": {"type": "string"},
                                        "position_start": {"type": "integer"},
                                        "confidence_level": {
                                            "type": "string",
                                            "enum": ["high", "medium", "low"],
                                        },
                                    },
                                    "required": [
                                        "type",
                                        "value",
                                        "position_start",
                                        "confidence_level",
                                    ],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["entities"],
                        "additionalProperties": False,
                    },
                }
            }

        response = self.client.responses.create(**kwargs)
        return response.choices[0].message.content
    
    def generate_with_image(self, system_prompt: str, image_url: str, text: str) -> str:
        """Generate a response using vision model (GPT-4o supports vision)."""
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            timeout=120
        )
        return response.choices[0].message.content


class AzureOpenAIProvider(LLMProvider):
    def __init__(
        self, api_key: str, endpoint: str, api_version: str, deployment_name: str
    ):
        # self.client = AzureOpenAI(
        #     api_key=api_key,
        #     azure_endpoint=endpoint,
        #     api_version=api_version
        # )
        self.client = OpenAI(
            api_key=api_key,
            base_url=endpoint,
            # api_version=api_version
        )
        self.deployment_name = deployment_name

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        kwargs = {
            "model": self.deployment_name,
            "input": messages,
            "timeout": 60,
            "temperature": 0,
            "reasoning": {"effort": "none"},
        }
        if json_mode:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": "person",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "PERSON",
                                                "PHONE",
                                                "EMAIL",
                                                "ID_CARD",
                                                "CREDIT_CARD",
                                                "ADDRESS",
                                                "ORG",
                                                "MEDICAL_HISTORY",
                                                "HEALTH_INSURANCE_ID",
                                                "POLICY_NUMBER",
                                                "CLAIM_NUMBER",
                                                "INSURANCE_PLAN",
                                            ],
                                        },
                                        "value": {"type": "string"},
                                        "position_start": {"type": "integer"},
                                        "confidence_level": {
                                            "type": "string",
                                            "enum": ["high", "medium", "low"],
                                        },
                                    },
                                    "required": [
                                        "type",
                                        "value",
                                        "position_start",
                                        "confidence_level",
                                    ],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["entities"],
                        "additionalProperties": False,
                    },
                }
            }

        response = self.client.responses.create(**kwargs)
        # return response.choices[0].message.content
        # print(response)
        return response.output_text
    
    def generate_with_image(self, system_prompt: str, image_url: str, text: str) -> str:
        """Generate a response using Azure OpenAI vision model."""
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=1,
            timeout=120
        )
        return response.choices[0].message.content


class CustomProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    # @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "timeout": 60,
            "temperature": 1,
            "seed":0
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def generate_with_image(self, system_prompt: str, image_url: str, text: str) -> str:
        """Generate a response using vision-capable model (e.g., Kimi-VL, GPT-4V).
        
        For Kimi/Moonshot, uses the standard chat API with image support.
        Note: Some models (like Kimi) only support temperature=1.
        """
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        
        # Use a vision-capable model variant if available
        vision_model = self.model
        # Map common non-vision models to vision equivalents
        model_mappings = {
            "moonshot-v1-8k": "moonshot-v1-8k-vision-preview",
            "moonshot-v1-32k": "moonshot-v1-32k-vision-preview",
            "moonshot-v1-128k": "moonshot-v1-128k-vision-preview",
            "gpt-3.5-turbo": "gpt-4o",
            "gpt-4": "gpt-4o",
        }
        if vision_model in model_mappings:
            vision_model = model_mappings[vision_model]
        
        response = self.client.chat.completions.create(
            model=vision_model,
            messages=messages,
            temperature=1,
            timeout=120
        )
        return response.choices[0].message.content


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google genai package not installed. Run: pip install google-genai")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model

    def generate(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        generation_config = {
            "temperature": 0,
        }
        if json_mode:
            generation_config["response_mime_type"] = "application/json"

        system_instruction = None
        contents = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents = content

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                response_mime_type="application/json" if json_mode else None,
            ),
        )
        return response.text
    
    def generate_with_image(self, system_prompt: str, image_url: str, text: str) -> str:
        """Generate a response using Gemini's multimodal capability.
        
        Note: image_url should be a data URL (data:image/xxx;base64,...)
        """
        # Parse data URL to get base64 content
        if image_url.startswith('data:'):
            # Extract mime_type and base64 data
            header, base64_data = image_url.split(',', 1)
            mime_type = header.split(';')[0].split(':')[1]
            import base64
            image_data = base64.b64decode(base64_data)
        else:
            # Regular URL - fetch it
            import requests
            import base64
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            mime_type = "image/jpeg"  # Default
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"{system_prompt}\n\n{text}"),
                        types.Part.from_bytes(data=image_data, mime_type=mime_type)
                    ]
                )
            ]
        )
        return response.text
    
    def extract_text_from_image(self, image_data: bytes, mime_type: str = "image/jpeg") -> str:
        """Extract text from image using Gemini's multimodal capability."""
        from google.genai import types
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text="Extract all text from this image. If it's a chat screenshot, preserve the conversation format with speaker names and messages."
                        ),
                        types.Part.from_bytes(data=image_data, mime_type=mime_type)
                    ]
                )
            ]
        )
        return response.text
    
    def format_chat_history_from_text(self, raw_text: str) -> str:
        """Use LLM to format extracted text into standard chat format."""
        prompt = f"""You are a chat history formatter. Given raw text extracted from a screenshot, format it into a clean, standardized chat format.

Input text:
{raw_text}

Please format the text following these rules:
1. Identify the speakers (e.g., "亲人:", "我:", "Mom:", "Me:", etc.)
2. Format as: "Speaker: Message"
3. Each message on a new line
4. Remove timestamps, phone status bars, and UI elements
5. Preserve the original language
6. Keep the conversation flow natural

Output format example:
亲人：吃饭了吗？
我：刚吃完
亲人：多吃点，别饿着

Formatted chat history:"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        return response.text.strip()


class LLMFactory:

    @staticmethod
    def create() -> LLMProvider:
        provider_type = os.getenv("LLM_PROVIDER", "openai").lower()

        if provider_type == "azure":
            return AzureOpenAIProvider(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            )
        elif provider_type == "gemini":
            return GeminiProvider(
                api_key=os.getenv("GEMINI_API_KEY"),
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            )
        elif provider_type == "custom":
            return CustomProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            )
        elif provider_type == "kimi":
            return CustomProvider(
                api_key=os.getenv("KIMI_API_KEY"),
                base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
                model=os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
            )
        else:
            # Default to OpenAI
            return OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            )


if __name__ == "__main__":
    try:
        print("Testing LLMProvider...")
        provider = LLMFactory.create()
        messages = [
            {
                "role": "user",
                "content": "Hello, what is your name?",
            }
        ]
        response = provider.generate(messages)
        print("\nResponse Received:")
        print("-" * 20)
        print(response)
        print("-" * 20)
    except Exception as e:
        traceback.print_exc()
        print(f"\nError occurred: {e}")
