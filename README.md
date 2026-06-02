# 🏰 欧利蒂丝庄园（AI Manor Game）

> **AI 驱动的谋杀推理游戏引擎** | 每局独一无二的谜题 | 程序化叙事

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B.svg)](https://streamlit.io/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--Chat-green.svg)](https://deepseek.com/)

---

## 这是什么

一座维多利亚哥特式庄园。一场谋杀。五个嫌疑人。

**AI 在每局游戏开始时，基于角色关系网程序化生成一份完整的谋杀谜题**——死者、真凶、动机、手法、线索分布、NPC 证词。这份谜题是游戏的"标准答案"，AI 主持人据此推动叙事。

玩家的任务：探索庄园、与 NPC 交谈、收集线索、发现谎言，最终指认真凶。

**每一次游戏都是全新的谜题。**

---

## 与一般聊天机器人的区别

| | 普通 AI 聊天 | 本项目 |
|---|---|---|
| 叙事方式 | AI 自由发挥续写 | AI 基于"谜题剧本"驱动，有标准答案 |
| 剧情一致性 | 容易前后矛盾 | 谜题剧本作为约束，NPC 反应基于设定 |
| 记忆 | 单层上下文 | 分层记忆（近期对话 + 摘要 + 关键线索） |
| 游戏目标 | 模糊 | 明确——找到真凶 |
| 可复玩性 | 低（续写走向相似） | 高（每局谜题不同） |
| 工程结构 | 单文件 | 模块化（mystery_generator / narrator / memory） |

---

## 核心机制

### 谜题生成层（开局一次）

```
5个角色 + 关系网（仇敌/利益/背叛）
        ↓ AI 生成
一份完整谋杀剧本：
  · 死者是谁
  · 真凶是谁（动机基于角色关系）
  · 作案手法和时间线
  · 每条线索分布在哪个地点
  · 每个 NPC 的证词（包含真相 + 隐瞒 + 谎言）
```

### 玩家探索层

```
玩家行动 → AI 参考"剧本"生成回复 → 更新分层记忆 → 继续
                                              ↓
                                    近期对话 / 剧情摘要 / 已发现线索
```

### 终局

玩家指认真凶 → AI 核对剧本 → 正确（真相大白） / 错误（冤案）

---

## 技术架构

```
AI-Manor-Game/
├── app.py                       # Streamlit 主程序
├── engine/
│   ├── mystery_generator.py     # AI 谜题剧本生成
│   ├── narrator.py              # AI 主持人叙事引擎
│   └── memory.py                # 分层记忆系统
├── data/                        # （预留）
├── characters.json              # 角色数据 + 关系网
├── world.txt                    # 庄园氛围 + 基本规则
├── map.txt                      # 地点列表
├── requirements.txt
└── .env.example
```

### 分层记忆系统

| 层级 | 内容 | 形式 |
|------|------|------|
| 近期对话 | 最近 N 轮完整文本 | 原文 |
| 剧情摘要 | 早期剧情的 AI 压缩 | 2-3 句概述 |
| 关键线索 | 玩家已发现的线索 | 结构化列表 |

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY=你的key
```

### 3. 启动

```bash
streamlit run app.py
```

浏览器访问 `http://localhost:8501`

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Streamlit（Chat UI + Sidebar） |
| AI | DeepSeek API（deepseek-chat） |
| 状态管理 | streamlit.session_state |
| 数据 | JSON（角色）+ TXT（世界/地图） |
| 配置 | python-dotenv |

---

## 游戏结局

| 结局 | 条件 | 表现 |
|------|------|------|
| 🏆 真凶落网 | 正确指认真凶 | 真相大白，死者安息 |
| 💀 冤案 | 错误指认 | 真凶逃脱，冤魂又添 |

---

## 作者

**李欣键**

西南民族大学 · 人工智能专业 · 大二

GitHub：[lixinjian5](https://github.com/lixinjian5)

---

> 项目状态：v3.0 — AI 谋杀推理引擎。每局独一无二的谜题，分层记忆架构。
> 目标是打造可写进简历、可在实习面试中讲解的 AI 应用作品。
