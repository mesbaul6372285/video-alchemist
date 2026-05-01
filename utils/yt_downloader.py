import os
import json
import subprocess
import tempfile
from faster_whisper import WhisperModel

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
WHISPER_MODEL_SIZE = "base"   # tiny | base | small | medium | large
AUDIO_FORMAT       = "mp3"
OUTPUT_DIR         = tempfile.gettempdir()


# ─────────────────────────────────────────────
# STEP 1 — Download audio from URL
# ─────────────────────────────────────────────
def download_audio(url: str) -> dict:
    """
    Downloads audio + metadata from a YouTube or Twitch URL using yt-dlp.
    Returns: { "audio_path": str, "title": str, "duration": int }
    """
    print(f"[Downloader] Fetching audio from: {url}")

    audio_path = os.path.join(OUTPUT_DIR, "video_audio.%(ext)s")

    command = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", AUDIO_FORMAT,
        "--audio-quality", "0",
        "--output", audio_path,
        "--print-json",
        "--no-playlist",
        url
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"[Downloader] yt-dlp failed:\n{result.stderr}")

    # Parse metadata from yt-dlp JSON output
    try:
        metadata = json.loads(result.stdout.strip().split("\n")[-1])
    except json.JSONDecodeError:
        metadata = {}

    final_audio_path = os.path.join(OUTPUT_DIR, f"video_audio.{AUDIO_FORMAT}")

    print(f"[Downloader] Audio saved to: {final_audio_path}")

    return {
        "audio_path": final_audio_path,
        "title": metadata.get("title", "Unknown Title"),
        "duration": metadata.get("duration", 0),
        "uploader": metadata.get("uploader", "Unknown"),
        "url": url
    }


# ─────────────────────────────────────────────
# STEP 2 — Transcribe audio with Whisper
# ─────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> list:
    """
    Transcribes audio file using faster-whisper.
    Returns: list of { "timestamp": "MM:SS", "text": str }
    """
    print(f"[Transcriber] Loading Whisper model: {WHISPER_MODEL_SIZE}")
    model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")

    print(f"[Transcriber] Transcribing: {audio_path}")
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"[Transcriber] Detected language: {info.language} (confidence: {info.language_probability:.2f})")

    transcript = []
    for segment in segments:
        minutes = int(segment.start // 60)
        seconds = int(segment.start % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"

        transcript.append({
            "timestamp": timestamp,
            "start_seconds": round(segment.start, 2),
            "end_seconds": round(segment.end, 2),
            "text": segment.text.strip()
        })

    print(f"[Transcriber] Total segments: {len(transcript)}")
    return transcript


# ─────────────────────────────────────────────
# STEP 3 — Main function (used by ingestion agent)
# ─────────────────────────────────────────────
def process_url(url: str) -> dict:
    """
    Full pipeline: URL → audio download → transcription
    Returns clean structured output for ingestion agent.
    """
    # Step 1: Download
    download_result = download_audio(url)

    # Step 2: Transcribe
    segments = transcribe_audio(download_result["audio_path"])

    # Step 3: Combine into final output
    output = {
        "title": download_result["title"],
        "uploader": download_result["uploader"],
        "duration_seconds": download_result["duration"],
        "duration_formatted": f"{int(download_result['duration'] // 60)}m {int(download_result['duration'] % 60)}s",
        "source_url": url,
        "segments": segments,
        "total_segments": len(segments)
    }

    print(f"[Downloader] Done. {len(segments)} segments from '{output['title']}'")
    return output


# ─────────────────────────────────────────────
# CLEANUP UTILITY
# ─────────────────────────────────────────────
def cleanup_audio():
    """Remove downloaded audio file after processing."""
    audio_path = os.path.join(OUTPUT_DIR, f"video_audio.{AUDIO_FORMAT}")
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print("[Downloader] Cleaned up audio file.")


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    test_url = input("Enter a YouTube URL to test: ").strip()
    result = process_url(test_url)

    print("\n=== OUTPUT ===")
    print(f"Title     : {result['title']}")
    print(f"Uploader  : {result['uploader']}")
    print(f"Duration  : {result['duration_formatted']}")
    print(f"Segments  : {result['total_segments']}")
    print(f"\nFirst 3 segments:")
    for seg in result["segments"][:3]:
        print(f"  [{seg['timestamp']}] {seg['text']}")

    cleanup_audio()