# ai_extractor.py
# -*- coding: utf-8 -*-
"""
AI信息提取器
自动从章节内容中提取角色、地点、物品、情节发展等信息
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from llm_adapters import create_llm_adapter
from logger_config import get_logger

logger = get_logger("AIExtractor")


class AIExtractor:
    """AI信息提取器类"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model_name: str,
        interface_format: str = "OpenAI",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 600
    ):
        """
        初始化AI提取器

        Args:
            api_key: API密钥
            base_url: API地址
            model_name: 模型名称
            interface_format: 接口格式
            temperature: 温度参数（建议较低以确保准确性）
            max_tokens: 最大令牌数
            timeout: 超时时间
        """
        self.llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        logger.info("AI提取器初始化完成")

    def extract_characters(self, chapter_text: str) -> List[Dict]:
        """
        从章节文本中提取角色信息

        Args:
            chapter_text: 章节文本

        Returns:
            角色信息列表
        """
        prompt = f"""
请分析以下章节文本，提取所有出现的角色信息。对于每个角色，请提供：
1. 名字
2. 简短描述（如果文中有提到）
3. 该角色在本章的重要性（主要/次要/背景）

章节文本：
{chapter_text}

请以JSON格式返回，格式如下：
{{
    "characters": [
        {{
            "name": "角色名",
            "description": "简短描述",
            "importance": "主要/次要/背景"
        }}
    ]
}}
"""

        try:
            response = self.llm_adapter.chat([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response)

            if result and "characters" in result:
                logger.info(f"提取到 {len(result['characters'])} 个角色")
                return result["characters"]
            else:
                logger.warning("未能提取角色信息")
                return []
        except Exception as e:
            logger.error(f"提取角色时出错: {e}")
            return []

    def extract_locations(self, chapter_text: str) -> List[Dict]:
        """
        从章节文本中提取地点信息

        Args:
            chapter_text: 章节文本

        Returns:
            地点信息列表
        """
        prompt = f"""
请分析以下章节文本，提取所有出现的地点/场景。对于每个地点，请提供：
1. 地点名称
2. 地点描述（如果文中有提到）
3. 地点类型（室内/室外/城市/自然等）

章节文本：
{chapter_text}

请以JSON格式返回，格式如下：
{{
    "locations": [
        {{
            "name": "地点名",
            "description": "地点描述",
            "type": "地点类型"
        }}
    ]
}}
"""

        try:
            response = self.llm_adapter.chat([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response)

            if result and "locations" in result:
                logger.info(f"提取到 {len(result['locations'])} 个地点")
                return result["locations"]
            else:
                logger.warning("未能提取地点信息")
                return []
        except Exception as e:
            logger.error(f"提取地点时出错: {e}")
            return []

    def extract_items(self, chapter_text: str) -> List[Dict]:
        """
        从章节文本中提取重要物品信息

        Args:
            chapter_text: 章节文本

        Returns:
            物品信息列表
        """
        prompt = f"""
请分析以下章节文本，提取所有重要的物品/道具。对于每个物品，请提供：
1. 物品名称
2. 物品描述
3. 重要性（关键/重要/普通）

注意：只提取对情节有重要影响的物品，忽略普通日常用品。

章节文本：
{chapter_text}

请以JSON格式返回，格式如下：
{{
    "items": [
        {{
            "name": "物品名",
            "description": "物品描述",
            "importance": "关键/重要/普通"
        }}
    ]
}}
"""

        try:
            response = self.llm_adapter.chat([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response)

            if result and "items" in result:
                logger.info(f"提取到 {len(result['items'])} 个物品")
                return result["items"]
            else:
                logger.warning("未能提取物品信息")
                return []
        except Exception as e:
            logger.error(f"提取物品时出错: {e}")
            return []

    def extract_plot_developments(self, chapter_text: str, chapter_number: int) -> Dict:
        """
        从章节文本中提取情节发展信息

        Args:
            chapter_text: 章节文本
            chapter_number: 章节号

        Returns:
            情节发展信息
        """
        prompt = f"""
请分析第{chapter_number}章的文本，提取以下信息：

1. 本章主要事件（2-3个关键事件）
2. 情节推进（本章推进了哪些情节线）
3. 新增冲突（如果有）
4. 解决的冲突（如果有）
5. 伏笔（本章埋下的伏笔）
6. 回应（本章回应了之前的伏笔）

章节文本：
{chapter_text}

请以JSON格式返回，格式如下：
{{
    "main_events": ["事件1", "事件2"],
    "plot_progress": ["情节线1的进展", "情节线2的进展"],
    "new_conflicts": ["新冲突1", "新冲突2"],
    "resolved_conflicts": ["已解决的冲突1"],
    "foreshadowing": ["伏笔1", "伏笔2"],
    "callbacks": ["回应的伏笔1"]
}}
"""

        try:
            response = self.llm_adapter.chat([{"role": "user", "content": prompt}])
            result = self._parse_json_response(response)

            if result:
                logger.info(f"提取到第{chapter_number}章的情节发展信息")
                return result
            else:
                logger.warning(f"未能提取第{chapter_number}章的情节发展信息")
                return {}
        except Exception as e:
            logger.error(f"提取情节发展时出错: {e}")
            return {}

    def extract_chapter_summary(self, chapter_text: str, max_length: int = 300) -> str:
        """
        生成章节摘要

        Args:
            chapter_text: 章节文本
            max_length: 摘要最大长度

        Returns:
            章节摘要
        """
        prompt = f"""
请为以下章节文本生成一个简洁的摘要，不超过{max_length}字。
摘要应包含：
1. 主要情节发展
2. 关键角色行动
3. 重要转折点

章节文本：
{chapter_text}

请直接返回摘要文本，不要包含其他内容。
"""

        try:
            response = self.llm_adapter.chat([{"role": "user", "content": prompt}])
            summary = response.strip()

            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

            logger.info(f"生成章节摘要，长度: {len(summary)}")
            return summary
        except Exception as e:
            logger.error(f"生成摘要时出错: {e}")
            # 降级方案：简单截取
            return chapter_text[:max_length] + "..." if len(chapter_text) > max_length else chapter_text

    def extract_all_from_chapter(self, chapter_text: str, chapter_number: int) -> Dict:
        """
        从章节中提取所有信息

        Args:
            chapter_text: 章节文本
            chapter_number: 章节号

        Returns:
            包含所有提取信息的字典
        """
        logger.info(f"开始提取第{chapter_number}章的所有信息...")

        result = {
            "chapter_number": chapter_number,
            "characters": self.extract_characters(chapter_text),
            "locations": self.extract_locations(chapter_text),
            "items": self.extract_items(chapter_text),
            "plot_developments": self.extract_plot_developments(chapter_text, chapter_number),
            "summary": self.extract_chapter_summary(chapter_text)
        }

        logger.info(f"第{chapter_number}章信息提取完成")
        return result

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        解析LLM返回的JSON响应

        Args:
            response: LLM响应文本

        Returns:
            解析后的字典，失败返回None
        """
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON代码块
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 尝试查找第一个完整的JSON对象
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            logger.error("无法解析JSON响应")
            return None


def create_ai_extractor(
    api_key: str,
    base_url: str,
    model_name: str,
    interface_format: str = "OpenAI",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: int = 600
) -> AIExtractor:
    """
    创建AI提取器实例

    Args:
        api_key: API密钥
        base_url: API地址
        model_name: 模型名称
        interface_format: 接口格式
        temperature: 温度参数
        max_tokens: 最大令牌数
        timeout: 超时时间

    Returns:
        AIExtractor实例
    """
    return AIExtractor(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        interface_format=interface_format,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )


def auto_extract_and_update(
    chapter_text: str,
    chapter_number: int,
    filepath: str,
    api_key: str,
    base_url: str,
    model_name: str,
    interface_format: str = "OpenAI"
) -> Dict:
    """
    自动提取章节信息并更新到context_manager和plot_tracker

    Args:
        chapter_text: 章节文本
        chapter_number: 章节号
        filepath: 项目路径
        api_key: API密钥
        base_url: API地址
        model_name: 模型名称
        interface_format: 接口格式

    Returns:
        提取的信息字典
    """
    # 创建提取器
    extractor = create_ai_extractor(
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        interface_format=interface_format
    )

    # 提取所有信息
    extracted_info = extractor.extract_all_from_chapter(chapter_text, chapter_number)

    # 更新到context_manager
    try:
        context_file = Path(filepath) / "context_manager.json"
        if context_file.exists():
            from context_manager import create_context_manager
            context_manager = create_context_manager(filepath)

            # 添加章节摘要
            context_manager.add_chapter_summary(chapter_number, extracted_info["summary"])

            # 添加角色
            for char in extracted_info["characters"]:
                context_manager.add_character(
                    name=char["name"],
                    description=char.get("description", ""),
                    first_appearance=chapter_number
                )

            # 添加地点
            for loc in extracted_info["locations"]:
                context_manager.add_location(
                    name=loc["name"],
                    description=loc.get("description", ""),
                    first_appearance=chapter_number
                )

            # 添加物品
            for item in extracted_info["items"]:
                context_manager.add_item(
                    name=item["name"],
                    description=item.get("description", ""),
                    first_appearance=chapter_number
                )

            logger.info(f"已更新第{chapter_number}章信息到context_manager")
    except Exception as e:
        logger.error(f"更新context_manager时出错: {e}")

    # 更新到plot_tracker
    try:
        plot_file = Path(filepath) / "plotlines.json"
        if plot_file.exists():
            from plot_tracker import create_plot_tracker
            plot_tracker = create_plot_tracker(filepath)

            plot_dev = extracted_info.get("plot_developments", {})

            # 记录活跃情节的发展
            active_plots = plot_tracker.get_active_plots(chapter_number)
            for plot in active_plots:
                plot_id = plot["plot_id"]
                # 构建发展描述
                development_parts = []
                if plot_dev.get("main_events"):
                    development_parts.append(f"主要事件: {'; '.join(plot_dev['main_events'])}")
                if plot_dev.get("plot_progress"):
                    development_parts.append(f"情节进展: {'; '.join(plot_dev['plot_progress'])}")

                development = "\n".join(development_parts) if development_parts else "本章推进了该情节线"
                plot_tracker.record_chapter_plot(plot_id, chapter_number, development)

            logger.info(f"已更新第{chapter_number}章信息到plot_tracker")
    except Exception as e:
        logger.error(f"更新plot_tracker时出错: {e}")

    return extracted_info


if __name__ == "__main__":
    # 测试代码
    test_chapter = """
    李明走进了神秘的古堡，手中紧握着那把钥匙。这座古堡坐落在迷雾森林深处，
    据说已经荒废了数百年。在大厅中，他遇到了一位老者，老者告诉他关于这座
    古堡的秘密。李明意识到，这次冒险比他想象的更加危险。
    """

    # 这里需要实际的API配置
    # extractor = create_ai_extractor(
    #     api_key="your-api-key",
    #     base_url="https://api.openai.com/v1",
    #     model_name="gpt-4"
    # )
    #
    # result = extractor.extract_all_from_chapter(test_chapter, 1)
    # print(json.dumps(result, ensure_ascii=False, indent=2))
