import json
from pathlib import Path

from healf_max.kb.index import build_index
from healf_max.kb.loader import load_kb_records
from healf_max.kb.search import search_kb
from healf_max.kb.validator import validate_kb


ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "kb"


EXPECTED_PRODUCT_IDS = {
    "lmnt_recharge_electrolytes",
    "pure_encapsulations_magnesium_glycinate",
    "thorne_creatine",
    "momentous_creatine",
    "thorne_creatine_travel_packs_nsf",
    "bare_biology_life_soul_high_strength_omega_3",
    "nordic_naturals_ultimate_omega",
    "momentous_omega_3",
    "momentous_magnesium_l_threonate",
    "thorne_magnesium_glycinate",
    "pure_encapsulations_one_multivitamin",
    "momentous_multivitamin",
    "blueprint_longevity_mix_blood_orange",
    "blueprint_essential_capsules",
    "h2tab_molecular_hydrogen_tablets",
    "pure_encapsulations_nac_600mg",
    "momentous_grass_fed_whey_protein_isolate",
    "pure_encapsulations_one_omega",
    "niagen_bioscience_tru_niagen_pro_1000mg",
    "biocare_bioacidophilus",
}


def test_product_catalogue_records_are_typed_and_portable() -> None:
    records = load_kb_records(KB_DIR)
    products = [record for record in records if record.type == "product"]

    assert {record.id for record in products} == EXPECTED_PRODUCT_IDS
    assert len(products) == 20
    assert all(record.path.startswith("products/catalogue/") for record in products)
    assert all(record.frontmatter["catalogue_snapshot"] == "healf_best_sellers_2026_06_30" for record in products)
    assert all(str(record.frontmatter["source_path"]).startswith("supplied/scaffold/kb/products/") for record in products)
    assert all(not str(record.frontmatter["source_path"]).startswith("/") for record in products)
    assert all(record.frontmatter.get("category_routes") for record in products)
    assert all("no_live_stock_or_pricing_claims" in record.frontmatter["safety_boundary"] for record in products)


def test_product_catalogue_strict_validation_and_graph_links(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    validation = validate_kb(KB_DIR, strict=True)
    assert validation.ok is True
    assert validation.counts_by_type["product"] == 20

    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)
    graph = json.loads((tmp_path / "kb_graph.json").read_text(encoding="utf-8"))

    assert {
        "source": "electrolytes",
        "target": "lmnt_recharge_electrolytes",
        "field": "catalogue_products",
    } in graph["edges"]
    assert {
        "source": "lmnt_recharge_electrolytes",
        "target": "electrolytes",
        "field": "category_routes",
    } in graph["edges"]


def test_product_search_surfaces_specific_catalogue_products(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "LMNT electrolytes sodium hydration hot day",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=12,
    )

    assert results[0].id == "lmnt_recharge_electrolytes"
    assert "electrolytes" in [record.id for record in results[:6]]
    assert all(record.retrieval_reason for record in results)


def test_category_search_pulls_linked_product_snapshots(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "hyrox recovery creatine protein electrolytes",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=24,
    )
    ids = [record.id for record in results]

    assert "creatine" in ids
    assert "electrolytes" in ids
    assert "protein" in ids
    assert "lmnt_recharge_electrolytes" in ids
    assert "thorne_creatine" in ids or "momentous_creatine" in ids
    assert "momentous_grass_fed_whey_protein_isolate" in ids


def test_longevity_query_retrieves_longevity_category_and_snapshot(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    build_index(kb_dir=KB_DIR, storage_dir=tmp_path)

    results = search_kb(
        "premium longevity NAD cellular energy niagen",
        kb_dir=KB_DIR,
        storage_dir=tmp_path,
        limit=12,
    )
    ids = [record.id for record in results]

    assert ids[0] == "niagen_bioscience_tru_niagen_pro_1000mg"
    assert "longevity_support" in ids[:6]
