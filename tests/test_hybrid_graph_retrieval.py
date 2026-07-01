import json
from pathlib import Path

from healf_max.kb.index import build_index
from healf_max.kb.search import search_kb


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "kb"


def test_ingest_writes_frontmatter_link_graph(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    graph = json.loads((tmp_path / "kb_graph.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "kb_manifest.json").read_text(encoding="utf-8"))

    assert manifest["graph_file"] == "kb_graph.json"
    assert manifest["graph_edge_count"] == graph["stats"]["edge_count"]
    assert graph["stats"]["node_count"] == manifest["record_count"]
    assert {
        "source": "endurance_fatigue_plant_based",
        "target": "oura_wearables",
        "field": "wearable_signals",
    } in graph["edges"]


def test_hybrid_search_exposes_bm25_and_graph_hops(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "plant based endurance athlete tired caffeine sensitive low deep sleep low ferritin borderline B12",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=24,
    )

    top = results[0]
    oura = next(record for record in results if record.id == "oura_wearables")

    assert top.id == "endurance_fatigue_plant_based"
    assert any(reason.startswith("bm25:") for reason in top.retrieval_reason)
    assert "graph_hop:wearable_signals:endurance_fatigue_plant_based" in oura.retrieval_reason


def test_specificity_gated_records_do_not_crowd_generic_queries(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "low ferritin tired hyrox deep sleep",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=8,
    )

    assert results[0].id == "hyrox_recovery_bottleneck_with_bloods"
    assert "endurance_fatigue_plant_based" not in [record.id for record in results[:5]]
