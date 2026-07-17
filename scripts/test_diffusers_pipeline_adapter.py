from pathlib import Path
import json

from scripts.diffusers_pipeline_adapter import parse_blocks, build_manifest


def test_parse_blocks_with_pipeline_and_section_aliases(tmp_path: Path):
    payload = {
        "pipeline": {
            "before_denoise": [
                {"path": "tests/fixtures/anima.py", "weight": 1, "block_id": "d1"},
                {"path": "tests/fixtures/noise.py", "weight": 2}
            ],
            "sampler": {"path": "sampler/sd.py"},
        }
    }
    blocks = parse_blocks(payload)
    assert len(blocks) == 3
    assert [b.block_id for b in blocks] == ["d1", "before_denoise-1", "sampler-0"]
    assert blocks[0].block_type == "before_denoise"
    assert blocks[1].block_type == "before_denoise"
    assert blocks[2].block_type == "sampler"


def test_build_manifest_contains_expected_contract(tmp_path: Path):
    payload = {
        "blocks": [
            {"block_type": "before_denoise", "block_id": "bd", "path": "a/b/c.py", "weight": 3},
            {"block_type": "unknown", "path": "x/y.py", "weight": 1},
        ]
    }
    out = build_manifest(payload, title="test")
    assert out["title"] == "test"
    assert out["total"] == 2
    assert out["stages"][0]["stage_type"] in {"before_denoise", "unknown"}
    # 在该输入中，最后一项是 unknown 类型块（顺序按权重/类型稳定）
    assert out["stages"][-1]["stage_type"] == "unknown"
    assert out["stages"][-1]["stage_type"] == "unknown"


def test_load_and_dump_roundtrip(tmp_path: Path):
    payload = {
        "before_denoise": [
            {"block_id": "a", "path": "p1"},
            {"block_id": "b", "path": "p2", "block_type": "before_denoise"},
        ]
    }
    json_path = tmp_path / "payload.json"
    json_path.write_text(json.dumps(payload), encoding="utf-8")
    read = json.loads(json_path.read_text(encoding="utf-8"))
    manifest = build_manifest(read, title="rt")
    assert manifest["block_types"] == ["before_denoise"]
    assert len(manifest["stages"]) == 2
    assert manifest["stages"][0]["source_file"] == ""
    assert manifest["stages"][1]["entry_path"] == "p2"
