import sys
import os
import json

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_config import get_llm_response
from agents.scoring_agent import ScoringAgent

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
SCORE_THRESHOLD = 75   # Minimum score to pass to formatter
MAX_ITERATIONS  = 3    # Maximum rewrite attempts per hook


# ─────────────────────────────────────────────
# REWRITE AGENT
# ─────────────────────────────────────────────

class RewriteAgent:
    """
    Agent 4 — Rewrite Agent (with Feedback Loop)
    ──────────────────────────────────────────────
    Input  : All hooks + their scores from ScoringAgent (list)
    Output : Final approved hooks with full iteration history (list)

    Responsibilities:
    - Part A: Rewrite any hook scoring below SCORE_THRESHOLD
    - Part B: Re-score rewritten hook via ScoringAgent
    - Loop:   Continue until score >= 75 OR 3 attempts reached
    - Log:    Track every iteration with score history
    - Pass:   Send approved hooks to FormatterAgent
    """

    def __init__(self):
        self.name = "Rewrite Agent"
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts", "rewrite_prompt.txt"
        )
        self.prompt = self._load_prompt()
        self.scorer = ScoringAgent()

    def _load_prompt(self) -> str:
        """Load rewrite prompt from file."""
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"[{self.name}] Prompt not found: {self.prompt_path}")
        with open(self.prompt_path, "r") as f:
            return f.read().strip()

    def _parse_rewrite_response(self, response: str, hook_id: int, attempt: int) -> dict:
        """Parse LLM rewrite response into structured dict."""
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"[{self.name}] Failed to parse rewrite response:\n{e}\n\nRaw:\n{response}")

        required = ["rewritten_hook", "rewritten_caption", "changes_made"]
        for field in required:
            if field not in result:
                raise ValueError(f"[{self.name}] Missing field in rewrite response: '{field}'")

        result["hook_id"] = hook_id
        result["attempt"] = attempt

        return result

    # ─────────────────────────────────────────────
    # PART A — REWRITER
    # ─────────────────────────────────────────────

    def rewrite_hook(self, hook: dict, score_result: dict, attempt: int) -> dict:
        """
        Rewrite a single hook using feedback from ScoringAgent.
        Returns rewritten hook dict.
        """
        hook_id = hook.get("id", score_result.get("hook_id", 0))
        original_hook = hook.get("hook", hook.get("rewritten_hook", ""))
        feedback = score_result.get("feedback", "")
        score = score_result.get("score", 0)

        print(f"  [{self.name}] Rewriting hook {hook_id} (attempt {attempt}) — score was {score}/100")
        print(f"  [{self.name}] Feedback: {feedback[:80]}...")

        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": (
                    f"Hook ID: {hook_id}\n"
                    f"Attempt: {attempt}\n\n"
                    f"ORIGINAL HOOK:\n{original_hook}\n\n"
                    f"VIRALITY SCORE: {score}/100\n\n"
                    f"FEEDBACK (fix exactly this):\n{feedback}\n\n"
                    f"SCORE BREAKDOWN:\n{json.dumps(score_result.get('breakdown', {}), indent=2)}"
                )
            }
        ]

        raw_response = get_llm_response(messages, temperature=0.7)
        rewrite = self._parse_rewrite_response(raw_response, hook_id, attempt)

        print(f"  [{self.name}] Rewrite done: {rewrite['rewritten_hook'][:60]}...")

        return rewrite

    # ─────────────────────────────────────────────
    # PART B — LOOP CONTROLLER
    # ─────────────────────────────────────────────

    def process_hook(self, hook: dict, initial_score: dict) -> dict:
        """
        Full loop for a single hook:
        Score → if < 75 rewrite → re-score → repeat max 3 times.

        Returns final approved hook with full iteration history.
        """
        hook_id = hook.get("id", 0)
        current_hook = hook.copy()
        current_score = initial_score

        iteration_log = []

        # Log initial state
        iteration_log.append({
            "attempt": 0,
            "hook_text": current_hook.get("hook", ""),
            "score": current_score["score"],
            "breakdown": current_score["breakdown"],
            "feedback": current_score["feedback"],
            "action": "initial_score"
        })

        print(f"\n  [{self.name}] Hook {hook_id} initial score: {current_score['score']}/100")

        # ── LOOP ──
        for attempt in range(1, MAX_ITERATIONS + 1):

            if current_score["score"] >= SCORE_THRESHOLD:
                print(f"  [{self.name}] Hook {hook_id} passed threshold ({current_score['score']}/100). Moving on.")
                break

            print(f"  [{self.name}] Score {current_score['score']} < {SCORE_THRESHOLD}. Rewriting (attempt {attempt}/{MAX_ITERATIONS})...")

            # Part A: Rewrite
            rewrite = self.rewrite_hook(current_hook, current_score, attempt)

            # Update current hook with rewritten version
            current_hook = {
                "id": hook_id,
                "hook": rewrite["rewritten_hook"],
                "rewritten_hook": rewrite["rewritten_hook"],
                "rewritten_caption": rewrite["rewritten_caption"],
                "timestamp": hook.get("timestamp", ""),
                "emotion": hook.get("emotion", ""),
                "video_title": hook.get("video_title", ""),
                "source_url": hook.get("source_url", "")
            }

            # Part B: Re-score
            current_score = self.scorer.score_hook(current_hook)

            # Log this iteration
            iteration_log.append({
                "attempt": attempt,
                "hook_text": rewrite["rewritten_hook"],
                "caption": rewrite["rewritten_caption"],
                "changes_made": rewrite["changes_made"],
                "score": current_score["score"],
                "breakdown": current_score["breakdown"],
                "feedback": current_score["feedback"],
                "action": "rewrite"
            })

            print(f"  [{self.name}] After rewrite {attempt}: {current_score['score']}/100")

        # ── FINAL RESULT ──
        passed = current_score["score"] >= SCORE_THRESHOLD
        status = "passed" if passed else "max_iterations_reached"

        print(f"  [{self.name}] Hook {hook_id} final: {current_score['score']}/100 — {status}")

        return {
            "hook_id": hook_id,
            "original_hook": hook.get("hook", ""),
            "final_hook": current_hook.get("hook", ""),
            "final_caption": current_hook.get("rewritten_caption", ""),
            "final_score": current_score["score"],
            "final_breakdown": current_score["breakdown"],
            "timestamp": hook.get("timestamp", ""),
            "emotion": hook.get("emotion", ""),
            "video_title": hook.get("video_title", ""),
            "source_url": hook.get("source_url", ""),
            "total_attempts": len(iteration_log) - 1,
            "passed_threshold": passed,
            "status": status,
            "iteration_log": iteration_log
        }

    # ─────────────────────────────────────────────
    # MAIN RUN
    # ─────────────────────────────────────────────

    def run(self, hooks: list, scores: list) -> list:
        """
        Process all hooks through the rewrite loop.
        Takes hooks from HookAgent and scores from ScoringAgent.
        Returns list of final approved hooks.
        """
        print(f"\n{'='*50}")
        print(f"[{self.name}] Starting...")
        print(f"[{self.name}] Hooks to process: {len(hooks)}")
        print(f"[{self.name}] Threshold: {SCORE_THRESHOLD}/100 | Max iterations: {MAX_ITERATIONS}")
        print(f"{'='*50}")

        if len(hooks) != len(scores):
            raise ValueError(
                f"[{self.name}] Hooks count ({len(hooks)}) != Scores count ({len(scores)})"
            )

        final_hooks = []

        for hook, score in zip(hooks, scores):
            result = self.process_hook(hook, score)
            final_hooks.append(result)

        # ── SUMMARY ──
        passed = sum(1 for h in final_hooks if h["passed_threshold"])
        avg_final = sum(h["final_score"] for h in final_hooks) / len(final_hooks)
        total_rewrites = sum(h["total_attempts"] for h in final_hooks)

        print(f"\n[{self.name}] All hooks processed.")
        print(f"[{self.name}] Passed threshold : {passed}/{len(final_hooks)}")
        print(f"[{self.name}] Avg final score  : {avg_final:.1f}/100")
        print(f"[{self.name}] Total rewrites    : {total_rewrites}")

        return final_hooks


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mock_hooks = [
        {
            "id": 1,
            "timestamp": "00:45",
            "hook": "I made money using a method.",
            "emotion": "curiosity",
            "video_title": "Test Video",
            "source_url": "https://youtube.com/watch?v=test"
        },
        {
            "id": 2,
            "timestamp": "07:15",
            "hook": "I almost quit three times. This is what kept me going.",
            "emotion": "inspiration",
            "video_title": "Test Video",
            "source_url": "https://youtube.com/watch?v=test"
        }
    ]

    mock_scores = [
        {
            "hook_id": 1,
            "score": 48,
            "breakdown": {
                "emotional_trigger": 10,
                "curiosity_gap": 12,
                "relatability": 14,
                "platform_fit": 12
            },
            "feedback": "Too vague. 'Made money' triggers no curiosity. Add a specific number or unexpected twist."
        },
        {
            "hook_id": 2,
            "score": 81,
            "breakdown": {
                "emotional_trigger": 22,
                "curiosity_gap": 20,
                "relatability": 21,
                "platform_fit": 18
            },
            "feedback": "Strong open loop and emotional vulnerability. Platform fit slightly weak for LinkedIn."
        }
    ]

    agent = RewriteAgent()

    try:
        results = agent.run(mock_hooks, mock_scores)

        print(f"\n=== REWRITE AGENT OUTPUT ===")
        for r in results:
            print(f"\nHook {r['hook_id']}:")
            print(f"  Original    : {r['original_hook']}")
            print(f"  Final       : {r['final_hook']}")
            print(f"  Final Score : {r['final_score']}/100")
            print(f"  Attempts    : {r['total_attempts']}")
            print(f"  Status      : {r['status']}")

    except Exception as e:
        print(f"\n[ERROR] {e}")