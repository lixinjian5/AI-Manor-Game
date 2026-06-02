import json
from ._api import call

PROMPT = """你是一个谋杀推理游戏的剧本生成器。根据以下角色数据和世界观，生成一个**完整的谋杀推理剧本**。

# 角色数据
{characters}

# 世界观
{world}

# 要求

1. 从角色中选择**一名作为死者**，**另一名作为真凶**（必须有合理动机，基于角色关系网）
2. 设计作案手法和时间线
3. 在每个地点分布 1-2 条线索
4. 为每个存活NPC设计证词：包括公开说辞、隐瞒的信息、以及一个与案件无关的私人秘密
5. 剧情要有反转——表象之下另有真相
6. 动机必须基于角色之间的真实关系（仇敌/背叛/利益冲突）

# 输出格式（严格按此结构）

【谋杀剧本】
死者：<角色名>
真凶：<角色名>
动机：<一句话描述凶手为何杀人>
手法：<作案手法描述>
案发地点：<庄园中的地点>
时间线：<案发经过的时间顺序>

【关键线索】
- <地点名>：<线索描述>
- <地点名>：<线索描述>
...

【NPC证词】
<角色名>：
  公开说辞：<对外声称的内容>
  隐瞒：<与案件有关但不想说的事>
  秘密：<与案件无关的私人秘密>
<角色名>：
  ...

【真相反转】
<玩家最初会怀疑A，但真正的凶手是B。描述误导线索和真相的对比>

请确保输出包含"【谋杀剧本】"、"【关键线索】"、"【NPC证词】"、"【真相反转】"四个标记，其中"真凶："字段必须存在。
"""


def generate_mystery(api_key: str, characters: dict, world_setting: str) -> str:
    """Generate a murder mystery script using DeepSeek API.

    Returns the mystery script as a semi-structured text.
    The script contains markers like '真凶：<name>' for later parsing.
    """
    messages = [
        {
            "role": "system",
            "content": "你是一个悬疑推理剧本作家，擅长设计密室谋杀谜题。你严格基于给定的角色数据创作，不使用外部设定。",
        },
        {
            "role": "user",
            "content": PROMPT.format(
                characters=json.dumps(characters, ensure_ascii=False, indent=2),
                world=world_setting,
            ),
        },
    ]
    return call(api_key, messages, timeout=90)
