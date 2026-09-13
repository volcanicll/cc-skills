---
name: exam-learning-assistant
category: learning
description: "Automated exam assistance and learning companion for online certification tests. Use for: 1) Taking online certification exams with browser automation via agent-browser CDP, 2) Practicing questions with detailed explanations and knowledge retention, 3) Managing question banks and tracking incorrect answers. Supports HarmonyOS/ArkTS/ArkUI exam topics with extensible question database."
---

# Exam Learning Assistant

Browser-based exam automation and learning companion for online certification tests.

## Quick Start

```bash
# Connect to existing browser session
agent-browser --cdp 9222

# Start exam assistance
"Help me complete this exam"
```

---

## Learning Modes

This skill operates in two modes based on context:

### 🎯 Exam Mode (考试辅助)
Fast-paced assistance for active certification exams:
- Auto-connect to browser via CDP
- Real-time question recognition
- Direct answer delivery
- Automated option selection
- Progress tracking

### 📚 Learning Mode (自主学习)
Detailed explanations for practice and review:
- Question analysis with explanations
- Knowledge point linkage
- Wrong answer notebook
- Review guide generation
- Learning suggestions

**Auto-switching**: Mode determined by user context (URL keywords, explicit request, or conversation flow).

---

## Workflow

```
┌─────────────────┐
│ 1. Connect      │  agent-browser --cdp <port>
└────────┬────────┘
         │
┌────────▼─────────┐
│ 2. Identify Q    │  Parse question text, detect type
└────────┬────────┘
         │
┌────────▼─────────┐
│ 3. Query KB      │  Search knowledge base
└────────┬────────┘
         │
┌────────▼─────────┐
│ 4. Deliver Ans   │  Exam: direct / Learning: explain
└────────┬────────┘
         │
┌────────▼─────────┐
│ 5. Next Q        │  Auto or manual advance
└──────────────────┘
```

---

## Core Capabilities

### 1. Browser Automation

**Tool**: `agent-browser` via CDP connection

**Usage**:
```bash
# Connect to running Chrome
agent-browser --cdp 9222

# Get current question
agent-browser --cdp 9222 eval 'document.querySelector(".question-content")?.innerText'

# Select option
agent-browser --cdp 9222 click @e3  # Option A
```

**Prerequisites**: Chrome running with `--remote-debugging-port=9222`

---

### 2. Question Recognition

**Detect question type** from text:
- `判断题` / `正确(True)` → True/False
- `单选题` → Single Choice  
- `多选题` → Multiple Choice

**Extract elements**:
```python
question_text = extract_question_content(page_text)
options = parse_options(snapshot)
```

---

### 3. Knowledge Base Query

**Primary source**: [`references/harmonyos_questions.md`](references/harmonyos_questions.md)

**Query logic**:
1. Exact match on question text
2. Keyword fuzzy matching
3. Concept-based lookup

**Fallback**: When no match found, ask user for confirmation and learn for next time.

---

### 4. Answer Delivery

**Exam Mode**: Direct answer + auto-select
```
Q: [题目内容]
A: ✗ 错误
[Auto-selected, clicking Next...]
```

**Learning Mode**: Answer + explanation
```
Q: [题目内容]
A: ✗ 错误

📖 解析: 元服务核心特性是免安装
🔗 相关: UIAbility生命周期, Context继承
💡 记忆: "元服务 = 免安装服务"
```

---

### 5. Wrong Answer Notebook

Automatically track:
- Question content
- User's wrong answer
- Correct answer
- Explanation
- Knowledge point
- Timestamp

**Generate review guide**:
```bash
"生成今日错题复习单"
```

---

## Question Bank Structure

### Adding New Questions

Edit [`references/harmonyos_questions.md`](references/harmonyos_questions.md):

```markdown
### [知识点分类]

#### [题目类型]

**题目**: [完整题目内容]
**选项**: A. ... B. ... C. ... D. ...
**答案**: [正确答案]
**解析**: [详细解释]
**知识点**: [关联知识点]
```

### Knowledge Categories

- Context 生命周期
- UIAbility 组件
- ArkTS 语言特性
- ArkUI 组件
- 网络请求
- 数据存储
- 元服务 (Atomic Service)
- ExtensionAbility

---

## Scripts Reference

### `exam_controller.py`

Browser automation controller for CDP-connected browsers.

**Key methods**:
```python
controller = ExamController(cdp_port=9222)
question = controller.get_current_question()
controller.select_option("A")
controller.click_next()
```

**Usage**: Execute directly or import in workflow.

---

### `question_matcher.py`

Question parsing and knowledge base matching.

**Key methods**:
```python
matcher = QuestionMatcher("references/harmonyos_questions.md")
q_type = matcher.identify_question_type(text)
answer = matcher.find_matching_answer(question)
```

**Includes**: Predefined `HarmonyOSKnowledgeBase` for common patterns.

---

## Templates

### Exam Report Template

**Location**: [`assets/templates/exam_report.md`](assets/templates/exam_report.md)

**Generates**:
- Score summary
- Wrong question list
- Knowledge point analysis
- Learning suggestions

**Usage**:
```bash
"生成考试报告并保存到当前目录"
```

---

## Best Practices

### ⚠️ Important Considerations

1. **Academic Integrity**: Position as learning tool, not cheating aid
2. **Confirmation**: For ambiguous questions, ask user before auto-selecting
3. **Rate Limiting**: Maintain human-like answering pace (0.5-1s delay)
4. **Verification**: Confirm submit before final submission

### ✅ Recommended Workflow

```bash
# 1. Connect
agent-browser --cdp 9222

# 2. Take first question screenshot
agent-browser --cdp 9222 screenshot

# 3. Get question and answer
"这道题选什么？为什么？"

# 4. Continue through exam
"继续下一题"

# 5. Generate report after completion
"生成考试报告"
```

---

## Extending the Skill

### Adding New Exam Domains

1. Create new reference file: `references/[domain]_questions.md`
2. Populate with questions using template structure
3. Update `question_matcher.py` to include new domain
4. Test with sample questions

### Adding Custom Learning Modes

Edit [`references/learning_modes.md`](references/learning_modes.md) to define new interaction patterns.

---

## Troubleshooting

**Problem**: Can't connect to browser
```
Solution: Ensure Chrome is running with --remote-debugging-port=9222
```

**Problem**: Question not recognized
```
Solution: Take screenshot and manually parse question text
```

**Problem**: Wrong answer in knowledge base
```
Solution: Report error and update knowledge base for next time
```

---

## References

- [Agent Browser Documentation](../../agent-browser/) - Browser automation
- [HarmonyOS Developer Docs](https://developer.huawei.com/consumer/cn/doc/) - Official docs
- [Learning Modes Guide](references/learning_modes.md) - Mode usage details
