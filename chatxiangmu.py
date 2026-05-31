import streamlit as st
import requests
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# =========================
# 页面全局样式（合并为一个块，避免冲突）
# =========================
st.markdown("""
<style>
/* ---- 侧边栏：固定不动 ---- */
[data-testid="stSidebar"] {
    font-size: 18px !important;
    line-height: 1.7;
    position: sticky !important;
    top: 0;
    height: 100vh !important;
    overflow-y: auto !important;
}

/* ---- 聊天消息文字 ---- */
[data-testid="stChatMessage"] {
    font-size: 18px !important;
    line-height: 1.8;
}

/* ---- 聊天输入框 ---- */
[data-testid="stChatInput"] textarea {
    font-size: 17px !important;
}

/* ---- 主内容区独立滚动，内容居左 ---- */
[data-testid="stAppViewContainer"] {
    overflow-y: auto !important;
    height: 100vh !important;
}
[data-testid="stAppViewContainer"] .block-container {
    max-width: none !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# API 配置（从环境变量读取，更安全）
# =========================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    st.error("❌ 未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置 API Key（参考 .env.example）")
    st.stop()
url = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

st.title("欧利蒂丝庄园")
st.caption("欢迎来到欧利蒂丝庄园。")

# =========================
# session_state 初始化
# =========================
defaults = {
    "messages": [],
    "memory": [],
    "location": "大厅",
    "time": "夜晚",
    "sanity": 100,
    "actions_left": 30,
    "short_memory": [],
    "important_events": [],
    "milestones": [],          # 关键剧情节点，用于追踪进度
    "npc_state": {},
    "game_log": [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =========================
# sidebar
# =========================
st.sidebar.title("🎭 玩家状态")

# 步数带进度条
st.sidebar.write(f"🕯️ 剩余行动：{st.session_state.actions_left}")
st.sidebar.progress(min(st.session_state.actions_left / 30, 1.0))

st.sidebar.write(f"📍 当前位置：{st.session_state.location}")
st.sidebar.write(f"🌙 当前时间：{st.session_state.time}")

# 理智值颜色提示
sanity = st.session_state.sanity
if sanity > 70:
    st.sidebar.write(f"🧠 理智值：{sanity}（清醒）")
elif sanity > 30:
    st.sidebar.write(f"🧠 理智值：{sanity}（不安）")
else:
    st.sidebar.write(f"🧠 理智值：{sanity}（濒临崩溃）")

# 关键发现
if st.session_state.milestones:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📜 关键发现")
    for m in st.session_state.milestones[-5:]:
        st.sidebar.caption(f"• {m}")

st.sidebar.markdown("---")
st.sidebar.caption("状态会随游戏实时更新")

# =========================
# 读取世界数据
# =========================
base_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base_dir, "map.txt"), "r", encoding="utf-8") as f:
    game_map = f.read()

with open(os.path.join(base_dir, "world.txt"), "r", encoding="utf-8") as f:
    world_background = f.read()

with open(os.path.join(base_dir, "characters.json"), "r", encoding="utf-8") as f:
    characters = json.load(f)

# =========================
# 从地图文件中提取所有地点，建立关键词表
# =========================
def parse_locations(map_text):
    """从 map.txt 中提取地点名，返回 {关键词: 地点名} 映射"""
    locs = {}
    for line in map_text.strip().split("\n"):
        m = re.match(r"\d+\.\s*(.+)", line)
        if m:
            name = m.group(1).strip()
            locs[name] = name
    return locs

ALL_LOCATIONS = parse_locations(game_map)

# 特殊地点效果（理智值变化）
LOCATION_EFFECTS = {
    "地下室": -10,
}

def detect_location_change(text):
    """扫描文本中是否出现地点关键词，返回 (新地点, 理智变化) 或 None"""
    for loc_name in ALL_LOCATIONS:
        if loc_name in text:
            effect = LOCATION_EFFECTS.get(loc_name, 0)
            return loc_name, effect
    return None

# =========================
# system prompt
# =========================
system_prompt = {
    "role": "system",
    "content": f"""
# Role
你是欧利蒂丝庄园的主持人，负责整个庄园的剧情推进和氛围控制。

# Task
1. 根据玩家的行动输出接下来的剧情
2. 扮演庄园中的NPC，包括医生、园丁、佣兵和律师
3. 充当旁白，描写环境和场景

# Rules
1. 推进剧情，保持逻辑合理，**主动向故事高潮推进**
2. 玩家行为必须符合庄园世界观
3. NPC行为和性格必须保持一致
4. 不允许出现现代网络语言
5. 适当制造悬念和神秘感，每隔几轮释放一点真相线索
6. 每次回复控制在200字以内
7. 给玩家提供可选行动引导
8. 当玩家移动到新区域时，必须在回复中明确写出地点名称

# 游戏结局条件（引导故事走向其中之一）
- **逃脱结局**：玩家揭开庄园真相，找到离开的方法
- **疯狂结局**：理智值归零 → 描写玩家精神崩溃
- **困死结局**：行动耗尽而未逃脱 → 庄园大门永远关闭

# Output Format
1. 场景环境描写（必须包含当前所在地点名称）
2. NPC描写
3. NPC行为和互动
4. 玩家状态或反应
5. 给玩家提供至少1-3个行动选项

# ⚠️ 重要：状态更新指令
在回复的最后，必须加上一行状态更新标记。格式必须精确（这是程序解析用的，玩家看不到）：

<STATE>
{"location": "玩家当前所在地点名称", "sanity_change": 理智变化数值, "milestone": "新的关键发现或null", "actions_used": 本次行动消耗步数(0或1)}
</STATE>

地点必须是以下之一：{list(ALL_LOCATIONS.keys())}
sanity_change：玩家做了可怕的事填负数(如-10)，发现希望填正数(如+5)，无变化填0
milestone：如果本轮揭露了重要秘密或真相线索，用简短文字描述(10字以内)；否则填"null"
actions_used：玩家主动调查/移动/做实质性行动填1，只是观察/思考/闲聊填0
escape：如果玩家成功逃脱填true，否则填false

# 当前状态
庄园世界观：{world_background}
庄园角色资料：{characters}
庄园区域：{game_map}
玩家当前位置：{st.session_state.location}
玩家理智值：{st.session_state.sanity}
剩余行动：{st.session_state.actions_left}
最近剧情：{st.session_state.game_log[-5:]}
"""
}

# =========================
# 开局剧情（只在第一次加载）
# =========================
if "game_started" not in st.session_state:
    opening_story = """
        【欧利蒂丝庄园】

        暴雨封锁了山路。

        你收到一封没有署名的邀请函，来到了这座被迷雾包围的庄园。

        大厅中央的吊灯微微摇晃，潮湿木地板散发着腐朽气味。

        你意识到，这里并不安全。

        远处传来钟声。

        有人在暗中观察你。

        ——你必须在这里活下去，并找到离开的方法。

        ━━━━━━━━━━━━━━
        【当前目标】
        ① 探索庄园，了解环境
        ② 与NPC交互，获取信息
        ③ 避免理智崩溃
        ④ 找到离开庄园的方法
        ━━━━━━━━━━━━━━

        【你可以尝试的行动】
        - 接近某位角色（医生 / 园丁 / 佣兵 / 律师）
        - 调查当前房间（大厅）
        - 前往其他区域（花园 / 医务室 / 地下室）
        - 询问庄园规则
        - 隐藏行动 / 单独探索

        请输入你的行动（例如：我去花园调查）……
        """

    st.session_state.messages = [
        system_prompt,
        {"role": "assistant", "content": opening_story}
    ]
    st.session_state.game_started = True

# =========================
# 显示历史消息
# =========================
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# =========================
# 输入处理
# =========================
prompt = st.chat_input("请输入你的行动")

if prompt:

    # =========================
    # 结束条件检测（显示完成局内容后停止）
    # =========================
    if st.session_state.sanity <= 0:
        st.chat_message("assistant").markdown("""
       【疯狂结局】

       你的理智彻底崩溃。

       耳边的低语越来越清晰。

       你终于明白了——这座庄园的真相。

       但你已无法告诉任何人……

       🎮 游戏结束 — 你的精神被庄园吞噬
       """)
        st.stop()

    if st.session_state.actions_left <= 0:
        st.chat_message("assistant").markdown("""
       【困死结局】

       最后一点时间耗尽了。

       钟声响起，大门缓缓关闭。

       你知道自己错过了逃离的机会。

       庄园又多了一位永久的住客……

       游戏结束 — 你未能逃出庄园
       """)
        st.stop()

    # 添加用户消息
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # 当前步数
    current_step = len(st.session_state.game_log) + 1

    # 最近剧情log
    recent_log = st.session_state.game_log[-5:]
    log_text = "\n".join([
        f"Step {e['step']} | 玩家:{e['player_input']} | 地点:{e['location']} | 理智:{e['sanity']} | AI:{e['ai_reply']}"
        for e in recent_log
    ])

    # 构建请求消息（注入多结局进度信息）
    temp_messages = [{
        "role": "system",
        "content": f"""
你是庄园主持人。当前是第{current_step}轮对话。

玩家状态：位置={st.session_state.location}，理智={st.session_state.sanity}，剩余行动={st.session_state.actions_left}
已发现线索：{st.session_state.milestones if st.session_state.milestones else "尚未发现关键线索"}

最近剧情：
{log_text}

请基于历史推进剧情。如果玩家已经发现了足够多的线索（3条以上），可以引导故事走向结局。
如果理智值低于30，在描写中体现玩家的精神压力。
"""
    }] + st.session_state.messages

    # API请求
    with st.spinner("庄园正在回应..."):
        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": temp_messages
                },
                timeout=30
            )
            result = response.json()
        except Exception as e:
            result = {"error": str(e)}

    # AI回复
    if "choices" in result:
        ai_reply = result["choices"][0]["message"]["content"]
    else:
        ai_reply = "庄园沉默了..."

    # =========================
    # 解析 <STATE> JSON 块（AI 驱动的状态更新，替代关键词匹配）
    # =========================
    display_reply = ai_reply
    state = None

    m = re.search(r"<STATE>\s*(\{.*?\})\s*</STATE>", ai_reply, re.DOTALL)
    if m:
        try:
            state = json.loads(m.group(1))
            # 从显示内容中移除 <STATE> 块
            display_reply = re.sub(r"<STATE>.*?</STATE>", "", ai_reply, flags=re.DOTALL).strip()
        except json.JSONDecodeError:
            pass

    # ---- 应用 AI 状态更新 ----
    if state:
        # 地点变化
        loc = state.get("location")
        if loc and loc in ALL_LOCATIONS and loc != st.session_state.location:
            st.session_state.location = loc

        # 理智变化
        sc = state.get("sanity_change", 0)
        if isinstance(sc, (int, float)):
            st.session_state.sanity = max(0, min(100, st.session_state.sanity + sc))

        # 里程碑
        ms = state.get("milestone")
        if ms and ms != "null" and ms not in st.session_state.milestones:
            st.session_state.milestones.append(ms)
            st.session_state.actions_left += 2

        # 步数消耗
        used = state.get("actions_used", 1)
        if used:
            st.session_state.actions_left -= 1

        # 逃脱检测
        if state.get("escape") is True:
            st.session_state.messages.append({
                "role": "assistant",
                "content": display_reply
            })
            st.chat_message("assistant").markdown(display_reply + "\n\n---\n\n🎮 **逃脱结局 — 你成功逃离了欧利蒂丝庄园！**")
            st.balloons()
            st.stop()

    else:
        # ---- 兜底：AI 没输出 <STATE> 时用关键词匹配 ----
        costly_keywords = [
            "调查", "搜索", "翻找", "打开", "进入", "推开", "拉动", "爬",
            "前往", "走向", "跑去", "离开", "上楼", "下楼",
            "攻击", "反抗", "逃跑", "逃离", "躲避", "追逐",
            "使用", "拿起", "放下", "破坏", "修理", "撬",
        ]
        user_loc = detect_location_change(prompt)
        if any(kw in prompt for kw in costly_keywords) or user_loc:
            st.session_state.actions_left -= 1
        if user_loc:
            loc_name, effect = user_loc
            st.session_state.location = loc_name
            st.session_state.sanity += effect

        ai_loc = detect_location_change(ai_reply)
        if ai_loc:
            loc_name, effect = ai_loc
            if loc_name != st.session_state.location:
                st.session_state.location = loc_name
                st.session_state.sanity += effect

        discoveries = re.findall(r"【发现：(.+?)】", ai_reply)
        for d in discoveries:
            if d not in st.session_state.milestones:
                st.session_state.milestones.append(d)
                st.session_state.actions_left += 2

        escape_keywords = ["离开了庄园", "逃出", "逃脱", "找到了出路", "大门敞开了", "终于自由", "离开这里"]
        if any(kw in ai_reply for kw in escape_keywords):
            st.session_state.messages.append({
                "role": "assistant",
                "content": display_reply
            })
            st.chat_message("assistant").markdown(display_reply + "\n\n---\n\n🎮 **逃脱结局 — 你成功逃离了欧利蒂丝庄园！**")
            st.balloons()
            st.stop()

    # 保存AI消息（不含 <STATE> 块）
    st.session_state.messages.append({
        "role": "assistant",
        "content": display_reply
    })

    # game_log
    st.session_state.game_log.append({
        "step": current_step,
        "player_input": prompt,
        "location": st.session_state.location,
        "sanity": st.session_state.sanity,
        "actions_left": st.session_state.actions_left,
        "ai_reply": display_reply
    })

    # 重新运行，让历史循环统一渲染所有消息（避免重复显示）
    st.rerun()
