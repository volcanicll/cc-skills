#!/usr/bin/env python3
"""
Question Matcher - Match questions against knowledge base and provide answers
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

DEFAULT_KB_PATH = Path(__file__).resolve().parent.parent / "references" / "harmonyos_questions.md"


class QuestionMatcher:
    """Match exam questions with knowledge base answers"""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        target_path = Path(knowledge_base_path) if knowledge_base_path else DEFAULT_KB_PATH
        self.knowledge_base = self._load_knowledge_base(str(target_path))

    def _load_knowledge_base(self, path: str) -> Dict[str, Dict]:
        """Load knowledge base from markdown file"""
        kb: Dict[str, Dict] = {}
        target = Path(path)
        if not target.is_file():
            fallback = Path("references/harmonyos_questions.md")
            if fallback.is_file():
                target = fallback
            else:
                print(f"Knowledge base not found at {path}")
                return kb

        try:
            content = target.read_text(encoding="utf-8")
            sections = re.split(r"(?m)^###\s+", content)
            for sec in sections[1:]:
                lines = sec.split("\n", 1)
                topic = lines[0].strip()
                body = lines[1] if len(lines) > 1 else ""

                q_match = re.search(
                    r"\*\*典型题目\*\*[:：]?\s*\n+>\s*(.+?)(?=\n\n|\n\*\*|$)",
                    body,
                    re.DOTALL,
                )
                a_match = re.search(
                    r"\*\*答案\*\*[:：]?\s*(.+?)(?=\n---|\n###|\n\n##|$)",
                    body,
                    re.DOTALL,
                )

                code_match = re.search(r"```(?:\w+)?\n(.*?)```", body, re.DOTALL)
                code = code_match.group(1).strip() if code_match else ""

                question = q_match.group(1).strip() if q_match else ""
                answer = a_match.group(1).strip() if a_match else ""

                if question and answer:
                    clean_q = " ".join(question.split())
                    clean_a = " ".join(answer.split())
                    entry = {"topic": topic, "code": code, "answer": clean_a, "question": clean_q}
                    kb[clean_q] = entry
                    if topic not in kb:
                        kb[topic] = entry
                elif topic and answer:
                    clean_a = " ".join(answer.split())
                    kb[topic] = {"topic": topic, "code": code, "answer": clean_a, "question": topic}
        except Exception as err:
            print(f"Failed to load knowledge base from {target}: {err}")

        return kb

    def identify_question_type(self, question_text: str) -> str:
        """Identify question type from text"""
        if any(k in question_text for k in ["判断题", "判断", "正确(True)", "正确/错误", "对/错"]):
            return "true_false"
        elif any(k in question_text for k in ["多选题", "多选"]):
            return "multiple_choice"
        elif any(k in question_text for k in ["单选题", "单选"]):
            return "single_choice"
        return "unknown"

    def extract_question_content(self, full_text: str) -> str:
        """Extract the core question content"""
        lines = full_text.split('\n')
        content = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('第') and '题' not in line[:10]:
                if '正确' not in line and '错误' not in line:
                    content.append(line)
        return ' '.join(content[:5])

    @staticmethod
    def _normalize(text: str) -> str:
        """Strip punctuation and whitespace for fuzzy comparison"""
        return re.sub(r"[\s\(\)（）\?？:：!！,，。、_\"\'`]+", "", text).lower()

    def find_matching_answer(self, question_text: str) -> Optional[Dict]:
        """Find matching answer in knowledge base"""
        clean_text = " ".join(question_text.split())
        if clean_text in self.knowledge_base:
            return self.knowledge_base[clean_text]

        norm_query = self._normalize(question_text)
        if not norm_query:
            return None

        # 1. Check normalized containment against KB keys
        for kb_key, kb_data in self.knowledge_base.items():
            norm_key = self._normalize(kb_key)
            if norm_key in norm_query or norm_query in norm_key:
                return kb_data

        # 2. Match on core content
        content = self.extract_question_content(question_text).strip()
        if content:
            norm_content = self._normalize(content)
            for kb_key, kb_data in self.knowledge_base.items():
                norm_key = self._normalize(kb_key)
                if norm_content in norm_key or norm_key in norm_content:
                    return kb_data

        # 3. Match against topic
        for kb_data in self.knowledge_base.values():
            topic = kb_data.get("topic", "")
            if topic:
                norm_topic = self._normalize(topic)
                if norm_topic in norm_query or norm_query in norm_topic:
                    return kb_data

        return None

    def format_answer(self, answer: str, question_type: str) -> str:
        """Format answer for display"""
        if question_type == "true_false":
            ans_upper = answer.upper()
            if any(k in ans_upper for k in ["A", "TRUE", "正确", "✓"]):
                return "正确"
            elif any(k in ans_upper for k in ["B", "FALSE", "错误", "✗", "X"]):
                return "错误"
        return answer


class HarmonyOSKnowledgeBase:
    """Pre-defined answers for common HarmonyOS exam questions"""

    COMMON_ANSWERS = {
        # Context相关
        "ApplicationContext": "全局上下文，应用级别",
        "UIAbilityContext": "UIAbility上下文，UI操作",
        "AbilityStageContext": "模块级上下文",
        "ExtensionContext": "ExtensionAbility上下文",

        # 生命周期
        "onCreate": "冷启动时调用，后续启动不调用",
        "onNewWant": "单实例模式后续启动调用",
        "onForeground": "前台可见",
        "onBackground": "后台不可见",
        "onWindowStageCreate": "窗口创建",
        "onWindowStageDestroy": "窗口销毁",

        # UIAbility启动模式
        "singleton": "单实例，系统默认",
        "multiton": "多实例",
        "specified": "指定实例",

        # 组件相关
        "Tabs": "支持自定义组件和if/else/ForEach",
        "Radio": "单选，同组只能选一个",
        "Checkbox": "多选",
        "Stack": "层叠布局，支持z-index",

        # 元服务
        "元服务安装": "免安装，可直接使用",
        "元服务入口": "可点击、碰一碰、扫一扫触发",

        # ArkTS
        "ArkTS类型": "静态类型系统",
        "命名空间": "PascalCase命名",
        "async/await": "生命周期中可用但不会等待完成",

        # HTTP
        "request": "返回完整HttpResponse",
        "requestInStream": "流式响应",
        "priority默认值": "0",
    }

    @classmethod
    def lookup(cls, keyword: str) -> Optional[str]:
        """Look up answer by keyword"""
        for key, value in cls.COMMON_ANSWERS.items():
            if key.lower() in keyword.lower() or keyword.lower() in key.lower():
                return value
        return None


def main():
    matcher = QuestionMatcher()
    print(f"Loaded {len(matcher.knowledge_base)} knowledge base entries.")
    sample = "判断题: ApplicationContext、AbilityStageContext、UIAbilityContext以及ExtensionContext都继承于Context。"
    match = matcher.find_matching_answer(sample)
    if match:
        print(f"Sample query: {sample}")
        print(f"Matched answer: {match['answer']}")


if __name__ == "__main__":
    main()
