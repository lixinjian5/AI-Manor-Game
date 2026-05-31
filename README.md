# AI-Manor-Game

基于大语言模型的剧情互动游戏。

## 项目介绍

AI-Manor-Game 是一个第五人格风格的文字剧情互动游戏。

玩家将在欧利蒂丝庄园中探索线索，
与NPC互动，
影响剧情发展，
最终触发不同结局。

## 技术栈

- Python
- Streamlit
- DeepSeek API
- Prompt Engineering

## 已实现功能

### 聊天系统

- Streamlit聊天界面
- DeepSeek API接入
- 多轮剧情互动

### 状态系统

- 地点(Location)
- 时间(Time)
- 理智值(Sanity)
- 行动次数(Actions Left)

### Memory系统（初版）

记录玩家关键行为：

- 帮助
- 怀疑
- 攻击
- 调查
- 发现

并自动加入Prompt。

## 项目结构

AI-Manor-Game
├─ chatxiangmu.py
├─ world.txt
├─ map.txt
├─ characters.json

## 运行方式

安装依赖：

pip install streamlit requests

启动项目：

streamlit run chatxiangmu.py

## 后续计划

- Memory系统升级
- NPC关系系统
- RAG记忆系统
- 多结局扩展
