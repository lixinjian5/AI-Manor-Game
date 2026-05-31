# AI-Manor-Game

基于大语言模型的文字剧情互动游戏 | 第五人格风格

## 项目介绍

AI-Manor-Game 是一个有《第五人格》元素的 AI 剧情互动文字游戏。

玩家将在欧利蒂丝庄园中探索线索、与 NPC 互动，影响剧情发展，并根据自己的选择触发不同结局。

项目尝试将 Prompt Engineering、状态管理和记忆系统结合，打造具有沉浸感的 AI 剧情体验。

---

## 技术栈

- Python
- Streamlit
- DeepSeek API
- Prompt Engineering

---

## 已实现功能

### 聊天系统

- Streamlit 聊天界面
- DeepSeek API 接入
- 多轮剧情互动

### 状态系统

- 地点（Location）
- 时间（Time）
- 理智值（Sanity）
- 行动次数（Actions Left）

### Memory 系统（初版）

记录玩家关键行为：

- 帮助
- 怀疑
- 攻击
- 调查
- 发现

并自动注入 Prompt，影响后续剧情生成。

---

## 项目结构

```text
AI-Manor-Game/
├─ chatxiangmu.py
├─ world.txt
├─ map.txt
└─ characters.json
```

---

## 运行方式

安装依赖：

```bash
pip install streamlit requests
```

启动项目：

```bash
streamlit run chatxiangmu.py
```

---

## 项目亮点

- 基于大语言模型实现动态剧情生成
- 通过 Prompt Engineering 约束 NPC 行为与世界观
- 实现游戏状态管理系统
- 实现初版 Memory 记忆机制
- 支持多轮对话与剧情推进
- 支持多结局扩展

---

## 后续计划

### Memory 系统升级

实现：

- 短期记忆（Short Memory）
- 长期记忆（Long Memory）
- 重要事件记录（Important Events）

### NPC 关系系统

根据玩家行为动态调整 NPC 态度：

- 好感度（Favorability）
- 怀疑度（Suspicion）
- 信任度（Trust）

### RAG 记忆系统

实现：

```text
剧情资料
↓
Embedding
↓
向量数据库
↓
Top-K 检索
↓
Prompt 注入
↓
剧情生成
```

### 多结局扩展

根据玩家选择触发不同结局：

- 逃离庄园
- 真相结局
- 疯狂结局
- 隐藏结局

---

## 作者

李欣键

西南民族大学 · 人工智能专业

GitHub：

https://github.com/lixinjian5
