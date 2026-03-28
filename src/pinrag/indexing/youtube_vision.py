"""Optional vision enrichment for YouTube transcript indexing."""

from __future__ import annotations

import base64
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.documents import Document

from pinrag.config import (
    get_vision_model,
    get_vision_provider,
    get_yt_vision_image_detail,
    get_yt_vision_max_frames,
    get_yt_vision_min_scene_score,
)
from pinrag.indexing.youtube_loader import YouTubeLoadResult

_log = logging.getLogger("pinrag.indexing")

_VISION_PROMPT = (
    "You are extracting on-screen context from a technical tutorial video frame "
    "for a search index. Your output must be concise, factual, and keyword-rich "
    "so it is easy to find later.\n\n"
    "If nothing meaningful is on screen (e.g. a talking-head shot with no text, "
    "code, or diagrams), reply with exactly the single word NO_CONTENT and nothing else.\n\n"
    "Otherwise describe only what is actually visible using the rules below.\n"
    "Hard rules (do not break these):\n"
    "- List a symbol, callee, or type only if you can read it in this frame. "
    "Do not guess from video topic, filename, or prior knowledge.\n"
    "- If call expressions on a line are too small or blurred, omit the Callees subsection "
    "or write exactly: (callees not legible)\n\n"
    "CODE (editor or terminal showing code):\n"
    "- Filename / tab name if shown.\n"
    "- Every visible top-level function: full signature (return type, name, parameters with types).\n"
    "- Callees: every API or function name invoked on visible lines inside those functions "
    "(read names letter-by-letter; include driver/HAL prefixes such as tuh_ if present).\n"
    "- Other identifiers: variables, macros, and types only when clearly visible on those lines "
    "(e.g. busy[pdrv], pdrv, lun, RES_OK, uint16_t).\n"
    "- Do NOT reproduce full bodies line-by-line; bullet lists are enough.\n\n"
    "TERMINAL / SHELL:\n"
    "- Exact commands, flags, and paths.\n"
    "- Key output lines, errors, and warnings verbatim.\n\n"
    "DIAGRAMS / SLIDES:\n"
    "- Every label and heading (exact spelling).\n"
    "- Arrow or connection relationships.\n\n"
    "UI (non-code application screen):\n"
    "- Application name, visible panels, status messages.\n\n"
    "Be precise — correct spelling of identifiers matters for search."
)


@dataclass(frozen=True)
class ExtractedFrame:
    """A single extracted video frame and timestamp."""

    timestamp: float
    image_path: Path
    scene_index: int


@dataclass(frozen=True)
class FrameAnalysis:
    """Vision model description for an extracted frame."""

    timestamp: float
    description: str
    scene_index: int


class _YtdlpStderrLogger:
    """Redirect all yt-dlp output to stderr so stdout stays clean for MCP JSON transport."""

    def debug(self, msg: str) -> None:
        if msg.startswith("[debug]"):
            return
        sys.stderr.write(msg + "\n")

    def info(self, msg: str) -> None:
        sys.stderr.write(msg + "\n")

    def warning(self, msg: str) -> None:
        sys.stderr.write("WARNING: " + msg + "\n")

    def error(self, msg: str) -> None:
        sys.stderr.write("ERROR: " + msg + "\n")


def download_video(video_id: str, output_dir: Path) -> Path:
    """Download a YouTube video as MP4 using yt-dlp and return local path."""
    import yt_dlp  # type: ignore[import-untyped]

    output_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(output_dir / "video.%(ext)s")
    source_url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _YtdlpStderrLogger(),
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(source_url, download=True)

    mp4_files = sorted(output_dir.glob("*.mp4"))
    if mp4_files:
        return mp4_files[0]

    any_file = sorted(output_dir.glob("*"))
    if any_file:
        return any_file[0]

    raise RuntimeError(f"yt-dlp did not produce a video file for {video_id}")


def extract_frames(
    video_path: Path,
    *,
    max_frames: int,
    min_scene_score: float,
    output_dir: Path,
) -> list[ExtractedFrame]:
    """Extract timestamped keyframes using scene detection and ffmpeg."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is required for YouTube vision enrichment. "
            "Install ffmpeg and retry."
        )

    try:
        from scenedetect import AdaptiveDetector, SceneManager, open_video
    except ImportError as exc:
        raise ImportError(
            "YouTube vision enrichment requires optional dependencies. "
            "Install with: pip install 'pinrag[vision]'"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(AdaptiveDetector(adaptive_threshold=min_scene_score))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    timestamps = [
        (start.get_seconds() + end.get_seconds()) / 2.0 for start, end in scene_list
    ]
    if not timestamps:
        duration = _probe_video_duration(video_path)
        # Fallback for static or low-motion videos: one frame each minute.
        timestamps = [float(t) for t in range(0, max(1, int(duration)), 60)]

    timestamps = sorted(set(max(0.0, float(t)) for t in timestamps))
    timestamps = timestamps[:max_frames]

    frames: list[ExtractedFrame] = []
    for idx, ts in enumerate(timestamps):
        out_path = output_dir / f"frame-{idx:04d}.png"
        _extract_single_frame(video_path=video_path, timestamp=ts, output_path=out_path)
        if out_path.exists():
            frames.append(
                ExtractedFrame(timestamp=round(ts, 2), image_path=out_path, scene_index=idx)
            )
    return frames


def analyze_frames(
    frames: list[ExtractedFrame],
    *,
    provider: str,
    model: str,
    image_detail: str = "low",
) -> list[FrameAnalysis]:
    """Run a vision model on extracted frames and return descriptions."""
    if provider == "anthropic":
        return _analyze_frames_anthropic(frames=frames, model=model)
    return _analyze_frames_openai(frames=frames, model=model, image_detail=image_detail)


def merge_transcript_and_frames(
    transcript_documents: list[Document],
    frame_analyses: list[FrameAnalysis],
) -> list[Document]:
    """Merge visual frame descriptions into transcript documents by timestamp."""
    merged = [
        Document(page_content=doc.page_content, metadata=dict(doc.metadata))
        for doc in transcript_documents
    ]
    if not merged or not frame_analyses:
        return merged

    frame_counts: dict[int, int] = {}
    on_screen_parts: dict[int, list[str]] = {}
    for analysis in sorted(frame_analyses, key=lambda a: a.timestamp):
        idx = _find_best_segment_index(merged, analysis.timestamp)
        if idx is None:
            continue
        desc = _normalize_whitespace(analysis.description)
        on_screen_parts.setdefault(idx, []).append(
            f"[On-screen at {int(round(analysis.timestamp))}s] {desc}"
        )
        frame_counts[idx] = frame_counts.get(idx, 0) + 1

    for idx, parts in on_screen_parts.items():
        doc = merged[idx]
        narrator_text = (doc.page_content or "").strip()
        if narrator_text.startswith("[Narrator] "):
            content_prefix = narrator_text
        elif narrator_text:
            content_prefix = f"[Narrator] {narrator_text}"
        else:
            content_prefix = "[Narrator]"
        doc.page_content = (content_prefix + "\n\n" + "\n\n".join(parts)).strip()
        doc.metadata["has_visual"] = True
        doc.metadata["frame_count"] = frame_counts[idx]
        doc.metadata["visual_source"] = "scene_detect"

    return merged


def enrich_with_vision(load_result: YouTubeLoadResult) -> YouTubeLoadResult:
    """Download, extract, analyze, and merge visual context into transcript docs."""
    max_frames = get_yt_vision_max_frames()
    min_scene_score = get_yt_vision_min_scene_score()
    provider = get_vision_provider()
    model = get_vision_model()
    image_detail = get_yt_vision_image_detail()

    with TemporaryDirectory(prefix=f"pinrag-yt-{load_result.video_id}-") as tmp:
        tmp_dir = Path(tmp)
        video_path = download_video(load_result.video_id, tmp_dir / "video")
        frames = extract_frames(
            video_path,
            max_frames=max_frames,
            min_scene_score=min_scene_score,
            output_dir=tmp_dir / "frames",
        )
        if not frames:
            return load_result
        analyses = analyze_frames(
            frames, provider=provider, model=model, image_detail=image_detail
        )
        if not analyses:
            return load_result
        docs = merge_transcript_and_frames(load_result.documents, analyses)

    return YouTubeLoadResult(
        video_id=load_result.video_id,
        source_url=load_result.source_url,
        documents=docs,
        total_segments=load_result.total_segments,
        title=load_result.title,
    )


def _probe_video_duration(video_path: Path) -> float:
    """Return media duration in seconds using ffprobe."""
    if shutil.which("ffprobe") is None:
        return 0.0
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    try:
        return max(0.0, float(result.stdout.strip()))
    except ValueError:
        return 0.0


def _extract_single_frame(*, video_path: Path, timestamp: float, output_path: Path) -> None:
    """Extract a single frame using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(0.0, timestamp):.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-y",
        str(output_path),
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to extract frame at {timestamp:.2f}s: {result.stderr.strip()}"
        )


def _find_best_segment_index(documents: list[Document], timestamp: float) -> int | None:
    """Find transcript segment index that contains or is nearest the timestamp."""
    if not documents:
        return None

    best_index: int | None = None
    best_distance = float("inf")

    for i, doc in enumerate(documents):
        start_raw = doc.metadata.get("start", 0)
        duration_raw = doc.metadata.get("duration", 0)
        try:
            start = float(start_raw)
        except (TypeError, ValueError):
            start = 0.0
        try:
            duration = float(duration_raw)
        except (TypeError, ValueError):
            duration = 0.0

        segment_end = start + max(duration, 1.0)
        if start <= timestamp < segment_end:
            return i

        distance = abs(start - timestamp)
        if distance < best_distance:
            best_distance = distance
            best_index = i

    return best_index


def _normalize_whitespace(text: str) -> str:
    """Collapse runs of blank lines into single blank lines and strip trailing spaces."""
    import re

    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _read_image_as_base64(path: Path) -> str:
    """Read image file as base64 string."""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _analyze_frames_openai(
    *,
    frames: list[ExtractedFrame],
    model: str,
    image_detail: str = "low",
) -> list[FrameAnalysis]:
    """Analyze frames with OpenAI chat completions API (vision)."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "OpenAI vision requires the openai package. Install with: pip install openai"
        ) from exc

    # Let the SDK resolve the key from OPENAI_API_KEY env var automatically;
    # passing api_key=None triggers the SDK's own env lookup and gives a clear
    # error if it is missing, so we avoid the redundant explicit check that
    # shadowed the SDK's error message.
    key = os.environ.get("OPENAI_API_KEY") or None
    client = OpenAI(api_key=key)
    analyses: list[FrameAnalysis] = []
    detail_norm = (image_detail or "low").strip().lower()
    if detail_norm not in ("low", "high", "auto"):
        detail_norm = "low"
    max_out = 600 if detail_norm in ("high", "auto") else 450

    for frame in frames:
        try:
            encoded = _read_image_as_base64(frame.image_path)
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_out,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _VISION_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded}",
                                    "detail": detail_norm,
                                },
                            },
                        ],
                    }
                ],
            )
            text = ""
            if response.choices:
                raw = (response.choices[0].message.content or "").strip()
                # Strip any lines that are solely the NO_CONTENT sentinel (the model
                # sometimes emits it as a section placeholder rather than a full reply)
                text = "\n".join(
                    line for line in raw.splitlines() if line.strip().upper() != "NO_CONTENT"
                ).strip()
            if not text or text.upper() == "NO_CONTENT":
                continue
            analyses.append(
                FrameAnalysis(
                    timestamp=frame.timestamp, description=text, scene_index=frame.scene_index
                )
            )
        except Exception as exc:  # pragma: no cover - external API errors
            _log.warning(
                "OpenAI vision failed for frame %s at %.2fs: %s",
                frame.image_path.name,
                frame.timestamp,
                exc,
            )

    return analyses


def _analyze_frames_anthropic(
    *, frames: list[ExtractedFrame], model: str
) -> list[FrameAnalysis]:
    """Analyze frames with Anthropic Messages API."""
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise ImportError(
            "Anthropic vision requires anthropic package. "
            "Install with: pip install anthropic"
        ) from exc

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required for Anthropic vision enrichment."
        )

    client = Anthropic(api_key=key)
    analyses: list[FrameAnalysis] = []

    for frame in frames:
        try:
            encoded = _read_image_as_base64(frame.image_path)
            response = client.messages.create(
                model=model,
                max_tokens=450,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _VISION_PROMPT},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": encoded,
                                },
                            },
                        ],
                    }
                ],
            )
            chunks = []
            for block in response.content:
                if getattr(block, "type", "") == "text" and getattr(block, "text", ""):
                    chunks.append(str(block.text).strip())
            raw = "\n".join(x for x in chunks if x).strip()
            # Strip any lines that are solely the NO_CONTENT sentinel
            text = "\n".join(
                line for line in raw.splitlines() if line.strip().upper() != "NO_CONTENT"
            ).strip()
            if not text or text.upper() == "NO_CONTENT":
                continue
            analyses.append(
                FrameAnalysis(
                    timestamp=frame.timestamp, description=text, scene_index=frame.scene_index
                )
            )
        except Exception as exc:  # pragma: no cover - external API errors
            _log.warning(
                "Anthropic vision failed for frame %s at %.2fs: %s",
                frame.image_path.name,
                frame.timestamp,
                exc,
            )

    return analyses
