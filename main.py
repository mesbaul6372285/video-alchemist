import sys
import os
import argparse
import time

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ingestion_agent  import IngestionAgent
from agents.hook_agent       import HookAgent
from agents.scoring_agent    import ScoringAgent
from agents.rewrite_agent    import RewriteAgent
from agents.formatter_agent  import FormatterAgent
from agents.output_agent     import OutputAgent

# ─────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────

class VideoAlchemistPipeline:
    """
    Master pipeline — connects all 6 agents in sequence.

    Flow:
    URL
     → Agent 1: IngestionAgent  (download + transcribe)
     → Agent 2: HookAgent       (extract 3-5 viral hooks)
     → Agent 3: ScoringAgent    (score each hook 0-100)
     → Agent 4: RewriteAgent    (rewrite loop until score ≥ 75)
     → Agent 5: FormatterAgent  (format for TikTok, LinkedIn, Twitter)
     → Agent 6: OutputAgent     (bundle + write output.json)
    """

    def __init__(self):
        self.ingestion_agent  = IngestionAgent()
        self.hook_agent       = HookAgent()
        self.scoring_agent    = ScoringAgent()
        self.rewrite_agent    = RewriteAgent()
        self.formatter_agent  = FormatterAgent()
        self.output_agent     = OutputAgent()

        self.pipeline_log     = []
        self.start_time       = None

    def _log_step(self, step: int, name: str, status: str, duration: float):
        """Log each agent step with timing."""
        entry = {
            "step"     : step,
            "agent"    : name,
            "status"   : status,
            "duration" : f"{duration:.2f}s"
        }
        self.pipeline_log.append(entry)
        print(f"\n[Pipeline] Step {step}/6 — {name} — {status} ({duration:.2f}s)")

    def _print_header(self, url: str):
        print(f"\n{'#'*60}")
        print(f"  AGENTIC VIDEO ALCHEMIST 2.0")
        print(f"  Multi-Agent Viral Content Pipeline")
        print(f"{'#'*60}")
        print(f"  URL: {url}")
        print(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}\n")

    def _print_pipeline_summary(self):
        total = time.time() - self.start_time
        print(f"\n{'─'*60}")
        print(f"  PIPELINE TIMING SUMMARY")
        print(f"{'─'*60}")
        for entry in self.pipeline_log:
            status_icon = "✅" if entry["status"] == "success" else "❌"
            print(f"  {status_icon} Step {entry['step']}: {entry['agent']:<25} {entry['duration']}")
        print(f"{'─'*60}")
        print(f"  Total time: {total:.2f}s")
        print(f"{'─'*60}\n")

    def run(self, url: str) -> dict:
        """
        Run the full pipeline from URL to output.json.
        Returns final output dict.
        """
        self._print_header(url)
        self.start_time = time.time()

        # ── STEP 1: INGESTION ──────────────────────
        t = time.time()
        try:
            ingestion_output = self.ingestion_agent.run(url)
            self._log_step(1, "Ingestion Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(1, "Ingestion Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Ingestion failed: {e}")

        # ── STEP 2: HOOK EXTRACTION ────────────────
        t = time.time()
        try:
            hooks = self.hook_agent.run(ingestion_output)
            self._log_step(2, "Hook Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(2, "Hook Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Hook extraction failed: {e}")

        # ── STEP 3: VIRALITY SCORING ───────────────
        t = time.time()
        try:
            scores = self.scoring_agent.run(hooks)
            self._log_step(3, "Scoring Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(3, "Scoring Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Scoring failed: {e}")

        # ── STEP 4: REWRITE LOOP ───────────────────
        t = time.time()
        try:
            approved_hooks = self.rewrite_agent.run(hooks, scores)
            self._log_step(4, "Rewrite Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(4, "Rewrite Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Rewrite loop failed: {e}")

        # ── STEP 5: PLATFORM FORMATTING ───────────
        t = time.time()
        try:
            formatted_outputs = self.formatter_agent.run(approved_hooks)
            self._log_step(5, "Formatter Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(5, "Formatter Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Formatting failed: {e}")

        # ── STEP 6: OUTPUT BUNDLE ──────────────────
        t = time.time()
        try:
            final_output = self.output_agent.run(formatted_outputs, ingestion_output)
            self._log_step(6, "Output Agent", "success", time.time() - t)
        except Exception as e:
            self._log_step(6, "Output Agent", "failed", time.time() - t)
            raise RuntimeError(f"[Pipeline] Output bundling failed: {e}")

        # ── TIMING SUMMARY ─────────────────────────
        self._print_pipeline_summary()

        return final_output


# ─────────────────────────────────────────────
# IMPORTABLE FUNCTION (used by frontend/app.py)
# ─────────────────────────────────────────────

def run_pipeline(url: str) -> dict:
    """
    Single importable function for Streamlit frontend.
    Usage: from main import run_pipeline
    """
    pipeline = VideoAlchemistPipeline()
    return pipeline.run(url)


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agentic Video Alchemist 2.0 — Viral Content Pipeline"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="YouTube or Twitch video URL to process"
    )

    args = parser.parse_args()

    if not args.url:
        print("[Error] Please provide a URL with --url")
        sys.exit(1)

    try:
        result = run_pipeline(args.url)
        print(f"\n[Done] Pipeline completed successfully.")
        print(f"[Done] output.json is ready for the frontend.")
    except Exception as e:
        print(f"\n[Pipeline Error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()