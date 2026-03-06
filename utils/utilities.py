from __future__ import annotations
from typing import Dict, Any, Iterable
import copy


def subset_top_keys_safe(d: Dict[str, Any], keep: Iterable[str], *, strict: bool = False) -> Dict[str, Any]:
    """
    Return a NEW dict containing only the requested top-level keys, with a DEEP COPY
    of the retained subtrees so mutating the result cannot affect the original.

    strict=True -> raise KeyError if any requested key is missing.
    strict=False -> ignore missing keys.
    """
    keep_set = set(keep)
    if "peso" in keep_set:
        keep_set.add("Base")
    if "Junior" in keep_set:
        keep_set.add("Junior_carie")
        keep_set.add("Junior_intolleranze")
        keep_set.add("Junior_fragilita")
        keep_set.add("Junior_sindrome_met")

    print("Requested keys for subset:", keep_set)

    if strict:
        missing = keep_set.difference(d.keys())
        if missing:
            raise KeyError(f"Requested keys not found: {sorted(missing)}")

    subset = {k: d[k] for k in d.keys() if k in keep_set}
    return copy.deepcopy(subset)
