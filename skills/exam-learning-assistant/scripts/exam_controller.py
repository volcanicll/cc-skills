#!/usr/bin/env python3
"""
Exam Controller - Browser automation for exam assistance
Integrates with agent-browser for CDP-based browser control
"""

import subprocess
import json
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
        return result.stdout

    def get_current_question(self) -> Optional[str]:
        """Extract current question text from page"""
        return self.execute("eval 'document.querySelector(\".question-content\")?.innerText'")

    def get_question_number(self) -> int:
        """Get current question number"""
        text = self.execute("eval 'document.body.innerText'")
        if "第" in text and "题" in text:
            import re
            match = re.search(r'第(\d+)/(\d+)题', text)
            if match:
                return int(match.group(1))
        return 0

    def get_total_questions(self) -> int:
        """Get total number of questions"""
        text = self.execute("eval 'document.body.innerText'")
        if "题" in text:
            import re
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
        # Parse snapshot to find the element
        lines = snap.split('\n')
        for line in lines:
            if f'"{option_label}"' in line or f'"{option_label}' in line.lower():
                # Extract ref like [ref=eX]
                import re
                match = re.search(r'\[ref=(\w+)\]', line)
                if match:
                    ref = match.group(1)
                    self.execute(f"click @{ref}")
                    time.sleep(0.3)
                    return True
        return False

    def click_next(self) -> bool:
        """Click next question button"""
        return self.execute("click @e6") if self.execute("snapshot -i") else False

    def click_submit(self) -> bool:
        """Click submit exam button"""
        return self.execute("click @e1") if self.execute("snapshot -i") else False

    def get_screenshot(self) -> str:
        """Take screenshot and return path"""
        return self.execute("screenshot")

    def wait_for_page_load(self, timeout_ms: int = 5000):
        """Wait for page to fully load"""
        self.execute(f"wait --load networkidle")

def main():
    """Test the controller"""
    controller = ExamController()
    print(f"Current question: {controller.get_current_question()}")
    print(f"Progress: {controller.get_question_number()}/{controller.get_total_questions()}")

if __name__ == "__main__":
    main()
