import csv
from pathlib import Path
import random
from typing import Dict, List, Optional, Set, Tuple, Union


def group_aware_split(
    items: List[Dict],
    group_key: str = "collection_session",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Performs group-aware splitting to ensure all images from the same collection session / route
    stay strictly within ONE split (preventing data leakage across adjacent video frames).
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"

    # Group items by session / group identifier
    groups: Dict[str, List[Dict]] = {}
    for item in items:
        g = item.get(group_key) or item.get("file_name", "").split("_")[0]
        groups.setdefault(g, []).append(item)

    group_keys = sorted(list(groups.keys()))
    rng = random.Random(seed)
    rng.shuffle(group_keys)

    total_items = len(items)
    target_train = int(total_items * train_ratio)
    target_val = int(total_items * val_ratio)

    train_set, val_set, test_set = [], [], []

    for g_key in group_keys:
        g_items = groups[g_key]
        if len(train_set) + len(g_items) <= target_train or (len(val_set) >= target_val and len(train_set) < target_train):
            train_set.extend(g_items)
        elif len(val_set) + len(g_items) <= target_val:
            val_set.extend(g_items)
        else:
            test_set.extend(g_items)

    # In case any group remained
    for g_key in group_keys:
        g_items = groups[g_key]
        if g_items[0] not in train_set and g_items[0] not in val_set and g_items[0] not in test_set:
            test_set.extend(g_items)

    return train_set, val_set, test_set


def create_deterministic_subsets(
    train_items: List[Union[str, Dict]],
    fractions: Tuple[float, ...] = (0.10, 0.25, 0.50, 1.00),
    seeds: Tuple[int, ...] = (42, 123, 999),
) -> Dict[int, Dict[float, List]]:
    """
    Generates deterministic stratified subsets (10%, 25%, 50%, 100%) for Experiment 4
    across multiple random seeds to build sample-efficiency learning curves.
    """
    subsets_by_seed: Dict[int, Dict[float, List]] = {}

    for seed in seeds:
        rng = random.Random(seed)
        shuffled = list(train_items)
        rng.shuffle(shuffled)

        subsets_by_seed[seed] = {}
        for frac in fractions:
            if frac >= 1.0:
                subsets_by_seed[seed][frac] = list(shuffled)
            else:
                k = max(1, int(round(len(shuffled) * frac)))
                subsets_by_seed[seed][frac] = shuffled[:k]

    return subsets_by_seed


def export_split_txt(
    file_list: List[Union[str, Path, Dict]],
    output_txt_path: Union[str, Path],
    images_base_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Exports list of image paths to a YOLO-compatible split text file."""
    output_txt_path = Path(output_txt_path)
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for item in file_list:
        if isinstance(item, dict):
            rel_name = item.get("file_name") or item.get("filename")
            if images_base_dir:
                p = Path(images_base_dir) / rel_name
            else:
                p = Path(rel_name)
        else:
            p = Path(item)
        lines.append(str(p).replace("\\", "/"))

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
