#!/usr/bin/env python3
"""
Unit tests for QuestionMatcher in exam-learning-assistant.
"""

import unittest
from pathlib import Path
import sys

# Add scripts directory to sys.path
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from question_matcher import QuestionMatcher, HarmonyOSKnowledgeBase


class TestQuestionMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = QuestionMatcher()

    def test_knowledge_base_loaded(self):
        """Ensure the knowledge base is non-empty and parsed accurately."""
        self.assertGreater(len(self.matcher.knowledge_base), 15)

    def test_identify_question_type(self):
        """Test identification of various question types."""
        self.assertEqual(self.matcher.identify_question_type("判断题: 元服务无需安装即可使用"), "true_false")
        self.assertEqual(self.matcher.identify_question_type("单选题: 默认启动模式是什么"), "single_choice")
        self.assertEqual(self.matcher.identify_question_type("多选题: 以下属于生命周期回调的是"), "multiple_choice")
        self.assertEqual(self.matcher.identify_question_type("请问这是什么题"), "unknown")

    def test_format_answer(self):
        """Test formatting answers for display."""
        self.assertEqual(self.matcher.format_answer("✓ 正确", "true_false"), "正确")
        self.assertEqual(self.matcher.format_answer("A", "true_false"), "正确")
        self.assertEqual(self.matcher.format_answer("B", "true_false"), "错误")
        self.assertEqual(self.matcher.format_answer("✗ 错误", "true_false"), "错误")
        self.assertEqual(self.matcher.format_answer("B. onNewWant()", "single_choice"), "B. onNewWant()")

    def test_find_matching_answer(self):
        """Test finding exact and fuzzy answers."""
        # Exact/prefix match
        res = self.matcher.find_matching_answer("UIAbility在singleton模式下，再次调用startAbility()会进入哪些回调？")
        self.assertIsNotNone(res)
        self.assertIn("onNewWant", res["answer"])

        # Concept/fuzzy match
        res2 = self.matcher.find_matching_answer("startAbility中哪个参数区分不同UIAbility实例")
        self.assertIsNotNone(res2)
        self.assertIn("instanceKey", res2["answer"])

    def test_predefined_lookup(self):
        """Test HarmonyOS predefined answer lookup."""
        ans = HarmonyOSKnowledgeBase.lookup("ApplicationContext")
        self.assertIsNotNone(ans)
        self.assertIn("全局上下文", ans)

        ans2 = HarmonyOSKnowledgeBase.lookup("Tabs")
        self.assertIsNotNone(ans2)


if __name__ == "__main__":
    unittest.main()
