from pathlib import Path

from healf_max.kb.index import build_index
from healf_max.kb.loader import load_kb_records
from healf_max.kb.search import search_kb
from healf_max.kb.validator import validate_kb


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "kb"


def test_step02_kb_records_have_required_typed_frontmatter() -> None:
    records = load_kb_records(KB_DIR)

    assert len(records) >= 46
    assert all(record.type for record in records)
    assert all(record.status == "active" for record in records)
    assert all(record.content_hash for record in records)
    assert any(record.id == "brand.context_pack" for record in records)
    assert any(record.id == "hyrox_recovery_bottleneck_with_bloods" for record in records)


def test_step02_validation_counts_types_and_allows_warnings() -> None:
    result = validate_kb(KB_DIR)

    assert result.ok is True
    assert result.record_count >= 46
    assert result.counts_by_type["evidence_claim"] >= 10
    assert result.counts_by_type["biomarker"] >= 6
    assert result.counts_by_type["product_category"] >= 8
    assert result.counts_by_type["brand_signal"] >= 5
    assert result.errors == []


def test_step02_ingest_writes_manifest_and_jsonl(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    count = build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    assert count >= 46
    assert (tmp_path / "kb_index.jsonl").exists()
    assert (tmp_path / "kb_manifest.json").exists()
    assert (tmp_path / "kb_embeddings.npy").exists() is False


def test_step02_search_prioritises_hyrox_bloods_records(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "low ferritin tired hyrox deep sleep",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=12,
    )
    paths = [record.path for record in results]

    assert paths[0] == "moments/hyrox_recovery_bottleneck_with_bloods.md"
    assert "biomarkers/ferritin.md" in paths[:5]
    assert "evidence/ferritin_low_fatigue.md" in paths[:8]
    assert "products/magnesium_glycinate.md" in paths[:12]
    assert all(record.retrieval_reason for record in results)


def test_step02_search_balances_brand_trace_records(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "low ferritin tired hyrox deep sleep",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=20,
    )
    types = {record.type for record in results}

    assert "editorial_signal" in types
    assert "trust_signal" in types
    assert "tone_pattern" in types
    assert "brand_signal" in types
    assert "editorial/stop_leaking_recovery.md" in [record.path for record in results]
    assert "trust/curated_not_random.md" in [record.path for record in results]
    assert "tone/group_chat_signal.md" in [record.path for record in results]


def test_step02_brand_source_paths_are_portable() -> None:
    brand_records = [record for record in load_kb_records(KB_DIR) if record.type == "brand_signal"]

    assert len(brand_records) == 5
    assert all(str(record.frontmatter["source_path"]).startswith("supplied/brand/") for record in brand_records)
    assert all(not str(record.frontmatter["source_path"]).startswith("/") for record in brand_records)


def test_net_new_endurance_plant_based_knowledge_is_typed() -> None:
    records = {record.id: record for record in load_kb_records(KB_DIR)}

    assert records["endurance_fatigue_plant_based"].type == "wellbeing_moment"
    assert records["oura_wearables"].type == "wearable_signal"
    assert records["hyrox_recovery_guide"].type == "editorial_signal"
    assert records["iron_support"].type == "product_category"
    assert records["b12_contextual"].type == "product_category"
    assert "plant_based" in records["b12"].frontmatter["population_risk"]
    assert records["ferritin"].frontmatter["bands"]["low"].startswith("<15")
    assert "wearable_signal" in validate_kb(KB_DIR).counts_by_type


def test_net_new_endurance_plant_based_search_path(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "plant based endurance athlete tired caffeine sensitive low deep sleep low ferritin borderline B12",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=24,
    )
    paths = [record.path for record in results]

    assert paths[0] == "moments/endurance_fatigue_plant_based.md"
    assert "signals/oura_wearables.md" in paths
    assert "editorial/hyrox_recovery_guide.md" in paths
    assert "products/iron_support.md" in paths
    assert "products/b12_contextual.md" in paths
    assert "biomarkers/b12.md" in paths
