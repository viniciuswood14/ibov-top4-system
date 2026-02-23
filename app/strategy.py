from dataclasses import dataclass
from typing import Any
import numpy as np, pandas as pd

@dataclass(frozen=True)
class ScoreWeights:
    quality: float = 0.4
    valuation: float = 0.3
    momentum: float = 0.3

def _safe_float(x: Any) -> float:
    try: return float(x) if x is not None else float("nan")
    except: return float("nan")

def compute_momentum_12_1(historical, as_of):
    if not historical: return float("nan")
    df = pd.DataFrame(historical)
    if df.empty or "date" not in df.columns or "close" not in df.columns: return float("nan")
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.dropna(subset=["date","close"]).sort_values("date")
    s = pd.Timestamp(as_of) - pd.DateOffset(months=13)
    e = pd.Timestamp(as_of) - pd.DateOffset(months=1)
    ds, de = df[df["date"] <= s], df[df["date"] <= e]
    if ds.empty or de.empty: return float("nan")
    sp, ep = float(ds.iloc[-1]["close"]), float(de.iloc[-1]["close"])
    return (ep / sp) - 1.0 if sp > 0 else float("nan")

def quality_score(stats, fin):
    roe = _safe_float(stats.get("returnOnEquity"))
    mar = _safe_float(fin.get("profitMargins") or stats.get("profitMargins"))
    nde = _safe_float(fin.get("netDebtToEbitda"))
    vals = []
    if np.isfinite(roe): vals.append(float(np.clip(np.clip(roe,0,0.30)/0.20*10,0,10)))
    if np.isfinite(mar): vals.append(float(np.clip(np.clip(mar,0,0.25)/0.15*10,0,10)))
    if np.isfinite(nde): vals.append(float(np.clip((3-np.clip(nde,0,5))/3*10,0,10)))
    return float(np.mean(vals)) if vals else float("nan")

def valuation_score(stats):
    pe = _safe_float(stats.get("trailingPE") or stats.get("priceEarnings"))
    pb = _safe_float(stats.get("priceToBook"))
    vals = []
    if np.isfinite(pe): vals.append(float(np.clip((20-np.clip(pe,5,40))/15*10,0,10)))
    if np.isfinite(pb): vals.append(float(np.clip((2.5-np.clip(pb,0.8,5))/1.7*10,0,10)))
    return float(np.mean(vals)) if vals else float("nan")

def momentum_score(mom):
    return float(np.clip((mom+0.20)/0.50*10,0,10)) if np.isfinite(mom) else float("nan")

def rank_universe(as_of, quotes_hist, quotes_modules, w):
    mod_map = {q.get("symbol"): q for q in quotes_modules if q.get("symbol")}
    rows = []
    for q in quotes_hist:
        sym = q.get("symbol")
        if not sym: continue
        mom = compute_momentum_12_1(q.get("historicalDataPrice") or [], as_of)
        mods = mod_map.get(sym, {})
        qs = quality_score(mods.get("defaultKeyStatistics") or {}, mods.get("financialData") or {})
        vs = valuation_score(mods.get("defaultKeyStatistics") or {})
        ms = momentum_score(mom)
        total = (w.quality*qs + w.valuation*vs + w.momentum*ms) if np.isfinite(qs) and np.isfinite(vs) and np.isfinite(ms) else float("nan")
        rows.append({"ticker":sym,"momentum_12_1":mom,"score_quality":qs,"score_valuation":vs,"score_momentum":ms,"score_total":total,"last_price":q.get("regularMarketPrice"),"market_cap":q.get("marketCap"),"volume":q.get("regularMarketVolume")})
    df = pd.DataFrame(rows)
    if df.empty: return df
    df = df.dropna(subset=["score_total"]).sort_values("score_total", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df
