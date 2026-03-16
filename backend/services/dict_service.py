"""
词典服务 - 使用免费 API 查询单词详情
"""
import requests
from typing import Optional, Dict, Any
import re


class DictService:
    """词典服务，整合多个免费词典 API

    免费词典 API:
    - Free Dictionary API: https://api.dictionaryapi.dev/api/v2/entries/<lang>/<word>
    - WordsAPI: https://www.wordsapi.com/api/ (需要 key)
    - Datamuse: https://api.datamuse.com/words (同义词/反义词)

    我们主要使用 Free Dictionary API（开源免费，无需 key）
    """

    FREE_DICT_API = "https://api.dictionaryapi.dev/api/v2/entries"

    def lookup_word(self, word: str, language: str = "en") -> Dict[str, Any]:
        """
        查询单词详情

        Args:
            word: 要查询的单词
            language: 语言代码 (en, ja, fr, es, de, ko 等)

        Returns:
            包含单词信息的字典
        """
        word = word.strip().lower()

        if not word:
            return {"word": word, "definition": "", "pronunciation": "", "example_sentence": ""}

        # 根据语言选择 API
        if language == "en":
            return self._lookup_english(word)
        elif language == "ja":
            return self._lookup_japanese(word)
        elif language == "zh":
            return self._lookup_chinese(word)
        else:
            # 其他语言尝试通用方法
            return self._lookup_generic(word, language)

    def _lookup_english(self, word: str) -> Dict[str, Any]:
        """查询英语单词"""
        try:
            url = f"{self.FREE_DICT_API}/en/{word}"
            response = requests.get(url, timeout=5)

            if response.status_code == 404:
                return {
                    "word": word,
                    "definition": "未找到释义",
                    "pronunciation": "",
                    "example_sentence": ""
                }

            if response.status_code != 200:
                raise Exception(f"API 返回错误：{response.status_code}")

            data = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                return {
                    "word": word,
                    "definition": "未找到释义",
                    "pronunciation": "",
                    "example_sentence": ""
                }

            entry = data[0]

            # 提取发音
            pronunciation = ""
            if "phonetics" in entry and entry["phonetics"]:
                for phonetic in entry["phonetics"]:
                    if phonetic.get("text"):
                        pronunciation = phonetic["text"]
                        break

            # 提取释义
            definition = ""
            example_sentence = ""

            if "meanings" in entry and entry["meanings"]:
                meaning = entry["meanings"][0]
                part_of_speech = meaning.get("partOfSpeech", "")

                if "definitions" in meaning and meaning["definitions"]:
                    defn = meaning["definitions"][0]
                    definition = defn.get("definition", "")
                    if part_of_speech:
                        definition = f"[{part_of_speech}] {definition}"
                    example_sentence = defn.get("example", "")

            return {
                "word": word,
                "definition": definition,
                "pronunciation": pronunciation,
                "example_sentence": example_sentence
            }

        except requests.RequestException as e:
            # API 失败时返回基本信息
            return {
                "word": word,
                "definition": f"查询失败：{str(e)}",
                "pronunciation": "",
                "example_sentence": ""
            }
        except Exception as e:
            return {
                "word": word,
                "definition": f"查询出错：{str(e)}",
                "pronunciation": "",
                "example_sentence": ""
            }

    def _lookup_japanese(self, word: str) -> Dict[str, Any]:
        """查询日语单词"""
        # 日语可以使用 JMdict API 或 Jisho API
        try:
            # 使用 Jisho.org API
            url = f"https://jisho.org/api/v1/search/words?keyword={word}"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                raise Exception(f"API 返回错误：{response.status_code}")

            data = response.json()

            if not data.get("data") or len(data["data"]) == 0:
                return {
                    "word": word,
                    "definition": "未找到释义",
                    "pronunciation": "",
                    "example_sentence": ""
                }

            entry = data["data"][0]

            # 提取日语信息
            japanese_entry = entry.get("japanese", [{}])[0]
            reading = japanese_entry.get("reading", word)
            word_text = japanese_entry.get("word", word)

            pronunciation = f"{word_text} ({reading})"

            # 提取英文释义
            senses = entry.get("senses", [])
            if senses:
                definitions = "; ".join(senses[0].get("english_definitions", [])[:3])
                definition = definitions if definitions else "未找到释义"
            else:
                definition = "未找到释义"

            return {
                "word": f"{word_text} ({reading})",
                "definition": definition,
                "pronunciation": pronunciation,
                "example_sentence": ""
            }

        except Exception as e:
            return {
                "word": word,
                "definition": f"查询失败：{str(e)}",
                "pronunciation": "",
                "example_sentence": ""
            }

    def _lookup_chinese(self, word: str) -> Dict[str, Any]:
        """查询中文词语"""
        # 中文可以使用 汉典 API 或其他中文词典 API
        # 这里暂时返回基本信息
        return {
            "word": word,
            "definition": "中文词语释义（待完善）",
            "pronunciation": "",
            "example_sentence": ""
        }

    def _lookup_generic(self, word: str, language: str) -> Dict[str, Any]:
        """通用查询方法（用于其他语言）"""
        # 尝试使用 Free Dictionary API 的其他语言版本
        lang_map = {
            "fr": "french",
            "es": "spanish",
            "de": "german",
            "ko": "korean",
            "ru": "russian",
            "it": "italian",
        }

        lang_name = lang_map.get(language, language)

        try:
            url = f"{self.FREE_DICT_API}/{language}/{word}"
            response = requests.get(url, timeout=5)

            if response.status_code == 404:
                return {
                    "word": word,
                    "definition": f"未找到 {lang_name} 单词 '{word}' 的释义",
                    "pronunciation": "",
                    "example_sentence": ""
                }

            if response.status_code != 200:
                raise Exception(f"API 返回错误：{response.status_code}")

            data = response.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                return {
                    "word": word,
                    "definition": f"未找到 {lang_name} 单词 '{word}' 的释义",
                    "pronunciation": "",
                    "example_sentence": ""
                }

            entry = data[0]

            pronunciation = ""
            definition = ""
            example_sentence = ""

            if "phonetics" in entry and entry["phonetics"]:
                for phonetic in entry["phonetics"]:
                    if phonetic.get("text"):
                        pronunciation = phonetic["text"]
                        break

            if "meanings" in entry and entry["meanings"]:
                meaning = entry["meanings"][0]
                part_of_speech = meaning.get("partOfSpeech", "")

                if "definitions" in meaning and meaning["definitions"]:
                    defn = meaning["definitions"][0]
                    definition = defn.get("definition", "")
                    if part_of_speech:
                        definition = f"[{part_of_speech}] {definition}"
                    example_sentence = defn.get("example", "")

            return {
                "word": word,
                "definition": definition,
                "pronunciation": pronunciation,
                "example_sentence": example_sentence
            }

        except Exception as e:
            return {
                "word": word,
                "definition": f"查询失败：{str(e)}",
                "pronunciation": "",
                "example_sentence": ""
            }


# 单例
dict_service = DictService()
