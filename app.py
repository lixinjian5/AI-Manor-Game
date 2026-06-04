import streamlit as st
import os
import re
import json
import random
from dotenv import load_dotenv

from engine import generate_mystery, MemoryManager, narrate, check_accusation, reveal_case
from engine.narrator import parse_killer

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    st.error("❌ 未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置 API Key")
    st.stop()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# 页面样式
# =========================
st.set_page_config(page_title="欧利蒂丝庄园", page_icon="🏰", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {
    font-size: 18px !important;
    line-height: 1.7;
    position: sticky !important;
    top: 0;
    height: 100vh !important;
    overflow-y: auto !important;
}
[data-testid="stChatMessage"] {
    font-size: 18px !important;
    line-height: 1.8;
}
[data-testid="stChatInput"] textarea {
    font-size: 17px !important;
}
[data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    height: 100vh !important;
}
[data-testid="stAppViewController"] .block-container {
    max-width: none !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏰 欧利蒂丝庄园")
st.caption("一场谋杀。真相只有一个。")

# =========================
# 加载静态数据
# =========================
with open(os.path.join(BASE_DIR, "map.txt"), "r", encoding="utf-8") as f:
    game_map = f.read()

with open(os.path.join(BASE_DIR, "world.txt"), "r", encoding="utf-8") as f:
    world_setting = f.read()

with open(os.path.join(BASE_DIR, "characters.json"), "r", encoding="utf-8") as f:
    ALL_CHARACTERS = json.load(f)

CHARACTER_POOL_SIZE = 5

ALL_LOCATIONS = {}
for line in game_map.strip().split("\n"):
    m = re.match(r"\d+\.\s*(.+)", line)
    if m:
        name = m.group(1).strip()
        ALL_LOCATIONS[name] = name


def detect_location(text: str) -> str | None:
    for loc in ALL_LOCATIONS:
        if loc in text:
            return loc
    return None


def match_character_name(name: str, active_characters: dict) -> str | None:
    """把 AI 输出的名字（可能是全名/身份/简称）匹配到 active_characters 的 key"""
    if not name:
        return None
    # 去除括号里的补充文字：薇拉·奈尔（调香师）→ 薇拉·奈尔
    clean = re.sub(r"[（(][^)）]*[)）]", "", name).strip()
    candidates = [name, clean] if clean != name else [name]
    for c in candidates:
        if c in active_characters:
            return c
    for c in candidates:
        for key, data in active_characters.items():
            if c in key or c in data.get("身份", ""):
                return key
    for c in candidates:
        for key in active_characters:
            if key in c:
                return key
    return None


def parse_victim(script: str, active_characters: dict) -> str:
    # 匹配 "死者：XXX" 或 "死者是XXX"，非贪婪，遇逗号句号换行停止
    for pat in [r"死者[：:]\s*(.+?)(?:[，。,.\n]|$)", r"死者是\s*(.+?)(?:[，。,.\n]|$)"]:
        m = re.search(pat, script)
        if m:
            raw = m.group(1).strip()
            matched = match_character_name(raw, active_characters)
            return matched if matched else raw
    return "一位客人"


# =========================
# session_state 初始化
# =========================
if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.messages = []
    st.session_state.mystery_script = ""
    st.session_state.killer = ""
    st.session_state.victim = ""
    st.session_state.memory = MemoryManager()
    st.session_state.location = "大厅"
    st.session_state.game_ended = False
    st.session_state.active_characters = {}

# 每局随机从角色池抽 5 人（1 死者 + 4 活人 = 1 真凶 + 3 嫌疑人）
if not st.session_state.active_characters:
    names = random.sample(list(ALL_CHARACTERS.keys()), CHARACTER_POOL_SIZE)
    st.session_state.active_characters = {n: ALL_CHARACTERS[n] for n in names}

# =========================
# 开局：生成谜题
# =========================
if not st.session_state.game_started:
    with st.spinner("🕯️ 正在生成本局谜题……（约30秒）"):
        script = generate_mystery(DEEPSEEK_API_KEY, st.session_state.active_characters, world_setting)

    if not script or "真凶" not in script:
        st.error("谜题生成失败，请刷新页面重试。")
        st.stop()

    st.session_state.mystery_script = script
    st.session_state.killer = parse_killer(script)
    # 同样做名字匹配：AI 可能输出"真凶：调香师"而非"真凶：薇拉·奈尔"
    resolved = match_character_name(st.session_state.killer, st.session_state.active_characters)
    if resolved:
        st.session_state.killer = resolved
    st.session_state.victim = parse_victim(script, st.session_state.active_characters)

    victim = st.session_state.victim
    alive_npcs = [name for name in st.session_state.active_characters if name != victim]
    loc_names = list(ALL_LOCATIONS.keys())

    opening = f"""
【欧利蒂丝庄园】

暴雨封锁了山路。一封没有署名的邀请函将你带到了这座被浓雾包围的庄园。

大厅里的烛光昏暗摇曳。其他客人已经到了——

{"、".join(alive_npcs)}，各自站在大厅的不同角落，神情各异。

但令你脊背发凉的是——

**{victim}** 死了。

尸体已被发现。每个人都说与自己无关。每个人都在撒谎。

而你，必须在谎言中找到真相。

━━━━━━━━━━━━━━
【当前目标】
① 探索庄园，搜索线索
② 与每位 NPC 交谈，获取证词
③ 发现每个人隐藏的秘密
④ 指认真凶 —— 你的指控将决定结局
━━━━━━━━━━━━━━

【你可以这样行动】
- 调查某个区域（{", ".join(loc_names)}）
- 与某人交谈（{" / ".join(alive_npcs)}）
- 检查尸体或案发现场
- 寻找物证

输入你的行动，游戏开始……
"""

    st.session_state.messages = [{"role": "assistant", "content": opening}]
    st.session_state.game_started = True
    st.rerun()

# =========================
# 侧边栏
# =========================
st.sidebar.title("🎭 调查笔记")

st.sidebar.write(f"📍 当前位置：{st.session_state.location}")

if st.session_state.victim:
    st.sidebar.write(f"💀 死者：{st.session_state.victim}")

alive = [n for n in st.session_state.active_characters if n != st.session_state.victim]
if alive:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 嫌疑人")
    for name in alive:
        st.sidebar.caption(f"• {st.session_state.active_characters[name]['身份']} — {name}")

if st.session_state.memory.facts:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 已发现线索")
    for f in st.session_state.memory.facts:
        st.sidebar.caption(f"• {f}")

st.sidebar.markdown("---")
st.sidebar.caption("当你准备好指认时，输入「我指认XXX」")
st.sidebar.caption("指认请慎重——错误指控的代价不可挽回。")

# =========================
# 显示历史消息
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# 输入处理
# =========================
if st.session_state.game_ended:
    st.stop()

prompt = st.chat_input("请输入你的行动")

if prompt:
    # ---- 指认检测 ----
    accused = check_accusation(prompt)
    if accused:
        resolved_accused = match_character_name(accused, st.session_state.active_characters) or accused
        resolved_killer = match_character_name(st.session_state.killer, st.session_state.active_characters) or st.session_state.killer
        correct = resolved_accused == resolved_killer

        if correct:
            with st.spinner("🕯️ 真相正在拼凑……"):
                case_reveal = reveal_case(DEEPSEEK_API_KEY, st.session_state.mystery_script)

            ending_msg = f"""
            {prompt}

            ---

            🏆 **真凶落网**

            「{resolved_killer}」—— 当这个名字被说出时，一切安静了。

            证据确凿。真相大白。

            ---
            {case_reveal}

            🎮 **结局：真相大白**
            """
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": ending_msg})
            st.session_state.game_ended = True
            st.rerun()
        else:
            with st.spinner("🕯️ 真相正在拼凑……"):
                case_reveal = reveal_case(DEEPSEEK_API_KEY, st.session_state.mystery_script)

            ending_msg = f"""
            {prompt}

            ---

            💀 **冤案**

            你指认了{resolved_accused}。

            但真正的凶手是**{resolved_killer}**。

            被冤枉的人踉跄后退，而真正的凶手嘴角浮现一丝冷笑。
            在你错误的指控下，真凶趁乱消失在庄园的迷雾中。

            ---
            **真正的真相：**
            {case_reveal}

            🎮 **结局：冤案**
            """
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": ending_msg})
            st.session_state.game_ended = True
            st.rerun()
        st.stop()

    # ---- 正常回合 ----
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("庄园正在回应……"):
        ai_reply = narrate(
            api_key=DEEPSEEK_API_KEY,
            mystery_script=st.session_state.mystery_script,
            characters=st.session_state.active_characters,
            world_setting=world_setting,
            memory=st.session_state.memory,
            player_input=prompt,
            messages_history=st.session_state.messages,
        )

    if not ai_reply:
        ai_reply = "庄园沉默了片刻……（AI 响应失败，请重试）"

    # 更新记忆
    st.session_state.memory.add_round(prompt, ai_reply)

    # 简单线索检测：AI 回复中如果有引号包裹的内容，视为潜在线索
    clues = re.findall(r"[「『""]([^」』""]{2,30})[」』""]", ai_reply)
    for c in clues:
        st.session_state.memory.add_fact(c)

    # 位置追踪（用 AI 回复 + 用户输入中的关键词，简单但够用）
    new_loc = detect_location(ai_reply) or detect_location(prompt)
    if new_loc:
        st.session_state.location = new_loc

    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    st.rerun()
