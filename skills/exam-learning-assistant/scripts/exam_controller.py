#!/usr/bin/env python3
"""
Exam Controller - Browser automation for exam assistance
Integrates with agent-browser for CDP-based browser control
"""

import argparse
import json
import re
import subprocess
import time
from typing import Optional, List, Dict


class ExamController:
    """Control browser for automated exam assistance"""

    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self.base_cmd = f"agent-browser --cdp {cdp_port}"

    def execute(self, command: str) -> str:
        """Execute agent-browser command and return output"""
        cmd = f"{self.base_cmd} {command}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return (result.stdout or "").strip()

    def get_current_question(self) -> Optional[str]:
        """Extract current question text from page"""
        res = self.execute("eval 'document.querySelector(\".question-content\")?.innerText'")
        return res if res else None

    def get_question_number(self) -> int:
        """Get current question number"""
        text = self.execute("eval 'document.body.innerText'")
        if "第" in text and "题" in text:
            match = re.search(r'第(\d+)/(\d+)题', text)
            if match:
                return int(match.group(1))
        return 0

    def get_total_questions(self) -> int:
        """Get total number of questions"""
        text = self.execute("eval 'document.body.innerText'")
        if "题" in text:
            match = re.search(r'第(\d+)/(\d+)题', text)
            if match:
                return int(match.group(2))
        return 0

    def take_snapshot(self) -> str:
        """Get interactive elements snapshot"""
        return self.execute("snapshot -i")

    def select_option(self, option_label: str) -> bool:
        """Select an option by label (A, B, C, D or True/False)"""
        snap = self.take_snapshot()
        if not snap:
            return False
        # Parse snapshot to find the element
        lines = snap.split('\n')
        for line in lines:
            if f'"{option_label}"' in line or f'"{option_label}' in line.lower():
                match = re.search(r'\[ref=(\w+)\]', line)
                if match:
                    ref = match.group(1)
                    self.execute(f"click @{ref}")
                    time.sleep(0.3)
                    return True
        return False

    def click_next(self) -> bool:
        """Click next question button"""
        snap = self.take_snapshot()
        if snap:
            for line in snap.splitlines():
                line_lower = line.lower()
                if any(kw in line_lower for kw in ["下一题", "下一个", "next"]):
                    match = re.search(r'\[ref=(\w+)\]', line)
                    if match:
                        self.execute(f"click @{match.group(1)}")
                        time.sleep(0.3)
                        return True
        out = self.execute("click 'text=下一题'")
        return bool(out and "error" not in out.lower())

    def click_submit(self) -> bool:
        """Click submit exam button"""
        snap = self.take_snapshot()
        if snap:
            for line in snap.splitlines():
                line_lower = line.lower()
                if any(kw in line_lower for kw in ["提交", "交卷", "submit"]):
                    match = re.search(r'\[ref=(\w+)\]', line)
                    if match:
                        self.execute(f"click @{match.group(1)}")
                        time.sleep(0.3)
                        return True
        out = self.execute("click 'text=交卷'")
        return bool(out and "error" not in out.lower())

    def get_screenshot(self) -> str:
        """Take screenshot and return path"""
        return self.execute("screenshot")

    def wait_for_page_load(self, timeout_ms: int = 5000):
        """Wait for page to fully load"""
        self.execute("wait --load networkidle")


def main():
    """Test and run the controller"""
    parser = argparse.ArgumentParser(description="Exam Browser Automation Controller")
    parser.add_argument("--cdp", type=int, default=9222, help="CDP debugging port (default: 9222)")
    parser.add_argument("--status", action="store_true", help="Print current question status")
    args = parser.parse_args()

    controller = ExamController(cdp_port=args.cdp)
    q = controller.get_current_question()
    print(f"Current question: {q if q else '(none)'}")
    print(f"Progress: {controller.get_question_number()}/{controller.get_total_questions()}")


if __name__ == "__main__":
    main()
