"""Etap 05: sesje odłożone na pokaz, potoki finalne, metadata.json, kontrola i E5."""
import json

import numpy as np
import pandas as pd
import pytest

import check_models
import e5_audio
import finalize
from experiments import TASKS
from features import PROCESSED, load_flows
from finalize import (HoldoutRule, holdout_mask, keys_from_records, keys_to_records,
                      select_holdout)
from model_store import MODELS_DIR, load_metadata, version_mismatches
from test_train_cli import synthetic_flows, write_features_json
from train import resolve_features, task_frame

# sesje syntetyczne mają 4–6 przepływów, a grupa ok. 50
TEST_RULE = HoldoutRule(min_flows=5, max_share=0.2)
MODELS = ("tree",)


@pytest.fixture(scope="module")
def flows():
    """Dane z test_train_cli plus Video w kampanii Tor-nonTor (zadanie WWW vs Video)."""
    base = synthetic_flows(np.random.default_rng(0))
    video = base[(base["service"] == "Video") & (base["tunnel"] == "plain")]
    return pd.concat([base, video.assign(campaign="tor-nontor", traffic_type="Non-Tor",
                                         session=video["session"] + 1_000)],
                     ignore_index=True)


def with_audio(flows: pd.DataFrame) -> pd.DataFrame:
    """Audio: kopia sesji VoIP z obu tuneli pod innymi numerami sesji."""
    voip = flows[flows["service"] == "VoIP"]
    return pd.concat([flows, voip.assign(service="Audio", session=voip["session"] + 10_000)],
                     ignore_index=True)


def test_select_holdout_is_deterministic_and_follows_the_rule(flows):
    keys = select_holdout(flows, TEST_RULE)

    assert keys.equals(select_holdout(flows, TEST_RULE))
    assert keys.groupby(finalize.HOLDOUT_STRATA).size().eq(TEST_RULE.per_group).all()
    assert len(keys) == TEST_RULE.per_group * flows.groupby(finalize.HOLDOUT_STRATA).ngroups
    group_total = flows.groupby(finalize.HOLDOUT_STRATA).size()
    share = keys["n_flows"] / group_total.loc[
        pd.MultiIndex.from_frame(keys[finalize.HOLDOUT_STRATA])].to_numpy()
    assert (keys["n_flows"] >= TEST_RULE.min_flows).all() and (share < TEST_RULE.max_share).all()


def test_select_holdout_fails_when_a_group_has_too_few_eligible_sessions(flows):
    with pytest.raises(ValueError, match="Za mało sesji"):
        select_holdout(flows, HoldoutRule(min_flows=6, max_share=0.2, per_group=4))


def test_holdout_mask_selects_whole_sessions_from_keys(flows):
    keys = select_holdout(flows, TEST_RULE)
    mask = holdout_mask(flows, keys)

    held_sessions = flows.loc[mask, "session"].unique()
    assert len(held_sessions) == len(keys)
    assert np.array_equal(mask, flows["session"].isin(held_sessions).to_numpy())


def test_session_keys_survive_json_round_trip(flows):
    keys = select_holdout(flows, TEST_RULE)
    records = json.loads(json.dumps(keys_to_records(keys)))

    assert keys_from_records(records).equals(keys)


def test_holdout_mask_rejects_a_key_matching_other_flow_count(flows):
    keys = select_holdout(flows, TEST_RULE).assign(n_flows=lambda k: k["n_flows"] + 1)
    with pytest.raises(ValueError, match="wybiera"):
        holdout_mask(flows, keys)


def test_version_check_ignores_python_patch_but_not_libraries():
    expected = {"python": "3.13.1", "sklearn": "1.9.1"}
    assert version_mismatches(expected, {"python": "3.13.7", "sklearn": "1.9.1"}) == {}
    assert version_mismatches(expected, {"python": "3.14.0", "sklearn": "1.9.0"}) == {
        "python": ("3.13.1", "3.14.0"), "sklearn": ("1.9.1", "1.9.0")}


@pytest.fixture(scope="module")
def trained(tmp_path_factory, flows):
    """Pełny przebieg finalize.py (tylko drzewo) na danych syntetycznych z Audio."""
    root = tmp_path_factory.mktemp("final")
    data_path = root / "data" / "flows.parquet"
    data_path.parent.mkdir()
    with_audio(flows).to_parquet(data_path, index=False)
    write_features_json(data_path, gap_min=5.0)
    results = root / "results"
    for task in finalize.FINAL_TASKS:
        (results / f"e4_bez_skrotow_{task}").mkdir(parents=True)
        pd.DataFrame({"model": list(MODELS), "split": "session", "f1_macro_mean": 0.9,
                      "f1_macro_std": 0.01}).to_csv(
            results / f"e4_bez_skrotow_{task}" / "summary.csv", index=False)
    models_dir = root / "models"
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(finalize, "FINAL_MODELS", MODELS)
        finalize.main(["--data", str(data_path), "--models-dir", str(models_dir),
                       "--results", str(results), "--min-flows", str(TEST_RULE.min_flows),
                       "--max-share", str(TEST_RULE.max_share), "--n-jobs", "1"])
    return data_path, models_dir, root


def test_metadata_describes_every_pipeline_and_the_input_contract(trained):
    _, models_dir, _ = trained
    meta = load_metadata(models_dir)

    assert {(e["task"], e["model"]) for e in meta["pipelines"]} == {
        (t, m) for t in finalize.FINAL_TASKS for m in MODELS}
    assert meta["features"] == resolve_features("bez_skrotow")
    assert set(meta["features"]) <= set(meta["input_columns"])
    assert set(finalize.FILTER_COLUMNS) <= set(meta["input_columns"])
    assert meta["data"]["release"] == "data-processed-v1" and meta["data"]["session_gap_min"] == 5
    assert set(meta["tasks"]) == set(finalize.FINAL_TASKS)
    assert all(e["reported_cv"]["f1_macro_mean"] == 0.9 for e in meta["pipelines"])
    assert meta["git"]["changed_during_run"] is False


def test_pipelines_never_train_on_held_out_sessions(trained, flows):
    _, models_dir, _ = trained
    meta = load_metadata(models_dir)
    held = holdout_mask(flows, keys_from_records(meta["holdout"]["sessions"]))

    for entry in meta["pipelines"]:
        population, _, _ = task_frame(flows, TASKS[entry["task"]])
        kept, _, _ = task_frame(flows[~held], TASKS[entry["task"]])
        assert len(kept) < len(population)
        assert entry["train_flows_per_class"] == kept["service"].value_counts().reindex(
            entry["classes"], fill_value=0).to_dict()


def test_check_models_loads_and_predicts_every_pipeline(trained, capsys):
    data_path, models_dir, _ = trained
    check_models.main(["--data", str(data_path), "--models-dir", str(models_dir)])

    out = capsys.readouterr().out
    assert f"OK: {len(finalize.FINAL_TASKS) * len(MODELS)} potoków" in out


def test_check_models_rejects_a_changed_pipeline_file(trained, tmp_path):
    data_path, models_dir, _ = trained
    meta = load_metadata(models_dir)
    meta["pipelines"][0]["sha256"] = "0" * 64
    (tmp_path / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    for entry in meta["pipelines"]:
        (tmp_path / entry["file"]).write_bytes((models_dir / entry["file"]).read_bytes())

    with pytest.raises(ValueError, match="SHA-256"):
        check_models.main(["--data", str(data_path), "--models-dir", str(tmp_path)])


def test_check_models_rejects_other_library_versions(trained, tmp_path):
    data_path, models_dir, _ = trained
    meta = load_metadata(models_dir)
    meta["versions"]["sklearn"] = "0.0.1"
    (tmp_path / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(RuntimeError, match="sklearn"):
        check_models.main(["--data", str(data_path), "--models-dir", str(tmp_path)])


def test_e5_splits_audio_predictions_by_campaign_and_tunnel(trained):
    data_path, models_dir, root = trained
    e5_audio.main(["--data", str(data_path), "--models-dir", str(models_dir),
                   "--out", str(root / "out")])

    dist = pd.read_csv(root / "out" / e5_audio.OUT_NAME / "distribution.csv")
    audio = load_flows(include_audio=True, path=data_path).query("service == 'Audio'")
    flows_rows = dist[dist["unit"] == "flows"]
    assert set(zip(flows_rows["campaign"], flows_rows["tunnel"])) == set(
        zip(audio["campaign"], audio["tunnel"]))
    assert flows_rows["total"].sum() == len(audio) * len(MODELS)
    assert dist.loc[dist["unit"] == "sessions", "total"].sum() == (
        audio["session"].nunique() * len(MODELS))
    shares = dist.filter(like="share_").sum(axis=1)
    assert np.allclose(shares, 1.0)


@pytest.mark.skipif(not ((MODELS_DIR / "metadata.json").exists()
                         and (PROCESSED / "flows.parquet").exists()),
                    reason="brak models/metadata.json albo flows.parquet")
def test_real_holdout_keys_match_real_flows():
    meta = load_metadata()
    keys = keys_from_records(meta["holdout"]["sessions"])

    assert holdout_mask(load_flows(), keys).sum() == keys["n_flows"].sum()
