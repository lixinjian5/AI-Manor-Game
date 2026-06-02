import streamlit as st
import os
import re
import json
from dotenv import load_dotenv

from engine import generate_mystery, MemoryManager, narrate, check_accusation
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
st.caption("一场谋杀。五个嫌疑人。真相只有一个。")

# =========================
# 加载静态数据
# =========================
with open(os.path.join(BASE_DIR, "map.txt"), "r", encoding="utf-8") as f:
    game_map = f.read()

with open(os.path.join(BASE_DIR, "world.txt"), "r", encoding="utf-8") as f:
    world_setting = f.read()

with open(os.path.join(BASE_DIR, "characters.json"), "r", encoding="utf-8") as f:
    characters = json.load(f)

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


def parse_victim(script: str) -> str:
    m = re.search(r"死者[：:]\s*(.+)", script)
    return m.group(1).strip() if m else "一位客人"


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


# =========================
# 开局：生成谜题
# =========================
if not st.session_state.game_started:
    with st.spinner("🕯️ 正在生成本局谜题……（约30秒）"):
        script = generate_mystery(DEEPSEEK_API_KEY, characters, world_setting)

    if not script or "真凶" not in script:
        st.error("谜题生成失败，请刷新页面重试。")
        st.stop()

    st.session_state.mystery_script = script
    st.session_state.killer = parse_killer(script)
    st.session_state.victim = parse_victim(script)

    victim = st.session_state.victim
    alive_npcs = [name for name in characters if name != victim]
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

alive = [n for n in characters if n != st.session_state.victim]
if alive:
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 嫌疑人")
    for name in alive:
        st.sidebar.caption(f"• {characters[name]['身份']} — {name}")

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
        killer = st.session_state.killer
        correct = accused in killer or killer in accused

        if correct:
            ending_msg = f"""
            {prompt}

            ---

            🏆 **真凶落网**

            「{killer}」—— 当这个名字被说出时，一切安静了。

            证据确凿。真相大白。

            凶手的面具终于被撕下。{st.session_state.victim}的灵魂得以安息。

            你做到了。

            🎮 **结局：真相大白**
            """
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": ending_msg})
            st.session_state.game_ended = True
            st.rerun()
        else:
            ending_msg = f"""
            {prompt}

            ---

            💀 **冤案**

            你指认了{accused}。

            但真正的凶手是**{killer}**。

            被冤枉的人踉跄后退，而真正的凶手嘴角浮现一丝冷笑。

            在你错误的指控下，真凶趁乱消失在庄园的迷雾中。

            庄园又多了一桩悬案，和两个冤魂。

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
            characters=characters,
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
