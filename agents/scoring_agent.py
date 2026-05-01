import sys
import os
import json

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_config import get_llm_response

# ─────────────────────────────────────────────
# SCORING AGENT
# ─────────────────────────────────────────────

class ScoringAgent:
    """
    Agent 3 — Virality Scoring Agent
    ──────────────────────────────────
    Input  : Single hook dict from HookAgent (or RewriteAgent)
    Output : Score result dict with breakdown + feedback

    Responsibilities:
    - Load scoring_prompt.txt
    - Score each hook individually on 4 criteria (0-25 each)
    - Return total score (0-100) + actionable feedback
    - Called per hook, and again after each rewrite
    """

    def __init__(self):
        self.name = "Scoring Agent"
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts", "scoring_prompt.txt"
        )
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load scoring rubric prompt from file."""
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"[{self.name}] Prompt not found: {self.prompt_path}")
        with open(self.prompt_path, "r") as f:
            return f.read().strip()

    def _parse_response(self, response: str, hook_id: int) -> dict:
        """
        Parse LLM JSON response into scoring result.
        Handles markdown code blocks and validates fields.
        """
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"[{self.name}] Failed to parse scoring response:\n{e}\n\nRaw:\n{response}")

        # Validate required fields
        required = ["score", "breakdown", "feedback"]
        for field in required:
            if field not in result:
                raise ValueError(f"[{self.name}] Missing field in scoring response: '{field}'")

        # Validate breakdown fields
        breakdown_fields = ["emotional_trigger", "curiosity_gap", "relatability", "platform_fit"]
        for field in breakdown_fields:
            if field not in result["breakdown"]:
                raise ValueError(f"[{self.name}] Missing breakdown field: '{field}'")

        # Force correct hook_id
        result["hook_id"] = hook_id

        # Validate score range
        score = result["score"]
        if not (0 <= score <= 100):
            raise ValueError(f"[{self.name}] Score out of range: {score}")

        return result

    def score_hook(self, hook: dict, caption: str = "") -> dict:
        """
        Score a single hook. Returns full scoring result.

        hook    : Hook dict from HookAgent or RewriteAgent
        caption : Optional caption text to score alongside hook
        """
        hook_id = hook.get("id", 0)
        hook_text = hook.get("hook", hook.get("rewritten_hook", ""))

        if not hook_text:
            raise ValueError(f"[{self.name}] Hook text is empty for hook_id: {hook_id}")

        print(f"[{self.name}] Scoring hook {hook_id}: {hook_text[:60]}...")

        # Build user message
        user_content = (
            f"Hook ID: {hook_id}\n"
            f"Hook Text: {hook_text}\n"
        )
        if caption:
            user_content += f"Caption: {caption}\n"

        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ]

        # Call LLM
        raw_response = get_llm_response(messages, temperature=0.3)

        # Parse and return
        result = self._parse_response(raw_response, hook_id)

        print(f"[{self.name}] Hook {hook_id} scored: {result['score']}/100")
        print(f"[{self.name}] Breakdown — ET:{result['breakdown']['emotional_trigger']} | CG:{result['breakdown']['curiosity_gap']} | R:{result['breakdown']['relatability']} | PF:{result['breakdown']['platform_fit']}")
        print(f"[{self.name}] Feedback: {result['feedback'][:80]}...")

        return result

    def run(self, hooks: list) -> list:
        """
        Score all hooks from HookAgent.
        Returns list of scoring results in same order.
        """
        print(f"\n{'='*50}")
        print(f"[{self.name}] Starting...")
        print(f"[{self.name}] Hooks to score: {len(hooks)}")
        print(f"{'='*50}")

        if not hooks:
            raise ValueError(f"[{self.name}] No hooks provided to score.")

        results = []
        for hook in hooks:
            result = self.score_hook(hook)
            results.append(result)

        # Summary
        avg_score = sum(r["score"] for r in results) / len(results)
        print(f"\n[{self.name}] All hooks scored.")
        print(f"[{self.name}] Average score: {avg_score:.1f}/100")

        return results


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mock_hooks = [
        {
            "id": 1,
            "timestamp": "00:45",
            "hook": "I made $50,000 in one week using a method nobody talks about.",
            "reason": "Bold financial claim creates curiosity",
            "emotion": "curiosity"
        },
        {
            "id": 2,
            "timestamp": "02:10",
            "hook": "The moment I stopped caring about what people thought, everything changed.",
            "reason": "Relatable turning point with emotional weight",
            "emotion": "inspiration"
        },
        {
            "id": 3,
            "timestamp": "07:15",
            "hook": "I almost quit three times. This is what kept me going.",
            "reason": "Vulnerability + open loop forces viewer to keep watching",
            "emotion": "inspiration"
        }
    ]

    agent = ScoringAgent()

    try:
        results = agent.run(mock_hooks)

        print(f"\n=== SCORING AGENT OUTPUT ===")
        for r in results:
            print(f"\nHook {r['hook_id']}:")
            print(f"  Score     : {r['score']}/100")
            print(f"  Breakdown : {r['breakdown']}")
            print(f"  Feedback  : {r['feedback']}")

    except Exception as e:
        print(f"\n[ERROR] {e}")