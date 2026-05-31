import streamlit as st
import requests
import json

st.set_page_config(layout="wide")

url = "https://api.deepseek.com/chat/completions"

headers = {
    "Authorization": "Bearer sk-d054b32f246b45ffbb615bb3de26818d",
    "Content-Type": "application/json"
}

st.title("欧利蒂丝庄园")
st.caption("欢迎来到欧利蒂丝庄园。")

# =========================
# ✅ 1. session_state 统一初始化（关键修复）
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = []

if "location" not in st.session_state:
    st.session_state.location = "大厅"

if "time" not in st.session_state:
    st.session_state.time = "夜晚"

if "sanity" not in st.session_state:
    st.session_state.sanity = 100

if "actions_left" not in st.session_state:
    st.session_state.actions_left = 15


# =========================
# sidebar（安全访问）
# =========================
st.sidebar.title("玩家状态")
st.sidebar.write(f"剩余行动：{st.session_state.actions_left}")
st.sidebar.write(f"当前位置：{st.session_state.location}")
st.sidebar.write(f"当前时间：{st.session_state.time}")
st.sidebar.write(f"理智值：{st.session_state.sanity}")

# =========================
# 读取世界文件
# =========================
with open("map.txt", "r", encoding="UTF-8") as f:
    game_map = f.read()

with open("world.txt", "r", encoding="UTF-8") as f:
    world_background = f.read()

with open("characters.json", "r", encoding="UTF-8") as f:
    characters = json.load(f)

# =========================
# 系统 prompt（原样保留）
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
1. 推进剧情，保持逻辑合理
2. 玩家行为必须符合庄园世界观
3. NPC行为和性格必须保持一致
4. 不允许出现现代网络语言
5. 适当制造悬念和神秘感
6. 每次回复控制在200字以内
7. 给玩家提供可选行动引导

# Output Format
1. 场景环境描写
2. NPC描写
3. NPC行为和互动
4. 玩家状态或反应
5. 给玩家提供至少1-3个行动选项

# 当前状态
庄园世界观：{world_background}
庄园角色资料：{characters}
庄园区域：{game_map}
玩家当前位置：{st.session_state.location}
玩家理智值：{st.session_state.sanity}
剩余行动：{st.session_state.actions_left}
玩家重要行为记录：
{'\n'.join(st.session_state.memory)}
"""
}
def extract_memory(text):
    keywords = ["帮助", "怀疑", "攻击", "逃跑", "相信", "欺骗", "进入", "调查", "发现"]

    for k in keywords:
        if k in text:
            return text
    return None
# =========================
# 开局剧情（不动）
# =========================
if len(st.session_state.messages) == 0:
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

# =========================
# 显示历史消息
# =========================
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# =========================
# 输入
# =========================
prompt = st.chat_input("请输入你的行动")

if prompt:

    # =========================
    # 结束条件
    # =========================
    if st.session_state.actions_left <= 0:
        st.chat_message("assistant").markdown("""
【结局】

钟声再次响起。

庄园的大门缓缓关闭。

你终究没能逃离这里……

游戏结束。
""")
        st.stop()

    st.session_state.actions_left -= 1

    # =========================
    # 地点逻辑（保留）
    # =========================
    if "地下室" in prompt:
        st.session_state.location = "地下室"
        st.session_state.sanity -= 10

    if "花园" in prompt:
        st.session_state.location = "花园"

    if "医务室" in prompt:
        st.session_state.location = "医务室"

    if "大厅" in prompt:
        st.session_state.location = "大厅"

    # =========================
    # 存用户消息
    # =========================
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # =========================
    # 重要记忆系统（不改逻辑）
    # =========================
    memory_item = extract_memory(prompt)
    if memory_item:
        st.session_state.memory.append(memory_item)

    memory_text = "\n".join(st.session_state.memory)

    # =========================
    # 临时 prompt
    # =========================
    temp_messages = [
        {
            "role": "system",
            "content": f"""
你是庄园剧情主持人。

以下是玩家的重要经历：
{memory_text}

请在后续剧情中参考。
"""
        }
    ]

    temp_messages.extend(st.session_state.messages)

    data = {
        "model": "deepseek-chat",
        "messages": temp_messages
    }

    # =========================
    # API 请求（加保护）
    # =========================
    with st.spinner("庄园正在回应你..."):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
        except Exception as e:
            result = {"error": str(e)}

    # =========================
    # AI 回复处理（增强防炸）
    # =========================
    if "choices" in result:
        ai_reply = result["choices"][0]["message"]["content"]
    else:
        ai_reply = "庄园暂时陷入沉寂……请稍后再试。"
        st.write(result)

    # =========================
    # 保存 AI 回复
    # =========================
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_reply
    })

    # =========================
    # 显示 AI
    # =========================
    with st.chat_message("assistant"):
        st.markdown(ai_reply)