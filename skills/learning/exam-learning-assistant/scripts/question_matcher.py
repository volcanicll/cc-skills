#!/usr/bin/env python3
"""
Question Matcher - Match questions against knowledge base and provide answers
"""

import re
from typing import Optional, Dict, List, Tuple

class QuestionMatcher:
    """Match exam questions with knowledge base answers"""

    def __init__(self, knowledge_base_path: str = "references/harmonyos_questions.md"):
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)

    def _load_knowledge_base(self, path: str) -> Dict[str, Dict]:
        """Load knowledge base from markdown file"""
        kb = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Parse question blocks
                pattern = r'###\s*(.+?)\n.*?```(.+?)```.*?答案[:：]\s*(.+?)(?:\n|$)'
                for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                    question = match.group(1).strip()
                    code = match.group(2).strip()
                    answer = match.group(3).strip()
                    kb[question] = {"code": code, "answer": answer}
        except FileNotFoundError:
            print(f"Knowledge base not found at {path}")
        return kb

    def identify_question_type(self, question_text: str) -> str:
        """Identify question type from text"""
        if "判断题" in question_text or "正确(True)" in question_text:
            return "true_false"
        elif "多选题" in question_text:
            return "multiple_choice"
        elif "单选题" in question_text:
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
        return ' '.join(content[:5])  # First few content lines

    def find_matching_answer(self, question_text: str) -> Optional[Dict]:
        """Find matching answer in knowledge base"""
        # Try exact match first
        if question_text in self.knowledge_base:
            return self.knowledge_base[question_text]

        # Try fuzzy matching
        content = self.extract_question_content(question_text)
        for kb_question, kb_data in self.knowledge_base.items():
            if content.lower() in kb_question.lower() or kb_question.lower() in content.lower():
                return kb_data

        return None

    def format_answer(self, answer: str, question_type: str) -> str:
        """Format answer for display"""
        if question_type == "true_false":
            return "正确" if answer.upper() in ["A", "TRUE", "正确", "✓"] else "错误"
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

        // UIAbility启动模式
        "singleton": "单实例，系统默认",
        "multiton": "多实例",
        "specified": "指定实例",

        // 组件相关
        "Tabs": "支持自定义组件和if/else/ForEach",
        "Radio": "单选，同组只能选一个",
        "Checkbox": "多选",
        "Stack": "层叠布局，支持z-index",

        // 元服务
        "元服务安装": "免安装，可直接使用",
        "元服务入口": "可点击、碰一碰、扫一扫触发",

        // ArkTS
        "ArkTS类型": "静态类型系统",
        "命名空间": "PascalCase命名",
        "async/await": "生命周期中可用但不会等待完成",

        // HTTP
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
