from __future__ import annotations
from typing import List, Dict
import math
import statistics

def _mad(values: List[float]) -> float:
    med = statistics.median(values) if values else 0.0
    dev = [abs(v - med) for v in values]
    return statistics.median(dev) if dev else 0.0

def _robust_z(values: List[float]) -> List[float]:
    if not values:
        return []
    med = statistics.median(values)
    mad = _mad(values) or 1.0
    return [(v - med) / (1.4826 * mad) for v in values]

def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

def compute_heat(narratives: List[Dict]) -> List[Dict]:
    vols = [n['signals'].get('onchainVolumeUsd', 0.0) for n in narratives]
    liqs = [n['signals'].get('onchainLiquidityUsd', 0.0) for n in narratives]
    zv = _robust_z(vols)
    zl = _robust_z(liqs)
    out = []
    for i, n in enumerate(narratives):
        x = 0.6 * zv[i] + 0.4 * zl[i]
        heat = round(100 * _sigmoid(x), 1)
        m = dict(n)
        m['heatScore'] = heat
        out.append(m)
    return out
