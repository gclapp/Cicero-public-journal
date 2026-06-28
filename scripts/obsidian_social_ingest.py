#!/usr/bin/env python3
"""Inventory saved social/video links and process them into Obsidian notes."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from obsidian_filename import sanitize_filename


VAULT = Path("/home/ubuntu/Obsidian/geoffclapp")
RAW_DIR = VAULT / "00_Unprocessed_Raw"
PROCESSED_DIR = VAULT / "10_Articles_Processed"
SYSTEM_DIR = PROCESSED_DIR / "_System"
STATE_DIR = Path("/home/ubuntu/.openclaw/workspace/state/social-ingest")
MEDIA_DIR = STATE_DIR / "media"
TRANSCRIPT_DIR = STATE_DIR / "transcripts"
TRANSCRIPTION_FAILURES = STATE_DIR / "transcription-failures.json"
DASHBOARD = PROCESSED_DIR / "Social Processing Dashboard.md"
URL_RE = re.compile(r"https?://[^\s)>\"]+")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
HASHTAG_RE = re.compile(r"#[\w_]+")


@dataclass
class RawLink:
    title: str
    url: str
    platform: str
    content_hint: str
    raw_path: str
    suggested_folder: str


def read_text(path: Path) -> str:
    return path.read_text(errors="ignore")


def platform_for(url: str) -> str:
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
    if "instagram.com" in host:
        return "instagram"
    if "threads.com" in host or "threads.net" in host:
        return "threads"
    if host in {"x.com", "twitter.com"}:
        return "x"
    if "reddit.com" in host:
        return "reddit"
    if "substack.com" in host:
        return "substack"
    if "linkedin.com" in host:
        return "linkedin"
    return host


def content_hint(url: str) -> str:
    lowered = url.lower()
    if "/reel/" in lowered:
        return "video"
    if "/stories/" in lowered:
        return "story"
    if "/p/" in lowered:
        return "post"
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return "video"
    return "link"


def first_link(path: Path) -> tuple[str, str] | None:
    text = read_text(path)
    match = MD_LINK_RE.search(text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    match = URL_RE.search(text)
    if match:
        return path.stem.strip(), match.group(0).strip()
    return None


def classify(title: str, url: str, description: str = "") -> str:
    blob = f"{title} {url} {description}".lower()
    if any(k in blob for k in ["obsidian", "second brain", "notebooklm", "knowledge management"]):
        return "AI/Obsidian Setups"
    if any(k in blob for k in ["agent", "agents", "agentic", "automation", "workflow"]):
        return "AI/Agents"
    if any(k in blob for k in ["claude code", "codex", "cursor", "cline"]):
        return "AI/Claude Code"
    if any(k in blob for k in ["prompt", "prompts", "prompting"]):
        return "AI/Prompting"
    if any(k in blob for k in ["product", "pm ", "roadmap", "strategy", "startup"]):
        return "AI/Product Management"
    if any(k in blob for k in ["ai", "llm", "openai", "chatgpt", "gemini", "claude"]):
        return "AI/Tools"
    if any(k in blob for k in ["leadership", "manager", "management", "ceo"]):
        return "Leadership"
    if any(k in blob for k in ["health", "metabolic", "sleep", "fitness", "shredded"]):
        return "Health"
    if any(k in blob for k in ["finance", "investor", "money", "trading", "crypto"]):
        return "Finance"
    if any(k in blob for k in ["entertainment", "movie", "music", "latimes"]):
        return "Entertainment"
    return "AI/Tools" if "instagram.com" in url and "ai" in title.lower() else "_Review"


def inventory() -> list[RawLink]:
    links: list[RawLink] = []
    for path in sorted(RAW_DIR.glob("**/*.md")):
        link = first_link(path)
        if not link:
            continue
        title, url = link
        platform = platform_for(url)
        if platform not in {"instagram", "threads", "x", "reddit", "substack", "linkedin"}:
            continue
        links.append(
            RawLink(
                title=title,
                url=url,
                platform=platform,
                content_hint=content_hint(url),
                raw_path=str(path.relative_to(VAULT)),
                suggested_folder=classify(title, url),
            )
        )
    return links


def fetch_metadata(url: str, timeout: int = 45) -> dict[str, Any]:
    cmd = ["yt-dlp", "--skip-download", "--dump-json", "--no-warnings", url]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or proc.stdout).strip()[:1000]}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"JSON parse failed: {exc}"}
    return {
        "ok": True,
        "id": data.get("id"),
        "title": data.get("title"),
        "description": data.get("description"),
        "uploader": data.get("uploader") or data.get("channel"),
        "duration": data.get("duration"),
        "webpage_url": data.get("webpage_url"),
        "thumbnail": data.get("thumbnail"),
        "extractor": data.get("extractor"),
    }


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ")


def write_inventory_report(links: list[RawLink]) -> Path:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts: dict[str, int] = {}
    platforms: dict[str, int] = {}
    for link in links:
        counts[link.suggested_folder] = counts.get(link.suggested_folder, 0) + 1
        platforms[link.platform] = platforms.get(link.platform, 0) + 1
    lines = [
        "# Social Link Inventory",
        "",
        f"Generated: {now}",
        "",
        f"Total links found: {len(links)}",
        "",
        "## By Platform",
        "",
    ]
    for key, value in sorted(platforms.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Suggested Folders", ""]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## Items",
        "",
        "| Platform | Type | Suggested Folder | Title | Raw Note |",
        "|---|---|---|---|---|",
    ]
    for link in links:
        lines.append(
            f"| {link.platform} | {link.content_hint} | {link.suggested_folder} | "
            f"[{md_escape(link.title)}]({link.url}) | `{md_escape(link.raw_path)}` |"
        )
    path = SYSTEM_DIR / "Social Link Inventory.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_pilot_report(results: list[dict[str, Any]]) -> Path:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Social Metadata Pilot",
        "",
        f"Generated: {now}",
        "",
        "This pilot uses anonymous `yt-dlp` metadata fetches. Items that fail may need Instagram/browser cookies later.",
        "",
    ]
    for item in results:
        link = item["link"]
        meta = item["metadata"]
        lines += [
            f"## {link['title']}",
            "",
            f"- Platform: {link['platform']}",
            f"- Type: {link['content_hint']}",
            f"- Suggested folder: {item['suggested_folder']}",
            f"- Raw note: `{link['raw_path']}`",
            f"- URL: {link['url']}",
            f"- Metadata status: {'ok' if meta.get('ok') else 'failed'}",
        ]
        if meta.get("ok"):
            description = (meta.get("description") or "").strip()
            lines += [
                f"- Extractor: {meta.get('extractor') or ''}",
                f"- Uploader: {meta.get('uploader') or ''}",
                f"- Duration: {meta.get('duration') or ''}",
                "",
                "### Caption / Description",
                "",
                description[:3000] or "_No description returned._",
                "",
            ]
        else:
            lines += ["", "### Error", "", meta.get("error", "Unknown error"), ""]
    path = SYSTEM_DIR / "Social Metadata Pilot.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def note_slug(text: str, max_len: int = 90) -> str:
    return sanitize_filename(text, max_len=max_len, default="Untitled")


def summary_from_description(title: str, description: str) -> str:
    cleaned = re.sub(r"\n[-\s]*\n", "\n", description or "").strip()
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    first = next((s.strip() for s in sentences if s.strip() and not s.strip().startswith("#")), "")
    if first:
        return first[:500]
    return f"Saved social item about {title}."


def concepts_from_text(title: str, description: str) -> list[str]:
    blob = f"{title} {description}".lower()
    concepts: list[str] = []
    rules = [
        ("AI memory", ["ai memory", "personal ai memory", "memory system"]),
        ("Obsidian", ["obsidian"]),
        ("Second brain", ["second brain"]),
        ("Claude", ["claude"]),
        ("Agents", ["agent", "agents", "agentic"]),
        ("Automation", ["automation", "automations", "workflow"]),
        ("Productivity", ["productivity"]),
        ("Startup", ["startup", "entrepreneur"]),
        ("MCP", ["mcp"]),
        ("Prompting", ["prompt"]),
    ]
    for label, needles in rules:
        if any(n in blob for n in needles):
            concepts.append(label)
    for tag in HASHTAG_RE.findall(description or "")[:8]:
        nice = tag.strip("#")
        if nice and nice not in concepts:
            concepts.append(nice)
    return concepts or ["Needs review"]


def links_from_text(text: str) -> list[str]:
    return sorted(set(URL_RE.findall(text or "")))


def create_processed_notes_from_pilot() -> list[Path]:
    pilot_path = STATE_DIR / "metadata-pilot.json"
    if not pilot_path.exists():
        raise SystemExit("No metadata pilot found. Run --pilot first.")
    data = json.loads(pilot_path.read_text())
    created: list[Path] = []
    for item in data:
        meta = item["metadata"]
        if not meta.get("ok"):
            continue
        link = item["link"]
        folder = item["suggested_folder"]
        out_dir = PROCESSED_DIR / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        title = meta.get("title") or link["title"]
        description = meta.get("description") or ""
        concepts = concepts_from_text(title, description)
        external_links = links_from_text(description)
        out_path = out_dir / f"{note_slug(title)}.md"
        lines = [
            "---",
            "type: processed_social_item",
            f"source_platform: {json.dumps(link['platform'])}",
            f"source_url: {json.dumps(link['url'])}",
            f"raw_note: {json.dumps(link['raw_path'])}",
            f"status: metadata_processed",
            f"transcript_status: pending",
            f"suggested_folder: {json.dumps(folder)}",
            "---",
            "",
            f"# {title}",
            "",
            "## Summary",
            "",
            summary_from_description(title, description),
            "",
            "## Key Concepts",
            "",
        ]
        lines += [f"- {c}" for c in concepts]
        lines += [
            "",
            "## Source",
            "",
            f"- URL: {link['url']}",
            f"- Raw note: `{link['raw_path']}`",
            f"- Uploader: {meta.get('uploader') or ''}",
            f"- Duration: {meta.get('duration') or ''}",
            f"- Extractor: {meta.get('extractor') or ''}",
            "",
            "## Caption / Description",
            "",
            description or "_No caption returned._",
            "",
            "## Links Mentioned",
            "",
        ]
        lines += [f"- {u}" for u in external_links] if external_links else ["_No outbound links found in caption._"]
        lines += [
            "",
            "## Transcript",
            "",
            "_Transcript pending. Media download/transcription has not run yet._",
            "",
            "## Cicero Notes",
            "",
            "- Created from metadata pilot. Review folder/category before scaling to the full vault.",
        ]
        if not out_path.exists():
            out_path.write_text("\n".join(lines) + "\n")
            created.append(out_path)
    return created


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def processed_social_notes() -> list[Path]:
    notes: list[Path] = []
    for path in sorted(PROCESSED_DIR.glob("**/*.md")):
        if path == DASHBOARD or "_System" in path.parts:
            continue
        meta = parse_frontmatter(path)
        if meta.get("type") == "processed_social_item":
            notes.append(path)
    return notes


def processed_source_urls() -> set[str]:
    urls: set[str] = set()
    for path in processed_social_notes():
        url = parse_frontmatter(path).get("source_url")
        if url:
            urls.add(url)
    return urls


def is_transcript_done(status: str) -> bool:
    return status in {"done", "cleaned", "complete_tiny_model"} or status.startswith("complete")


def replace_frontmatter_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(key)}:\s*).*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(rf"\1{value}", text, count=1)
    if text.startswith("---\n"):
        return text.replace("---\n", f"---\n{key}: {value}\n", 1)
    return text


def replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"(^## {re.escape(heading)}\n\n)(.*?)(?=\n## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    replacement = rf"\1{body.rstrip()}\n"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + f"\n\n## {heading}\n\n{body.rstrip()}\n"


def get_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def cleanup_transcript(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        line = re.sub(r"^\[[0-9:.,\s\-]+-->\s*[0-9:.,\s]+\]\s*", "", line).strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    text = "\n".join(lines)
    replacements = {
        "AO second brain": "AI second brain",
        "under Caparty's LLM": "Unclear: third-party LLM",
        "To offer fire": "Unclear audio",
        "Process as knows": "process these notes",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.strip()


def download_audio(url: str, media_id: str, timeout: int = 180) -> Path:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    output = MEDIA_DIR / f"{media_id}.%(ext)s"
    existing = sorted(MEDIA_DIR.glob(f"{media_id}.*"))
    if existing:
        return existing[0]
    cmd = [
        "yt-dlp",
        "-f",
        "ba/bestaudio",
        "--extract-audio",
        "--audio-format",
        "m4a",
        "--no-playlist",
        "-o",
        str(output),
        url,
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:1200])
    existing = sorted(MEDIA_DIR.glob(f"{media_id}.*"))
    if not existing:
        raise RuntimeError("yt-dlp completed but no audio file was found")
    return existing[0]


def run_whisper(audio_path: Path, model: str = "tiny", timeout: int = 900) -> Path:
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TRANSCRIPT_DIR / f"{audio_path.stem}.txt"
    if out_path.exists() and out_path.read_text(errors="ignore").strip():
        return out_path
    cmd = [
        "whisper",
        str(audio_path),
        "--model",
        model,
        "--language",
        "en",
        "--output_format",
        "txt",
        "--output_dir",
        str(TRANSCRIPT_DIR),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:1200])
    if not out_path.exists():
        raise RuntimeError("Whisper completed but no transcript file was found")
    return out_path


def transcribe_pending(limit: int, max_duration: int, model: str, dry_run: bool = False) -> list[dict[str, Any]]:
    failures = load_json(TRANSCRIPTION_FAILURES, [])
    results: list[dict[str, Any]] = []
    candidates: list[Path] = []
    for path in processed_social_notes():
        meta = parse_frontmatter(path)
        if is_transcript_done(meta.get("transcript_status", "")):
            continue
        if not meta.get("source_url"):
            continue
        if "instagram" not in meta.get("source_platform", ""):
            continue
        text = read_text(path)
        duration_match = re.search(r"^- Duration:\s*([0-9.]+)", text, re.MULTILINE)
        if duration_match:
            try:
                if float(duration_match.group(1)) > max_duration:
                    continue
            except ValueError:
                pass
        candidates.append(path)
    for path in candidates[:limit]:
        meta = parse_frontmatter(path)
        url = meta["source_url"]
        media_id = url.rstrip("/").split("/")[-1].split("?")[0] or note_slug(path.stem)
        if dry_run:
            results.append({"note": str(path), "status": "would_transcribe", "url": url})
            continue
        try:
            audio = download_audio(url, media_id)
            transcript_path = run_whisper(audio, model=model)
            transcript = cleanup_transcript(transcript_path.read_text(errors="ignore"))
            note_text = read_text(path)
            note_text = replace_section(note_text, "Transcript", transcript or "_Transcript returned empty._")
            note_text = replace_frontmatter_value(note_text, "transcript_status", "done")
            path.write_text(note_text)
            results.append({"note": str(path), "status": "done", "audio": str(audio), "transcript": str(transcript_path)})
        except Exception as exc:  # noqa: BLE001 - surfaced in dashboard for manual review
            failure = {
                "at": datetime.now(timezone.utc).isoformat(),
                "note": str(path),
                "url": url,
                "reason": str(exc)[:1200],
            }
            failures.append(failure)
            results.append({"note": str(path), "status": "failed", "reason": failure["reason"]})
    save_json(TRANSCRIPTION_FAILURES, failures[-100:])
    return results


def cleanup_existing_transcripts(limit: int, dry_run: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in processed_social_notes():
        if len(results) >= limit:
            break
        text = read_text(path)
        meta = parse_frontmatter(path)
        if not is_transcript_done(meta.get("transcript_status", "")):
            continue
        transcript = get_section(text, "Transcript")
        if not transcript or "Transcript pending" in transcript:
            continue
        cleaned = cleanup_transcript(transcript)
        if cleaned == transcript.strip() and meta.get("transcript_status") == "cleaned":
            continue
        if dry_run:
            results.append({"note": str(path), "status": "would_cleanup"})
            continue
        text = replace_section(text, "Transcript", cleaned)
        text = replace_frontmatter_value(text, "transcript_status", "cleaned")
        path.write_text(text)
        results.append({"note": str(path), "status": "cleaned"})
    return results


def failed_metadata_items() -> list[dict[str, Any]]:
    results = load_json(STATE_DIR / "metadata-pilot.json", [])
    failed: list[dict[str, Any]] = []
    for item in results:
        meta = item.get("metadata", {})
        if meta.get("ok"):
            continue
        link = item.get("link", {})
        failed.append(
            {
                "title": link.get("title", ""),
                "platform": link.get("platform", ""),
                "type": link.get("content_hint", ""),
                "raw_path": link.get("raw_path", ""),
                "url": link.get("url", ""),
                "reason": meta.get("error", "metadata fetch failed"),
                "action": "Open in browser or rerun later with explicit cookie authorization.",
            }
        )
    return failed


def write_dashboard(links: list[RawLink]) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    platform_counts: dict[str, int] = {}
    folder_counts: dict[str, int] = {}
    for link in links:
        platform_counts[link.platform] = platform_counts.get(link.platform, 0) + 1
        folder_counts[link.suggested_folder] = folder_counts.get(link.suggested_folder, 0) + 1

    notes = processed_social_notes()
    source_urls = processed_source_urls()
    transcript_counts = {"done": 0, "pending": 0, "failed": 0}
    for note in notes:
        status = parse_frontmatter(note).get("transcript_status", "pending")
        if is_transcript_done(status):
            transcript_counts["done"] += 1
        elif status in transcript_counts:
            transcript_counts[status] += 1
        else:
            transcript_counts["pending"] += 1
    transcription_failures = load_json(TRANSCRIPTION_FAILURES, [])
    if transcription_failures:
        transcript_counts["failed"] = len(transcription_failures)
    metadata_failures = failed_metadata_items()
    unprocessed = [link for link in links if link.url not in source_urls]

    lines = [
        "# Social Processing Dashboard",
        "",
        f"Last updated: {now}",
        "",
        "## Running Stats",
        "",
        f"- Raw social links found: {len(links)}",
        f"- Processed social notes created: {len(notes)}",
        f"- Raw links not yet processed into notes: {len(unprocessed)}",
        f"- Metadata failures needing manual review: {len(metadata_failures)}",
        f"- Transcription failures needing manual review: {len(transcription_failures)}",
        f"- Transcripts done: {transcript_counts['done']}",
        f"- Transcripts pending: {transcript_counts['pending']}",
        "",
        "## By Platform",
        "",
    ]
    for key, value in sorted(platform_counts.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## By Suggested Folder", ""]
    for key, value in sorted(folder_counts.items()):
        lines.append(f"- {key}: {value}")

    lines += [
        "",
        "## Manual Intervention Needed",
        "",
        "| Type | Title / Note | Raw Note | Reason | Action | URL |",
        "|---|---|---|---|---|---|",
    ]
    if not metadata_failures and not transcription_failures:
        lines.append("| none | No current failures |  |  |  |  |")
    for item in metadata_failures:
        reason = md_escape(item["reason"][:240])
        lines.append(
            f"| metadata | {md_escape(item['title'])} | `{md_escape(item['raw_path'])}` | "
            f"{reason} | {md_escape(item['action'])} | {item['url']} |"
        )
    for item in transcription_failures[-50:]:
        reason = md_escape(item.get("reason", "")[:240])
        note = str(Path(item.get("note", "")).relative_to(VAULT)) if item.get("note", "").startswith(str(VAULT)) else item.get("note", "")
        lines.append(
            f"| transcript | `{md_escape(note)}` |  | {reason} | Retry later or inspect cached media/transcript state. | {item.get('url', '')} |"
        )

    lines += [
        "",
        "## Recently Processed Notes",
        "",
    ]
    for note in notes[-25:]:
        rel = note.relative_to(VAULT)
        meta = parse_frontmatter(note)
        lines.append(f"- [[{rel.with_suffix('').as_posix()}]] - transcript `{meta.get('transcript_status', 'pending')}`")
    path = DASHBOARD
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory/process saved social links in Obsidian.")
    parser.add_argument("--inventory-report", action="store_true", help="Write inventory report into 10_Articles_Processed/_System.")
    parser.add_argument("--pilot", action="store_true", help="Run metadata pilot against saved Instagram video links.")
    parser.add_argument("--create-notes-from-pilot", action="store_true", help="Create processed notes for successful pilot metadata items.")
    parser.add_argument("--transcribe-pending", action="store_true", help="Download/transcribe pending processed Instagram notes with limits.")
    parser.add_argument("--cleanup-transcripts", action="store_true", help="Clean up existing transcript text without refetching media.")
    parser.add_argument("--refresh-dashboard", action="store_true", help="Write the top-level social processing dashboard.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-duration", type=int, default=180, help="Skip videos longer than this many seconds for batch transcription.")
    parser.add_argument("--whisper-model", default="tiny", help="Whisper model for local transcription.")
    args = parser.parse_args()

    links = inventory()
    print(f"Found {len(links)} social links")
    if args.inventory_report:
        path = write_inventory_report(links)
        print(f"Wrote inventory report: {path}")

    if args.pilot:
        pilot_links = [l for l in links if l.platform == "instagram" and l.content_hint in {"video", "post", "story"}][: args.limit]
        results: list[dict[str, Any]] = []
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        for link in pilot_links:
            print(f"Fetching metadata: {link.title} {link.url}")
            meta = fetch_metadata(link.url)
            folder = classify(link.title, link.url, meta.get("description") or "")
            results.append({"link": asdict(link), "metadata": meta, "suggested_folder": folder})
        (STATE_DIR / "metadata-pilot.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
        path = write_pilot_report(results)
        print(f"Wrote pilot report: {path}")
    if args.create_notes_from_pilot:
        paths = create_processed_notes_from_pilot()
        for path in paths:
            print(f"Created processed note: {path}")
        print(f"Created {len(paths)} processed note(s)")
    if args.transcribe_pending:
        results = transcribe_pending(
            limit=args.limit,
            max_duration=args.max_duration,
            model=args.whisper_model,
            dry_run=args.dry_run,
        )
        for result in results:
            print(json.dumps(result, ensure_ascii=False))
        print(f"Transcription results: {len(results)}")
    if args.cleanup_transcripts:
        results = cleanup_existing_transcripts(limit=args.limit, dry_run=args.dry_run)
        for result in results:
            print(json.dumps(result, ensure_ascii=False))
        print(f"Transcript cleanup results: {len(results)}")
    if (
        args.refresh_dashboard
        or args.inventory_report
        or args.pilot
        or args.create_notes_from_pilot
        or args.transcribe_pending
        or args.cleanup_transcripts
    ):
        path = write_dashboard(links)
        print(f"Wrote dashboard: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
