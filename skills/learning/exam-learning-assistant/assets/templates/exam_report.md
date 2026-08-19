# {{exam_name}} - 考试报告

> 考试时间: {{exam_date}}
> 考试链接: {{exam_url}}
> 答题模式: {{mode}}

---

## 📊 考试概况

| 项目 | 结果 |
|------|------|
| **总题数** | {{total_questions}} |
| **答对** | {{correct_count}} |
| **答错** | {{wrong_count}} |
| **正确率** | {{accuracy}}% |
| **用时** | {{duration}} |

---

## 题型分布

| 题型 | 数量 | 正确率 |
|------|------|--------|
| 判断题 | {{true_false_count}} | {{tf_accuracy}}% |
| 单选题 | {{single_choice_count}} | {{sc_accuracy}}% |
| 多选题 | {{multiple_choice_count}} | {{mc_accuracy}}% |

---

## ❌ 错题回顾

### 错题列表

{% for question in wrong_questions %}
#### {{question.number}}. {{question.type}} - {{question.topic}}

**题目**: {{question.content}}

**你的答案**: {{question.user_answer}}
**正确答案**: {{question.correct_answer}}

**解析**: {{question.explanation}}

**知识点**: {{question.knowledge_point}}

---

{% endfor %}

---

## 📚 知识点掌握情况

### 掌握良好 ✅
{% for topic in mastered_topics %}
- {{topic}}
{% endfor %}

### 需要加强 ⚠️
{% for topic in weak_topics %}
- {{topic}} (错误率: {{topic.error_rate}}%)
{% endfor %}

---

## 💡 学习建议

{{learning_suggestions}}

---

## 📝 备注

{{notes}}
