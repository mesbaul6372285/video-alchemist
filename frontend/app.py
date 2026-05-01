import sys
import os
import json
import time
import streamlit as st

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_pipeline

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Video Alchemist 2.0",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF4B4B, #FF8C00, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .platform-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #2d2d44;
        height: 100%;
    }
    .platform-title {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .tiktok-title   { color: #ff0050; }
    .linkedin-title { color: #0077b5; }
    .twitter-title  { color: #1da1f2; }
    .score-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .score-high   { background: #1a4a1a; color: #4cff4c; }
    .score-mid    { background: #4a3d00; color: #ffd700; }
    .score-low    { background: #4a1a1a; color: #ff4b4b; }
    .hook-card {
        background: #111122;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2d2d44;
        margin-bottom: 2rem;
    }
    .step-done    { color: #4cff4c; }
    .step-running { color: #ffd700; }
    .step-waiting { color: #444; }
    .iteration-pill {
        background: #2d2d44;
        border-radius: 20px;
        padding: 0.15rem 0.6rem;
        font-size: 0.75rem;
        color: #aaa;
        margin-right: 0.3rem;
    }
    div[data-testid="stCopyButton"] { float: right; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def score_badge(score: int) -> str:
    if score >= 75:
        css = "score-high"
    elif score >= 50:
        css = "score-mid"
    else:
        css = "score-low"
    return f'<span class="score-badge {css}">{score}/100</span>'

def score_color(score: int) -> str:
    if score >= 75:
        return "green"
    elif score >= 50:
        return "orange"
    return "red"

def render_iteration_history(iteration_log: list):
    if not iteration_log:
        return
    with st.expander("📊 Iteration History", expanded=False):
        for entry in iteration_log:
            attempt = entry.get("attempt", 0)
            s       = entry.get("score", 0)
            action  = entry.get("action", "")
            label   = "Initial Score" if attempt == 0 else f"Rewrite #{attempt}"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{label}** — _{entry.get('hook_text', '')[:80]}..._")
                if entry.get("changes_made"):
                    st.caption(f"Changes: {entry['changes_made']}")
                st.caption(f"Feedback: {entry.get('feedback', '')[:100]}...")
            with col2:
                st.metric("Score", f"{s}/100", delta=None)
            st.divider()

def render_platform_outputs(hook: dict):
    tiktok   = hook.get("tiktok", {})
    linkedin = hook.get("linkedin", {})
    twitter  = hook.get("twitter", {})

    col1, col2, col3 = st.columns(3)

    # ── TIKTOK ──
    with col1:
        st.markdown('<div class="platform-card">', unsafe_allow_html=True)
        st.markdown('<p class="platform-title tiktok-title">🎵 TikTok</p>', unsafe_allow_html=True)
        st.markdown(f"**Hook:** {tiktok.get('hook_line', '')}")
        st.code(tiktok.get("caption", ""), language=None)
        if tiktok.get("hashtags"):
            st.markdown(" ".join([f"`{h}`" for h in tiktok["hashtags"]]))
        st.markdown('</div>', unsafe_allow_html=True)

    # ── LINKEDIN ──
    with col2:
        st.markdown('<div class="platform-card">', unsafe_allow_html=True)
        st.markdown('<p class="platform-title linkedin-title">💼 LinkedIn</p>', unsafe_allow_html=True)
        st.markdown(f"**Hook:** {linkedin.get('hook_line', '')}")
        st.code(linkedin.get("caption", ""), language=None)
        if linkedin.get("cta"):
            st.markdown(f"_CTA: {linkedin['cta']}_")
        if linkedin.get("hashtags"):
            st.markdown(" ".join([f"`{h}`" for h in linkedin["hashtags"]]))
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TWITTER ──
    with col3:
        st.markdown('<div class="platform-card">', unsafe_allow_html=True)
        st.markdown('<p class="platform-title twitter-title">🐦 Twitter / X</p>', unsafe_allow_html=True)
        st.code(twitter.get("tweet", ""), language=None)
        thread = twitter.get("thread", [])
        if thread:
            with st.expander("🧵 View Thread"):
                for i, tweet in enumerate(thread, 1):
                    st.markdown(f"**{i}.** {tweet}")
                    st.divider()
        st.markdown('</div>', unsafe_allow_html=True)

def render_hook_card(hook: dict, index: int):
    hook_id        = hook.get("hook_id", index + 1)
    timestamp      = hook.get("timestamp", "00:00")
    final_score    = hook.get("final_score", 0)
    passed         = hook.get("passed_threshold", False)
    total_attempts = hook.get("total_attempts", 0)
    video_title    = hook.get("video_title", "")
    iteration_log  = hook.get("iteration_log", [])
    warnings       = hook.get("warnings", [])

    status_icon = "✅" if passed else "⚠️"

    st.markdown(f'<div class="hook-card">', unsafe_allow_html=True)

    # Header row
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 2, 2, 2])
    with h_col1:
        st.markdown(f"### Hook {hook_id}")
        st.caption(f"⏱ {timestamp}")
    with h_col2:
        st.markdown(f"**Final Score**")
        st.markdown(score_badge(final_score), unsafe_allow_html=True)
    with h_col3:
        st.markdown(f"**Rewrites**")
        st.markdown(f"`{total_attempts}` iteration(s)")
    with h_col4:
        st.markdown(f"**Status**")
        st.markdown(f"{status_icon} {'Passed' if passed else 'Max iterations reached'}")

    st.divider()

    # Score bar
    st.progress(final_score / 100, text=f"Virality Score: {final_score}/100")

    # Warnings
    if warnings:
        for w in warnings:
            st.warning(f"⚠ {w}")

    # Iteration history
    render_iteration_history(iteration_log)

    st.markdown("#### Platform Outputs")
    render_platform_outputs(hook)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AGENT PROGRESS TRACKER
# ─────────────────────────────────────────────

AGENT_STEPS = [
    ("🔗", "Ingestion Agent",  "Downloading + transcribing video"),
    ("🪝", "Hook Agent",       "Extracting viral moments"),
    ("📊", "Scoring Agent",    "Scoring each hook 0-100"),
    ("✏️", "Rewrite Agent",    "Rewriting low-scoring hooks"),
    ("🎨", "Formatter Agent",  "Formatting for all platforms"),
    ("📦", "Output Agent",     "Bundling final results"),
]

def render_progress_tracker(current_step: int):
    """Render live agent step tracker. current_step = 1-6, 0 = not started."""
    st.markdown("### 🤖 Pipeline Progress")
    for i, (icon, name, desc) in enumerate(AGENT_STEPS, 1):
        if i < current_step:
            css, status = "step-done", "✅ Done"
        elif i == current_step:
            css, status = "step-running", "⚡ Running..."
        else:
            css, status = "step-waiting", "⏳ Waiting"
        st.markdown(
            f'<span class="{css}">{icon} <b>Step {i}:</b> {name} — {desc} &nbsp; <i>{status}</i></span>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────

def main():
    # ── HEADER ──
    st.markdown('<p class="main-title">🎬 Video Alchemist 2.0</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Drop a URL. Get viral-ready content — automatically refined until it hits.</p>', unsafe_allow_html=True)

    # ── URL INPUT ──
    url = st.text_input(
        "YouTube or Twitch URL",
        placeholder="https://youtube.com/watch?v=...",
        label_visibility="collapsed"
    )

    run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

    st.divider()

    # ── PIPELINE RUN ──
    if run_btn:
        if not url or not url.startswith("http"):
            st.error("Please enter a valid YouTube or Twitch URL.")
            return

        # Progress placeholder
        progress_placeholder = st.empty()
        status_placeholder   = st.empty()

        # Simulate step tracking (pipeline runs synchronously)
        # We show steps incrementally using session state
        with st.spinner(""):
            progress_placeholder.markdown("---")
            with progress_placeholder.container():
                render_progress_tracker(1)

            try:
                # Run full pipeline
                # Note: In production, wrap each agent call separately for live updates
                status_placeholder.info("⚡ Pipeline running — this may take 1-3 minutes depending on video length...")
                result = run_pipeline(url)

                # Clear progress
                progress_placeholder.empty()
                status_placeholder.empty()

                # Store in session state
                st.session_state["result"] = result
                st.session_state["url"]    = url
                st.success("✅ Pipeline complete!")

            except Exception as e:
                progress_placeholder.empty()
                status_placeholder.empty()
                st.error(f"❌ Pipeline failed: {e}")
                return

    # ── RESULTS ──
    if "result" in st.session_state:
        result   = st.session_state["result"]
        metadata = result.get("metadata", {})
        hooks    = result.get("hooks", [])

        # ── METADATA SUMMARY ──
        st.markdown("## 📊 Pipeline Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Hooks",    metadata.get("total_hooks", 0))
        m2.metric("Passed (≥75)",   metadata.get("hooks_passed", 0))
        m3.metric("Avg Score",      f"{metadata.get('avg_final_score', 0)}/100")
        m4.metric("Total Rewrites", metadata.get("total_rewrites", 0))
        m5.metric("Pass Rate",      metadata.get("pass_rate", "0%"))

        st.caption(
            f"📹 **{metadata.get('video_title', '')}** by {metadata.get('video_uploader', '')} "
            f"· {metadata.get('video_duration', '')} "
            f"· Processed at {metadata.get('processed_at', '')}"
        )

        st.divider()

        # ── HOOK CARDS ──
        st.markdown("## 🪝 Hook Results")

        for i, hook in enumerate(hooks):
            render_hook_card(hook, i)

        # ── DOWNLOAD JSON ──
        st.divider()
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "output.json"
        )
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                json_data = f.read()
            st.download_button(
                label="⬇️ Download Full Output (JSON)",
                data=json_data,
                file_name="video_alchemist_output.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()