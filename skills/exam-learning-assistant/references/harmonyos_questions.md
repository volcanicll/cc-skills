# HarmonyOS 考试题库

> 本文件收录HarmonyOS开发者认证常见题目及其解析
> 按知识点分类整理，方便快速查找

## 目录

- [Context 生命周期](#context-生命周期)
- [UIAbility 组件](#uiability-组件)
- [ArkTS 语言特性](#arkts-语言特性)
- [ArkUI 组件](#arkui-组件)
- [网络请求](#网络请求)
- [数据存储](#数据存储)
- [元服务](#元服务)

---

## Context 生命周期

### Context继承关系
```
ApplicationContext (应用全局)
    ↑
    ├── AbilityStageContext (模块级)
    ├── UIAbilityContext (UIAbility专用)
    └── ExtensionContext (ExtensionAbility专用)
```

**典型题目**:
> 判断题: ApplicationContext、AbilityStageContext、UIAbilityContext以及ExtensionContext都继承于Context。

**答案**: ✓ 正确

---

### onCreate() 触发时机
- **冷启动**: onCreate() → onWindowStageCreate() → onForeground()
- **热启动**: 只触发 onForeground()
- **单实例模式后续启动**: 只触发 onNewWant()

**典型题目**:
> 单选题: UIAbility在singleton模式下，再次调用startAbility()会进入哪些回调？

**答案**: B. onNewWant()（不会再次调用onCreate和onWindowStageCreate）

---

### onBackground() 用途
- 释放UI不可见时的资源
- 执行耗时操作（如数据保存）
- 调用onSaveState()备份状态

**典型题目**:
> 单选题: 在哪个回调中释放UI不可时无用的资源？

**答案**: B. onBackground()

---

## UIAbility 组件

### 启动模式 (launchType)

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| singleton | 单实例，系统默认 | 大多数应用 |
| multiton | 每次启动创建新实例 | 需要多窗口 |
| specified | 按instanceKey区分实例 | 特定业务场景 |

**典型题目**:
> 单选题: singleton模式的默认启动方式？

**答案**: B. singleton是系统默认（非multiton）

---

### 实例区分参数
- **instanceKey**: 在want中设置，用于specified模式区分不同实例

**典型题目**:
> 单选题: startAbility()中哪个参数区分不同UIAbility实例？

**答案**: C. instanceKey

---

### 状态备份
- **onSaveState()**: 在onBackground()时自动调用
- 需在module.json5中启用备份恢复功能

**典型题目**:
> 单选题: 启用备份后，哪个生命周期调用onSaveState()？

**答案**: B. onBackground()

---

## ArkTS 语言特性

### 静态类型系统
- 强制静态类型检查
- 比TypeScript更严格的验证
- 减少运行时错误

**典型题目**:
> 判断题: ArkTS通过强制静态类型系统减少运行时错误？

**答案**: ✓ 正确

---

### async/await 在生命周期中
- **语法允许**: 可以使用async/await语法
- **行为限制**: 框架不会等待异步操作完成
- **不推荐**: 网络、定时器等异步操作可能无法正确执行

**典型题目**:
> 单选题: 关于生命周期使用async/await说法错误的是？

**答案**: A. 允许在生命周期函数中使用async await（说法不完整，未说明行为限制）

---

### 命名规范
- **命名空间**: PascalCase（大驼峰）
- **类**: PascalCase
- **接口**: PascalCase
- **变量/函数**: camelCase（小驼峰）
- **不推荐**: 中文拼音

**典型题目**:
> 单选题: 命名空间命名说法错误的是？

**答案**: C. 推荐采用小驼峰（错误，应使用PascalCase）

---

### 并发编程
- **TaskPool**: 任务池并发
- **Worker**: 线程并发
- **setCloneList()**: 克隆ArrayBuffer（值传递）
- **setTransferList()**: 转移ArrayBuffer所有权

**典型题目**:
> 单选题: ArrayBuffer多次调用不修改原对象，应该用什么？

**答案**: B. setCloneList()

---

## ArkUI 组件

### Tabs 组件
- **支持**: 自定义组件、if/else、ForEach
- **事件**: onTabChange() 切换时触发
- **动画**: customContentTransition 自定义切换动画

**典型题目**:
> 判断题: Tabs不支持自定义组件和渲染控制？

**答案**: ✗ 错误

---

### 容器组件对比

| 组件 | 用途 | 根节点能力 |
|------|------|-----------|
| Stack | 层叠布局 | ✓ |
| Column | 线性垂直布局 | ✓ |
| Row | 线性水平布局 | ✓ |
| Grid | 网格布局 | ✓ |
| List | 列表 | ✓ |
| Swiper | 轮播 | ✓ |
| Image | 图片 | ✗ 叶子组件 |

**典型题目**:
> 单选题: 哪个组件不能作为build()根节点？

**答案**: C. Image

---

### Radio vs Checkbox
- **Radio**: 单选，同组只能选一个
- **Checkbox**: 多选，可选多个

**典型题目**:
> 判断题: Radio同一组可以多个被选中？

**答案**: ✗ 错误

---

### 对齐方式
- **Column**:
  - alignItems(): 水平对齐（交叉轴）
  - justifyContent(): 垂直对齐（主轴）
- **Row**:
  - alignItems(): 垂直对齐（交叉轴）
  - justifyContent(): 水平对齐（主轴）

**典型题目**:
> 单选题: Column子元素水平居中？

**答案**: B. alignItems(HorizontalAlign.Center)

---

### 样式设置
- **fontColor()**: 文字颜色
- **borderStyle**: Dashed虚线
- **decoration**: TextDecorationType.Underline下划线
- **backgroundBrightness()**: 背景提亮

**典型题目**:
> 单选题: TextArea文字颜色设为红色？

**答案**: A. fontColor('#FF0000')

---

## 网络请求

### request vs requestInStream

| 特性 | request() | requestInStream() |
|------|-----------|-------------------|
| 返回类型 | HttpResponse | 流式数据 |
| 事件订阅 | ❌ | ✓ |
| 适用场景 | 小数据响应 | 大文件/流式 |

**典型题目**:
> 单选题: request/requestInStream说法错误的是？

**答案**: D. 都支持取消订阅（request不支持）

---

### priority 默认值
- **默认值**: 0
- **范围**: 值越大优先级越高

**典型题目**:
> 单选题: HTTP priority默认值？

**答案**: C. 0

---

### cookies
- **cookies字段**: 表示服务器返回的cookies

**典型题目**:
> 判断题: request回调返回值中cookies字段表示服务器cookies？

**答案**: ✓ 正确

---

## 数据存储

### 非线性容器

| 容器 | 键类型 | 特点 |
|------|--------|------|
| PlainArray | number | 整数键 |
| PlainMap | 任意 | 通用键值 |
| HashMap | 任意 | 哈希表 |
| TreeMap | 任意 | 有序键值 |

**典型题目**:
> 单选题: 哪种容器键必须是number？

**答案**: A. PlainArray

---

### Preferences (首选项)
- **getSync()**: 同步获取，需要Context和默认值
- **返回默认值情况**: null或非默认类型
- **flush()**: XML模式持久化
- **GSKV模式**: 实时持久化

**典型题目**:
> 多选题: getSync说法正确的是？

**答案**: A, C, D（需要Context、返回默认值、是同步接口）

---

## 元服务

### 核心特性
- **免安装**: 不需要显式安装
- **独立入口**: 点击、碰一碰、扫一扫
- **即用即走**: 快速启动

**典型题目**:
> 判断题: 元服务需要显式安装后才能使用？

**答案**: ✗ 错误（核心特性是免安装）

---

## ExtensionAbility

### 限制
- ❌ 不能自定义派生类型
- ❌ 不能获取其他应用的Context
- ✓ 只能使用预定义类型

**典型题目**:
> 单选题: 关于ExtensionAbility说法错误的是？

**答案**: B. 可以直接派生实现自定义类型（错误）

---

## 其他常见考点

### DevEco Studio
- **自动补全排序**: 支持按最近使用排序
- **证书安装**: 上传→点击安装/命令行管理器→选择格式
- **Module引用**: srcPath配置外部模块

### 服务卡片
- **创建**: New > Service Widget
- **类型**: Form/Widget

### 多设备分发
- **功能相同+UI自适应**: 单APP多设备
- **功能不同**: 多HAP分包

### 语音控制
- **API**: 语音识别API (AI Core Speech Kit)

### 底部导航条适配
- 抬高底部控件
- 弹窗避让
- 沉浸式自动隐藏
- 可滚动内容延伸

### 状态管理装饰器
- @State: 组件内部状态
- @Link: 双向绑定
- @Entry: 入口组件
- @Component: 自定义组件

### build()根节点
- ✓ Stack, Column, Row, Grid, List, Swiper
- ✗ Image, Text, Button（叶子组件）
