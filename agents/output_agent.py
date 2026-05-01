import sys
import os
import json
from datetime import datetime

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─────────────────────────────────────────────
# OUTPUT AGENT
# ─────────────────────────────────────────────

class OutputAgent:
    """
    Agent 6 — Output Agent
    ───────────────────────
    Input  : All formatted platform outputs from FormatterAgent (list)
    Output : Final bundled JSON written to output.json

    Responsibilities:
    - No LLM calls — pure data assembly
    - Bundle all hook results + platform outputs into one clean JSON
    - Compute summary metadata (avg score, total iterations, pass rate)
    - Write output.json for frontend to read
    - Print clean summary to terminal
    """

    def __init__(self):
        self.name = "Output Agent"
        self.output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "output.json"
        )

    def _compute_metadata(self, formatted_outputs: list, ingestion_data: dict) -> dict:
        """
        Compute summary stats across all hooks.
        """
        total_hooks       = len(formatted_outputs)
        passed            = sum(1 for h in formatted_outputs if h.get("passed_threshold", False))
        total_iterations  = sum(h.get("total_attempts", 0) for h in formatted_outputs)
        scores            = [h.get("final_score", 0) for h in formatted_outputs]
        avg_score         = round(sum(scores) / total_hooks, 1) if total_hooks > 0 else 0
        highest_score     = max(scores) if scores else 0
        lowest_score      = min(scores) if scores else 0

        return {
            "processed_at"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_url"        : ingestion_data.get("source_url", ""),
            "video_title"       : ingestion_data.get("title", "Unknown"),
            "video_uploader"    : ingestion_data.get("uploader", "Unknown"),
            "video_duration"    : ingestion_data.get("duration_formatted", "Unknown"),
            "total_hooks"       : total_hooks,
            "hooks_passed"      : passed,
            "hooks_failed"      : total_hooks - passed,
            "pass_rate"         : f"{round((passed / total_hooks) * 100)}%" if total_hooks > 0 else "0%",
            "total_rewrites"    : total_iterations,
            "avg_final_score"   : avg_score,
            "highest_score"     : highest_score,
            "lowest_score"      : lowest_score,
        }

    def _build_hook_summary(self, hook: dict) -> dict:
        """
        Build a clean summary for a single hook.
        """
        return {
            "hook_id"           : hook.get("hook_id", 0),
            "timestamp"         : hook.get("timestamp", ""),
            "final_score"       : hook.get("final_score", 0),
            "passed_threshold"  : hook.get("passed_threshold", False),
            "total_attempts"    : hook.get("total_attempts", 0),
            "tiktok"            : hook.get("tiktok", {}),
            "linkedin"          : hook.get("linkedin", {}),
            "twitter"           : hook.get("twitter", {}),
            "warnings"          : hook.get("warnings", [])
        }

    def _print_terminal_summary(self, metadata: dict, hooks: list):
        """
        Print a clean readable summary to terminal after pipeline completes.
        """
        print(f"\n{'='*60}")
        print(f"  PIPELINE COMPLETE — {self.name}")
        print(f"{'='*60}")
        print(f"  Video     : {metadata['video_title']}")
        print(f"  Uploader  : {metadata['video_uploader']}")
        print(f"  Duration  : {metadata['video_duration']}")
        print(f"  URL       : {metadata['source_url']}")
        print(f"{'─'*60}")
        print(f"  Hooks processed : {metadata['total_hooks']}")
        print(f"  Passed (≥75)    : {metadata['hooks_passed']} ({metadata['pass_rate']})")
        print(f"  Total rewrites  : {metadata['total_rewrites']}")
        print(f"  Avg final score : {metadata['avg_final_score']}/100")
        print(f"  Highest score   : {metadata['highest_score']}/100")
        print(f"  Lowest score    : {metadata['lowest_score']}/100")
        print(f"{'─'*60}")

        for hook in hooks:
            status = "✅ PASSED" if hook["passed_threshold"] else "⚠ MAX ITER"
            print(f"  Hook {hook['hook_id']} @ [{hook['timestamp']}] — {hook['final_score']}/100 — {status}")
            print(f"    TikTok  : {hook['tiktok'].get('caption', '')[:55]}...")
            print(f"    LinkedIn: {hook['linkedin'].get('hook_line', '')[:55]}...")
            print(f"    Twitter : {hook['twitter'].get('tweet', '')[:55]}...")

        print(f"{'='*60}")
        print(f"  Output saved to : output.json")
        print(f"  Processed at    : {metadata['processed_at']}")
        print(f"{'='*60}\n")

    def run(self, formatted_outputs: list, ingestion_data: dict = None) -> dict:
        """
        Main entry point for output agent.
        Bundles everything, writes output.json, prints summary.
        """
        print(f"\n{'='*50}")
        print(f"[{self.name}] Starting...")
        print(f"[{self.name}] Bundling {len(formatted_outputs)} hooks...")
        print(f"{'='*50}")

        if not formatted_outputs:
            raise ValueError(f"[{self.name}] No formatted outputs to bundle.")

        if ingestion_data is None:
            ingestion_data = {}

        # Step 1: Compute metadata
        metadata = self._compute_metadata(formatted_outputs, ingestion_data)

        # Step 2: Build hook summaries
        hook_summaries = [self._build_hook_summary(h) for h in formatted_outputs]

        # Step 3: Build final output bundle
        final_output = {
            "metadata"  : metadata,
            "hooks"     : hook_summaries
        }

        # Step 4: Write to output.json
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        print(f"[{self.name}] output.json written to: {self.output_path}")

        # Step 5: Print terminal summary
        self._print_terminal_summary(metadata, hook_summaries)

        return final_output


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    mock_ingestion = {
        "title"              : "How I Made $50K in a Week",
        "uploader"           : "Test Channel",
        "duration_formatted" : "12m 30s",
        "source_url"         : "https://youtube.com/watch?v=test"
    }

    mock_formatted = [
        {
            "hook_id"           : 1,
            "timestamp"         : "00:45",
            "final_score"       : 82,
            "total_attempts"    : 2,
            "passed_threshold"  : True,
            "video_title"       : "How I Made $50K in a Week",
            "source_url"        : "https://youtube.com/watch?v=test",
            "tiktok"  : {
                "hook_line" : "I turned $200 into $50K in 7 days.",
                "caption"   : "Nobody believed me until I showed receipts. Here's exactly how.",
                "hashtags"  : ["#money", "#sidehustle", "#viral"]
            },
            "linkedin": {
                "hook_line" : "Most people overcomplicate making money online.",
                "caption"   : "I kept it stupidly simple. $200 turned into $50,000 in 7 days. Here's the method step by step.",
                "hashtags"  : ["#entrepreneurship", "#finance", "#growth"],
                "cta"       : "Have you tried this approach? What was your experience?"
            },
            "twitter" : {
                "tweet"  : "I turned $200 into $50K in 7 days. Nobody believed me until I showed the receipts.",
                "thread" : [
                    "I turned $200 into $50K in 7 days. Nobody believed me until I showed the receipts.",
                    "Here's the method step by step...",
                    "The biggest mistake people make is overcomplicating it.",
                    "Keep it simple. Stay consistent. Show up every day."
                ]
            },
            "warnings": []
        },
        {
            "hook_id"           : 2,
            "timestamp"         : "07:15",
            "final_score"       : 81,
            "total_attempts"    : 0,
            "passed_threshold"  : True,
            "video_title"       : "How I Made $50K in a Week",
            "source_url"        : "https://youtube.com/watch?v=test",
            "tiktok"  : {
                "hook_line" : "I almost quit three times.",
                "caption"   : "This is what kept me going when nothing was working.",
                "hashtags"  : ["#motivation", "#entrepreneur", "#mindset"]
            },
            "linkedin": {
                "hook_line" : "Everyone talks about the wins. Nobody talks about the nights you almost walked away.",
                "caption"   : "I almost quit three times. Each time something small kept me going. Here's what it was.",
                "hashtags"  : ["#leadership", "#resilience", "#entrepreneurship"],
                "cta"       : "What kept you going when you wanted to quit?"
            },
            "twitter" : {
                "tweet"  : "I almost quit three times. This is what kept me going.",
                "thread" : []
            },
            "warnings": []
        }
    ]

    agent = OutputAgent()

    try:
        result = agent.run(mock_formatted, mock_ingestion)
        print(f"[TEST] Final output keys: {list(result.keys())}")
        print(f"[TEST] output.json successfully created.")

    except Exception as e:
        print(f"\n[ERROR] {e}")