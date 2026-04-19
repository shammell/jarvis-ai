#!/usr/bin/env python3
"""
Full repository audit for JARVIS.

Outputs:
- analysis/FULL_REPO_AUDIT_REPORT.md
- analysis/FULL_REPO_AUDIT_REPORT.json

This script scans code files, partitions them by major folders, classifies
usability readiness, and maps advanced capabilities from implementation
evidence in key runtime files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".sh", ".ps1", ".bat"}

PRIMARY_PARTITIONS = [
    "core",
    "api",
    "memory",
    "agents",
    "grpc_service",
    "whatsapp",
    "web",
    "mcp",
    "control",
    "tests",
    "scripts",
    "launchers",
    "skills",
    "archive",
    "analysis",
    "ralph-claude-code",
    "root",
    "other",
]

MIRROR_PREFIXES = [
    ".claude/worktrees/",
]

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".next",
    ".venv",
    "venv",
    "dist",
    "build",
}


@dataclass
class FileAudit:
    path: str
    partition: str
    is_mirror: bool
    dedupe_key: str
    usability: str
    reasons: List[str]


def normalize_rel_path(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def iter_code_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        parts = set(path.parts)
        if parts.intersection(EXCLUDED_DIRS):
            continue
        yield path


def path_partition(rel_path: str) -> str:
    top = rel_path.split("/", 1)[0]
    if top in PRIMARY_PARTITIONS:
        return top
    if "/" not in rel_path:
        return "root"
    return "other"


def is_mirror_path(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in MIRROR_PREFIXES)


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sampled_file_signature(path: Path, sample_size: int = 65536) -> str:
    """Build a fast dedupe signature without reading entire huge files."""
    try:
        stat = path.stat()
        with path.open("rb") as fh:
            head = fh.read(sample_size)
        digest = sha1_bytes(head)
        return f"{stat.st_size}:{digest}"
    except OSError:
        return "unreadable"


def safe_read_text(path: Path, max_bytes: int = 300000) -> str:
    """Read at most max_bytes and decode safely for regex heuristics."""
    try:
        with path.open("rb") as fh:
            raw = fh.read(max_bytes)
        return raw.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def classify_file(rel_path: str, content: str) -> Tuple[str, List[str]]:
    path_lower = rel_path.lower()
    reasons: List[str] = []

    if "/archive/" in f"/{path_lower}" or path_lower.startswith("archive/"):
        return "archived_dead", ["Located under archive/"]

    if any(token in path_lower for token in ["template", "boilerplate", "example"]):
        reasons.append("Template/example path pattern")

    todo_hits = len(re.findall(r"\b(todo|fixme|xxx|hack)\b", content, flags=re.IGNORECASE))
    pass_hits = len(re.findall(r"^\s*pass\s*$", content, flags=re.MULTILINE))
    bare_except_hits = len(re.findall(r"except\s*:\s*(pass)?", content))

    if todo_hits:
        reasons.append(f"TODO-like markers: {todo_hits}")
    if pass_hits > 3:
        reasons.append(f"Multiple pass statements: {pass_hits}")
    if bare_except_hits:
        reasons.append(f"Bare except patterns: {bare_except_hits}")

    if ".claude/worktrees/" in rel_path:
        return "archived_dead", ["Mirror copy under .claude/worktrees"]

    if path_lower.startswith("control/") and "quantum" in path_lower:
        return "experimental_research", reasons + ["High-risk control/quantum module"]

    if "self_modifying" in path_lower or "self_evolving" in path_lower:
        return "experimental_research", reasons + ["Autonomous self-modification/evolution module"]

    production_prefixes = (
        "main.py",
        "jarvis_brain.py",
        "launchers/",
        "api/",
        "memory/",
        "grpc_service/",
        "whatsapp/",
        "core/",
        "web/",
    )
    if rel_path in {"main.py", "jarvis_brain.py"} or rel_path.startswith(production_prefixes[2:]):
        if any([todo_hits > 0, pass_hits > 5, bare_except_hits > 0]):
            return "usable_minor_fixes", reasons or ["Needs hardening cleanup"]
        return "usable_now", reasons or ["Runtime-relevant path with no major static smell"]

    if rel_path.startswith("tests/") or rel_path.startswith("scripts/"):
        return "usable_minor_fixes", reasons or ["Support/testing code"]

    if rel_path.startswith("skills/"):
        if "assets/boilerplate" in path_lower:
            return "archived_dead", reasons + ["Skill boilerplate asset"]
        if todo_hits > 0 or pass_hits > 0:
            return "experimental_research", reasons + ["Skill implementation incomplete"]
        return "usable_minor_fixes", reasons or ["Skill code requires per-skill validation"]

    if reasons:
        return "usable_minor_fixes", reasons
    return "usable_now", ["No major static red flags"]


def collect_capabilities(root: Path) -> Dict[str, Dict[str, object]]:
    checks = {
        "api_message_processing": {
            "file": "api/services/chat_service.py",
            "patterns": [r"class\s+ChatService", r"async\s+def\s+send_message"],
            "description": "Chat message persistence + orchestrator response flow",
        },
        "grpc_bridge": {
            "file": "grpc_service/python_server.py",
            "patterns": [r"class\s+OrchestratorProxy", r"grpc"],
            "description": "gRPC gateway between clients and orchestrator",
        },
        "whatsapp_bridge": {
            "file": "whatsapp/baileys_bridge.js",
            "patterns": [r"makeWASocket", r"CircuitBreaker"],
            "description": "WhatsApp integration with circuit breaker",
        },
        "memory_hybrid": {
            "file": "memory/memory_controller.py",
            "patterns": [r"GraphRAG", r"ColBERTRetriever", r"pin_context|pinned_contexts"],
            "description": "Hybrid memory with retrieval and context pinning",
        },
        "system2_reasoning": {
            "file": "core/system2_thinking.py",
            "patterns": [r"MCTS", r"class\s+MCTSNode"],
            "description": "System-2 style reasoning (MCTS/PRM-inspired)",
        },
        "speculative_decoding": {
            "file": "core/speculative_decoder.py",
            "patterns": [r"class\s+SpeculativeDecoder|speculative"],
            "description": "Speculative decoding optimization",
        },
        "autonomy_execution": {
            "file": "core/autonomous_executor.py",
            "patterns": [r"class\s+AutonomousExecutor", r"execute_goal"],
            "description": "Goal decomposition and autonomous execution",
        },
        "desktop_control": {
            "file": "control/advanced_chrome_controller.py",
            "patterns": [r"class\s+AdvancedChromeController", r"pyautogui|win32gui"],
            "description": "Desktop/browser control automation",
        },
        "self_modifying_code": {
            "file": "core/self_modifying_evolution.py",
            "patterns": [r"class\s+EvolutionaryCodeEngine", r"mutate_algorithm"],
            "description": "Self-modifying code engine (experimental)",
        },
    }

    results: Dict[str, Dict[str, object]] = {}
    for name, meta in checks.items():
        file_path = root / meta["file"]
        if not file_path.exists():
            results[name] = {
                "status": "missing",
                "file": meta["file"],
                "description": meta["description"],
                "evidence": [],
            }
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        evidence = [pat for pat in meta["patterns"] if re.search(pat, text, flags=re.IGNORECASE)]
        status = "implemented" if len(evidence) == len(meta["patterns"]) else "partial"
        if name in {"self_modifying_code", "desktop_control"} and status != "missing":
            readiness = "beta_only"
        elif status == "implemented":
            readiness = "launch_candidate"
        else:
            readiness = "needs_validation"
        results[name] = {
            "status": status,
            "readiness": readiness,
            "file": meta["file"],
            "description": meta["description"],
            "evidence": evidence,
        }
    return results


def build_report(root: Path, include_mirrors: bool) -> Dict[str, object]:
    file_audits: List[FileAudit] = []
    dedupe_map: Dict[str, List[str]] = defaultdict(list)
    partition_counter = Counter()
    ext_counter = Counter()

    for path in iter_code_files(root):
        rel = normalize_rel_path(path, root)
        mirror = is_mirror_path(rel)
        if mirror and not include_mirrors:
            continue
        content = safe_read_text(path)
        dedupe = sampled_file_signature(path)
        dedupe_map[dedupe].append(rel)

        partition = path_partition(rel)
        usability, reasons = classify_file(rel, content)
        file_audits.append(
            FileAudit(
                path=rel,
                partition=partition,
                is_mirror=mirror,
                dedupe_key=dedupe,
                usability=usability,
                reasons=reasons,
            )
        )
        partition_counter[partition] += 1
        ext_counter[path.suffix.lower()] += 1

    usability_counter = Counter(f.usability for f in file_audits)
    duplicate_groups = [paths for paths in dedupe_map.values() if len(paths) > 1]
    mirror_count = sum(1 for f in file_audits if f.is_mirror)
    unique_files = len(dedupe_map)

    by_partition = defaultdict(lambda: Counter())
    for f in file_audits:
        by_partition[f.partition][f.usability] += 1

    capabilities = collect_capabilities(root)

    return {
        "summary": {
            "total_code_files_scanned": len(file_audits),
            "unique_content_fingerprints": unique_files,
            "duplicate_groups": len(duplicate_groups),
            "mirror_files_scanned": mirror_count,
            "include_mirrors": include_mirrors,
        },
        "counts_by_extension": dict(ext_counter),
        "counts_by_partition": dict(partition_counter),
        "usability_counts": dict(usability_counter),
        "usability_by_partition": {k: dict(v) for k, v in by_partition.items()},
        "capabilities": capabilities,
        "sample_duplicate_groups": duplicate_groups[:20],
        "file_audits": [asdict(f) for f in file_audits],
    }


def to_markdown(report: Dict[str, object]) -> str:
    summary = report["summary"]
    lines: List[str] = []
    lines.append("# Full Repository Audit Report")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total code files scanned: {summary['total_code_files_scanned']}")
    lines.append(f"- Unique content fingerprints: {summary['unique_content_fingerprints']}")
    lines.append(f"- Duplicate groups: {summary['duplicate_groups']}")
    lines.append(f"- Mirror files scanned: {summary['mirror_files_scanned']}")
    lines.append(f"- Mirrors included: {summary['include_mirrors']}")
    lines.append("")

    lines.append("## Usability Counts")
    for key, value in sorted(report["usability_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Partition Overview")
    for partition, count in sorted(report["counts_by_partition"].items()):
        lines.append(f"- {partition}: {count}")
    lines.append("")

    lines.append("## Usability by Partition")
    for partition, counts in sorted(report["usability_by_partition"].items()):
        items = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"- {partition}: {items}")
    lines.append("")

    lines.append("## Capability Truth Map")
    for name, info in sorted(report["capabilities"].items()):
        evidence = "; ".join(info["evidence"]) if info["evidence"] else "none"
        lines.append(
            f"- {name}: status={info['status']}, readiness={info.get('readiness','n/a')}, "
            f"file={info['file']}, evidence={evidence}"
        )
    lines.append("")

    lines.append("## Launch Recommendation")
    lines.append("- Best first launch: single VPS with Docker Compose for API + gRPC + WhatsApp + Redis.")
    lines.append("- Keep high-risk modules (self-modifying and deep desktop control) as beta-only toggles.")
    lines.append("- Promote web app after API/bridge reliability and auth hardening are verified.")
    lines.append("")

    return "\n".join(lines)


def write_outputs(root: Path, report: Dict[str, object]) -> Tuple[Path, Path]:
    analysis_dir = root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    json_path = analysis_dir / "FULL_REPO_AUDIT_REPORT.json"
    md_path = analysis_dir / "FULL_REPO_AUDIT_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full repository audit")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root path",
    )
    parser.add_argument(
        "--include-mirrors",
        action="store_true",
        help="Include mirrored .claude/worktrees files in scan",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root, include_mirrors=args.include_mirrors)
    json_path, md_path = write_outputs(root, report)

    print(f"[OK] JSON report: {json_path}")
    print(f"[OK] Markdown report: {md_path}")
    print("[OK] Full repository audit completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
