class MemoryManager:
    """Layered memory for the murder mystery game.

    Layers (closest to AI → farthest):
      recent  — last N rounds of full conversation text
      summary — AI-compressed summary of older rounds
      facts   — structured list of clues the player has discovered
    """

    MAX_RECENT = 8  # rounds to keep as full text before summarizing

    def __init__(self):
        self.recent: list[dict] = []  # [{"player": ..., "ai": ...}, ...]
        self.summary: str = ""
        self.facts: list[str] = []

    def add_round(self, player_input: str, ai_reply: str):
        self.recent.append({"player": player_input, "ai": ai_reply})
        if len(self.recent) > self.MAX_RECENT:
            # Move oldest rounds to summary as raw text (will be compressed later)
            overflow = self.recent[:-self.MAX_RECENT]
            self.recent = self.recent[-self.MAX_RECENT:]
            for r in overflow:
                self.summary += f"[玩家: {r['player']}] [AI: {r['ai']}]\n"

    def add_fact(self, fact: str):
        if fact not in self.facts:
            self.facts.append(fact)

    def get_context_for_ai(self) -> str:
        """Build the memory section for the system prompt."""
        parts = []
        if self.summary:
            parts.append(f"【早期剧情摘要】\n{self.summary[-2000:]}")  # cap at 2000 chars
        if self.facts:
            parts.append("【玩家已发现的线索】\n" + "\n".join(f"- {f}" for f in self.facts))
        if self.recent:
            parts.append("【最近对话】\n" + "\n".join(
                f"玩家: {r['player']}\n主持人: {r['ai']}" for r in self.recent[-5:]
            ))
        return "\n\n".join(parts)
