import sys
import os
import json

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_config import get_llm_response

# ─────────────────────────────────────────────
# FORMATTER AGENT
# ─────────────────────────────────────────────

class FormatterAgent:
    """
    Agent 5 — Platform Formatter Agent
    ────────────────────────────────────
    Input  : Final approved hooks from RewriteAgent (list)
    Output : Platform-ready content for TikTok, LinkedIn, Twitter/X (list)

    Responsibilities:
    - Load formatter_prompt.txt
    - Format each approved hook for all 3 platforms
    - Follow strict platform rules (tone, length, hashtags, CTA)
    - Return structured platform output per hook
    """

    def __init__(self):
        self.name = "Formatter Agent"
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "prompts", "formatter_prompt.txt"
        )
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load formatter prompt from file."""
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"[{self.name}] Prompt not found: {self.prompt_path}")
        with open(self.prompt_path, "r") as f:
            return f.read().strip()

    def _parse_response(self, response: str, hook_id: int) -> dict:
        """
        Parse LLM formatter response into structured dict.
        Validates all 3 platform outputs exist.
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
            raise ValueError(f"[{self.name}] Failed to parse formatter response:\n{e}\n\nRaw:\n{response}")

        # Validate all 3 platforms exist
        required_platforms = ["tiktok", "linkedin", "twitter"]
        for platform in required_platforms:
            if platform not in result:
                raise ValueError(f"[{self.name}] Missing platform in response: '{platform}'")

        # Validate TikTok fields
        tiktok_fields = ["hook_line", "caption", "hashtags"]
        for field in tiktok_fields:
            if field not in result["tiktok"]:
                raise ValueError(f"[{self.name}] Missing TikTok field: '{field}'")

        # Validate LinkedIn fields
        linkedin_fields = ["hook_line", "caption", "hashtags", "cta"]
        for field in linkedin_fields:
            if field not in result["linkedin"]:
                raise ValueError(f"[{self.name}] Missing LinkedIn field: '{field}'")

        # Validate Twitter fields
        twitter_fields = ["tweet", "thread"]
        for field in twitter_fields:
            if field not in result["twitter"]:
                raise ValueError(f"[{self.name}] Missing Twitter field: '{field}'")

        # Force correct hook_id
        result["hook_id"] = hook_id

        return result

    def _validate_platform_limits(self, result: dict) -> dict:
        """
        Enforce character limits per platform.
        Truncates if over limit and flags it.
        """
        warnings = []

        # TikTok caption — 150 chars max
        tiktok_caption = result["tiktok"]["caption"]
        if len(tiktok_caption) > 150:
            result["tiktok"]["caption"] = tiktok_caption[:147] + "..."
            warnings.append("TikTok caption truncated to 150 chars")

        # Twitter single tweet — 280 chars max
        tweet = result["twitter"]["tweet"]
        if len(tweet) > 280:
            result["twitter"]["tweet"] = tweet[:277] + "..."
            warnings.append("Twitter tweet truncated to 280 chars")

        if warnings:
            result["warnings"] = warnings
            for w in warnings:
                print(f"  [{self.name}] ⚠ {w}")

        return result

    def format_hook(self, hook: dict) -> dict:
        """
        Format a single approved hook for all 3 platforms.
        Returns full platform output dict.
        """
        hook_id = hook.get("hook_id", hook.get("id", 0))
        final_hook = hook.get("final_hook", hook.get("hook", ""))
        final_caption = hook.get("final_caption", "")
        final_score = hook.get("final_score", hook.get("score", 0))
        timestamp = hook.get("timestamp", "")
        emotion = hook.get("emotion", "")

        print(f"  [{self.name}] Formatting hook {hook_id} @ [{timestamp}] (score: {final_score}/100)")

        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": (
                    f"Hook ID: {hook_id}\n"
                    f"Timestamp: {timestamp}\n"
                    f"Emotion: {emotion}\n"
                    f"Virality Score: {final_score}/100\n\n"
                    f"APPROVED HOOK:\n{final_hook}\n\n"
                    f"CAPTION:\n{final_caption if final_caption else 'No caption provided — generate one.'}"
                )
            }
        ]

        raw_response = get_llm_response(messages, temperature=0.6)
        result = self._parse_response(raw_response, hook_id)
        result = self._validate_platform_limits(result)

        print(f"  [{self.name}] Hook {hook_id} formatted for TikTok, LinkedIn, Twitter.")

        return result

    def run(self, approved_hooks: list) -> list:
        """
        Format all approved hooks from RewriteAgent.
        Returns list of platform-ready content dicts.
        """
        print(f"\n{'='*50}")
        print(f"[{self.name}] Starting...")
        print(f"[{self.name}] Hooks to format: {len(approved_hooks)}")
        print(f"{'='*50}")

        if not approved_hooks:
            raise ValueError(f"[{self.name}] No approved hooks to format.")

        formatted_outputs = []

        for hook in approved_hooks:
            result = self.format_hook(hook)

            # Attach metadata
            result["source_url"] = hook.get("source_url", "")
            result["video_title"] = hook.get("video_title", "")
            result["timestamp"] = hook.get("timestamp", "")
            result["final_score"] = hook.get("final_score", 0)
            result["total_attempts"] = hook.get("total_attempts", 0)
            result["passed_threshold"] = hook.get("passed_threshold", False)

            formatted_outputs.append(result)

        print(f"\n[{self.name}] All hooks formatted.")
        print(f"[{self.name}] Total outputs: {len(formatted_outputs)}")

        return formatted_outputs


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mock_approved_hooks = [
        {
            "hook_id": 1,
            "original_hook": "I made money using a method.",
            "final_hook": "I turned $200 into $50,000 in 7 days — and nobody believed me until I showed the receipts.",
            "final_caption": "Most people overcomplicate making money online. I kept it stupidly simple, and it worked. Here's the exact method.",
            "final_score": 82,
            "timestamp": "00:45",
            "emotion": "curiosity",
            "video_title": "How I Made $50K in a Week",
            "source_url": "https://youtube.com/watch?v=test",
            "total_attempts": 2,
            "passed_threshold": True,
            "status": "passed"
        },
        {
            "hook_id": 2,
            "original_hook": "I almost quit three times. This is what kept me going.",
            "final_hook": "I almost quit three times. This is what kept me going.",
            "final_caption": "Everyone talks about the wins. Nobody talks about the nights you almost walked away.",
            "final_score": 81,
            "timestamp": "07:15",
            "emotion": "inspiration",
            "video_title": "How I Made $50K in a Week",
            "source_url": "https://youtube.com/watch?v=test",
            "total_attempts": 0,
            "passed_threshold": True,
            "status": "passed"
        }
    ]

    agent = FormatterAgent()

    try:
        results = agent.run(mock_approved_hooks)

        print(f"\n=== FORMATTER AGENT OUTPUT ===")
        for r in results:
            print(f"\nHook {r['hook_id']}:")
            print(f"  TikTok    : {r['tiktok']['caption'][:60]}...")
            print(f"  LinkedIn  : {r['linkedin']['caption'][:60]}...")
            print(f"  Twitter   : {r['twitter']['tweet'][:60]}...")
            if r.get("warnings"):
                print(f"  Warnings  : {r['warnings']}")

    except Exception as e:
        print(f"\n[ERROR] {e}")