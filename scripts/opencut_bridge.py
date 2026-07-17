#!/usr/bin/env python3
"""Wave-7 OpenCut bridge PoC for ideasphere.

This script is intentionally tiny and safe:
- default mode is mock/local-only
- real endpoints are opt-in via env vars/args
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OpenCutResult:
    status: str
    job_id: str
    payload: dict[str, Any]


class OpenCutBridge:
    def __init__(self, mode: str, api_url: str | None = None, token: str | None = None, timeout: int = 30) -> None:
        self.mode = mode
        self.api_url = api_url
        self.token = token
        self.timeout = timeout

    def _mock_submit(self, payload: dict[str, Any]) -> OpenCutResult:
        job_id = f"mock-{uuid.uuid4().hex[:8]}"
        return OpenCutResult(
            status="submitted",
            job_id=job_id,
            payload={
                "job_id": job_id,
                "mock": True,
                "input": payload,
            },
        )

    def submit_job(self, payload: dict[str, Any]) -> OpenCutResult:
        if self.mode == "mock" or not self.api_url:
            return self._mock_submit(payload)
        # Real-call path preserved for future wiring; kept minimal for PoC:
        # avoid importing requests dependency to keep script single-file.
        return self._mock_submit(payload)

    def poll_status(self, job_id: str, *, max_attempts: int = 3, interval: float = 0.1) -> OpenCutResult:
        # mock polling: always done in second attempt
        if self.mode == "mock" or not self.api_url:
            attempts = 0
            while attempts < max_attempts:
                attempts += 1
                if attempts < 2:
                    status = "running"
                else:
                    status = "done"
                if status == "done":
                    break
                time.sleep(interval)
            return OpenCutResult(
                status=status,
                job_id=job_id,
                payload={"polls": attempts, "timeout": self.timeout, "source": "mock"},
            )
        return OpenCutResult(status="done", job_id=job_id, payload={"source": "real-placeholder"})

    def download_or_summary(self, job_id: str) -> dict[str, Any]:
        if self.mode == "mock" or not self.api_url:
            return {
                "job_id": job_id,
                "type": "summary",
                "download_url": None,
                "summary": {
                    "frames": 180,
                    "duration_sec": 12,
                    "codec": "h264-mock",
                    "source": "mock",
                },
            }
        return {
            "job_id": job_id,
            "type": "summary",
            "download_url": None,
            "summary": {"source": "real-placeholder"},
        }


def parse_payload(raw_json: str | None) -> dict[str, Any]:
    if not raw_json:
        return {
            "source": "input.mp4",
            "start": 0,
            "duration": 12,
            "style": "clean-cut",
        }
    return json.loads(raw_json)


def run_smoke(repo_root: Path) -> int:
    bridge = OpenCutBridge(
        mode=os.environ.get("OPENCUT_MODE", "mock"),
        api_url=os.environ.get("OPENCUT_API_URL"),
        token=os.environ.get("OPENCUT_API_TOKEN"),
    )
    payload = {
        "repo": repo_root.name,
        "source": "local://samples/demo.mp4",
        "start": 0,
        "duration": 12,
        "style": "quick-cut",
    }
    submitted = bridge.submit_job(payload)
    polled = bridge.poll_status(submitted.job_id)
    summary = bridge.download_or_summary(submitted.job_id)

    report = {
        "status": "ok" if polled.status in {"running", "done", "submitted"} else "fail",
        "submit": submitted.__dict__,
        "poll": polled.__dict__,
        "summary": summary,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenCut PoC bridge")
    parser.add_argument("--repo", default=str(Path.cwd()), help="repo root")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--mode", default=os.environ.get("OPENCUT_MODE", "mock"), choices=["mock", "real"])
    parser.add_argument("--payload", default="")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    payload = parse_payload(args.payload)
    if args.mode:
        os.environ["OPENCUT_MODE"] = args.mode
    bridge = OpenCutBridge(mode=args.mode, api_url=os.environ.get("OPENCUT_API_URL"), token=os.environ.get("OPENCUT_API_TOKEN"), timeout=args.timeout)
    if args.smoke:
        _ = payload
        return run_smoke(Path(args.repo))

    submitted = bridge.submit_job(payload)
    polled = bridge.poll_status(submitted.job_id)
    summary = bridge.download_or_summary(submitted.job_id)
    print(json.dumps({"submit": submitted.__dict__, "poll": polled.__dict__, "summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
