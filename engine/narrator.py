import re
import json
from ._api import call

SYSTEM_PROMPT = """# Role
你是欧利蒂丝庄园的主持人，负责推动这场谋杀推理游戏。你同时扮演旁白和所有NPC。

# 本局谜题（这是"标准答案"，你作为主持人的内部参考，绝不能直接告知玩家）
{mystery_script}

# 角色数据
{characters}

# 世界观
{world}

{memory_context}

# 核心规则
1. 根据玩家的行动推进剧情，NPC的反应必须符合他们的性格
2. 线索要**分散释放**——每次只给出1-2条，让玩家自己拼凑真相
3. NPC会撒谎、隐瞒、或不小心说漏嘴——这是推理的乐趣
4. 保持哥特悬疑氛围，但不要过度渲染恐怖
5. 每次回复控制在200字以内
6. 你知道谁是凶手，但你**绝不能说**——除非玩家正式指认
7. 当玩家接近真相时，NPC的反应会逐渐紧张、失态

# 指认规则
- 当玩家明确说"我指认XXX"或"凶手是XXX"时，这是指认行为
- 此时你必须如实回答：如果指认正确，揭露真相；如果错误，描述后果
- 指认错误时，真凶会趁乱逃脱，所有NPC知道游戏结束

# 氛围
- 维多利亚哥特风格，没有现代科技
- 对话中自然流露角色性格
- 每条线索都是一块拼图
"""


def narrate(
    api_key: str,
    mystery_script: str,
    characters: dict,
    world_setting: str,
    memory,
    player_input: str,
    messages_history: list,
) -> str:
    """Call AI to narrate the next story beat."""

    system_content = SYSTEM_PROMPT.format(
        mystery_script=mystery_script,
        characters=json.dumps(characters, ensure_ascii=False, indent=2),
        world=world_setting,
        memory_context=memory.get_context_for_ai(),
    )

    # messages_history already includes the system prompt and all previous turns
    # But we need to rebuild with the updated system prompt (memory changes each turn)
    msgs = [{"role": "system", "content": system_content}]
    for m in messages_history:
        if m["role"] != "system":
            msgs.append({"role": m["role"], "content": m["content"]})

    return call(api_key, msgs)


def check_accusation(text: str) -> str | None:
    """Detect if the player is accusing someone. Returns the accused name or None."""
    patterns = [
        r"我指认(.+?)(?:是凶手|杀|$)",
        r"凶手是(.+?)(?:[!！。.]|$)",
        r"(.+?)是(?:真)?凶",
        r"我确定.*?(?:就是|是)(.+?)(?:[!！。.]|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None


def parse_killer(mystery_script: str) -> str:
    """Extract the killer's name from the mystery script."""
    m = re.search(r"真凶[：:]\s*(.+)", mystery_script)
    if m:
        return m.group(1).strip()
    return ""


def reveal_case(api_key: str, mystery_script: str) -> str:
    """游戏结束时，根据谜题剧本生成完整案情揭示。"""
    prompt = f"""游戏结束了。请根据以下谜题剧本，以主持人的口吻向玩家揭示完整的案件真相。

剧本：
{mystery_script}

请用以下格式输出（200字以内，哥特风格）：
- 凶手是谁
- 动机是什么
- 作案手法
- 关键证据链"""
    return call(api_key, [{"role": "user", "content": prompt}])
