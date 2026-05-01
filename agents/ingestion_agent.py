import sys
import os

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.yt_downloader import process_url, cleanup_audio

# ─────────────────────────────────────────────
# INGESTION AGENT
# ─────────────────────────────────────────────

class IngestionAgent:
    """
    Agent 1 — Ingestion Agent
    ─────────────────────────
    Input  : YouTube or Twitch URL (string)
    Output : Structured transcript data (dict)

    Responsibilities:
    - Validate the URL
    - Call yt_downloader to download + transcribe
    - Return clean structured output for Hook Agent
    """

    def __init__(self):
        self.name = "Ingestion Agent"

    def validate_url(self, url: str) -> bool:
        """Basic URL validation for supported platforms."""
        supported = [
            "youtube.com/watch",
            "youtu.be/",
            "twitch.tv/",
            "youtube.com/live"
        ]
        return any(platform in url for platform in supported)

    def run(self, url: str) -> dict:
        """
        Main entry point for the ingestion agent.
        Returns structured transcript data.
        """
        print(f"\n{'='*50}")
        print(f"[{self.name}] Starting...")
        print(f"[{self.name}] URL: {url}")
        print(f"{'='*50}")

        # Step 1: Validate URL
        if not url or not url.startswith("http"):
            raise ValueError(f"[{self.name}] Invalid URL: {url}")

        if not self.validate_url(url):
            raise ValueError(
                f"[{self.name}] Unsupported platform. Supported: YouTube, Twitch"
            )

        # Step 2: Download + Transcribe
        print(f"[{self.name}] Downloading and transcribing...")
        raw_data = process_url(url)

        # Step 3: Validate we got usable transcript
        if not raw_data.get("segments") or len(raw_data["segments"]) == 0:
            raise RuntimeError(f"[{self.name}] Transcript is empty. Cannot proceed.")

        # Step 4: Build structured output
        output = {
            "status": "success",
            "agent": self.name,
            "title": raw_data["title"],
            "uploader": raw_data["uploader"],
            "duration_seconds": raw_data["duration_seconds"],
            "duration_formatted": raw_data["duration_formatted"],
            "source_url": url,
            "segments": raw_data["segments"],
            "total_segments": raw_data["total_segments"]
        }

        print(f"[{self.name}] Done.")
        print(f"[{self.name}] Title    : {output['title']}")
        print(f"[{self.name}] Duration : {output['duration_formatted']}")
        print(f"[{self.name}] Segments : {output['total_segments']}")

        # Cleanup downloaded audio
        cleanup_audio()

        return output


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    url = input("Enter YouTube/Twitch URL: ").strip()

    agent = IngestionAgent()

    try:
        result = agent.run(url)

        print(f"\n=== INGESTION AGENT OUTPUT ===")
        print(f"Title     : {result['title']}")
        print(f"Uploader  : {result['uploader']}")
        print(f"Duration  : {result['duration_formatted']}")
        print(f"Segments  : {result['total_segments']}")
        print(f"\nFirst 5 segments:")
        for seg in result["segments"][:5]:
            print(f"  [{seg['timestamp']}] {seg['text']}")

    except Exception as e:
        print(f"\n[ERROR] {e}")