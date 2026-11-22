import numpy as np
import pandas as pd
import pytest

from saham_gorengan.evaluation.splits import Split, loco_splits

T = pd.bdate_range("2024-01-01", periods=300)


def _wins(*pairs):
    return pd.DataFrame({
        "window_id": [f"w{i}" for i in range(len(pairs))],
        "ticker": ["AAAA"] * len(pairs),
        "start": [T[a] if isinstance(a, int) else a for a, _ in pairs],
        "end": [T[b] if isinstance(b, int) else b for _, b in pairs],
    })


def test_hand_example():
    (s,) = loco_splits(T, _wins((100, 109)), lead=20, embargo=60)
    assert isinstance(s, Split)
    assert s.held_out == "w0"
    assert list(s.test_days) == list(T[80:110])
    assert len(s.test_days) == 30
    assert list(s.train_days) == list(T[0:20]) + list(T[170:300])
    assert len(s.train_days) == 150
    assert T[19] in s.train_days and T[20] not in s.train_days
    assert T[169] not in s.train_days and T[170] in s.train_days


def test_window_near_start():
    (s,) = loco_splits(T, _wins((5, 9)), lead=20, embargo=60)
    assert s.test_days[0] == T[0]
    assert list(s.test_days) == list(T[0:10])
    assert list(s.train_days) == list(T[70:300])


def test_window_outside_days_skipped():
    w = _wins((100, 109), (pd.Timestamp("2030-01-01"), pd.Timestamp("2030-02-01")),
              (150, 155))
    splits = loco_splits(T, w)
    assert [s.held_out for s in splits] == ["w0", "w2"]


def test_no_overlap():
    w = _wins((100, 109), (5, 9), (250, 299))
    pos = {d: i for i, d in enumerate(T)}
    for s in loco_splits(T, w, lead=20, embargo=60):
        assert len(s.train_days.intersection(s.test_days)) == 0
        tr = np.array([pos[d] for d in s.train_days])
        te = np.array([pos[d] for d in s.test_days])
        if len(tr) and len(te):
            gap = np.abs(tr[:, None] - te[None, :]).min()
            assert gap > 60


def test_order_and_ids():
    w = _wins((150, 155), (50, 55))
    w["window_id"] = ["zeta", "alpha"]
    splits = loco_splits(T, w)
    assert [s.held_out for s in splits] == ["zeta", "alpha"]


def test_days_unsorted_and_duplicates():
    shuffled = list(T[::-1]) + list(T[:10])
    (s,) = loco_splits(shuffled, _wins((100, 109)))
    assert list(s.test_days) == list(T[80:110])
    assert list(s.train_days) == list(T[0:20]) + list(T[170:300])


def test_inputs_not_modified():
    w = _wins((100, 109))
    before = w.copy()
    loco_splits(T, w)
    pd.testing.assert_frame_equal(w, before)


def test_bad_args():
    w = _wins((100, 109))
    with pytest.raises(ValueError):
        loco_splits(T, w, lead=-1)
    with pytest.raises(ValueError):
        loco_splits(T, w, embargo=True)
    with pytest.raises(ValueError):
        loco_splits(T, w.drop(columns=["end"]))
    dup = pd.concat([w, w], ignore_index=True)
    with pytest.raises(ValueError):
        loco_splits(T, dup)
