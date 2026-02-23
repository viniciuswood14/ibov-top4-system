from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class ScoreWeights:
    quality: float = 0.4
    valuation: float = 0.3
    momentum: float = 0.3

def _safe_float(x: Any) -> float:
    try:
        if x is None:
            return float("nan")
        return float(x)
    except Exception:
        return float("nan")

def compute_momentum_12_1(historical: list[dict[str,Any]], as_of: date) -> float:
    """Momentum 12-1 (retorno ~12m terminando ~1m atrás) usando série diária."""
    if not historical:
        return float("nan")
    df = pd.DataFrame(historical)
    if df.empty or "date" not in df.columns or "close" not in df.columns:
        return float("nan")

    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.dropna(subset=["date","close"]).sort_values("date")

    start_target = pd.Timestamp(as_of) - pd.DateOffset(months=13)
    end_target   = pd.Timestamp(as_of) - pd.DateOffset(months=1)

    start_df = df[df["date"] <= start_target]
    end_df   = df[df["date"] <= end_target]
    if start_df.empty or end_df.empty:
        return float("nan")

    start_px = float(start_df.iloc[-1]["close"])
    end_px   = float(end_df.iloc[-1]["close"])
    if start_px <= 0:
        return float("nan")
    return (end_px / start_px) - 1.0

def quality_score(stats: dict[str,Any], fin: dict[str,Any]) -> float:
    roe = _safe_float(stats.get("returnOnEquity"))
    margins = _safe_float(fin.get("profitMargins") or stats.get("profitMargins"))
    nde = _safe_float(fin.get("netDebtToEbitda"))

    roe_n = np.clip(roe, 0, 0.30) / 0.20 * 10 if np.isfinite(roe) else np.nan
    roe_n = np.clip(roe_n, 0, 10) if np.isfinite(roe_n) else np.nan

    mar_n = np.clip(margins, 0, 0.25) / 0.15 * 10 if np.isfinite(margins) else np.nan
    mar_n = np.clip(mar_n, 0, 10) if np.isfinite(mar_n) else np.nan

    nde_n = (3 - np.clip(nde, 0, 5)) / 3 * 10 if np.isfinite(nde) else np.nan
    nde_n = np.clip(nde_n, 0, 10) if np.isfinite(nde_n) else np.nan

    parts = [p for p in [roe_n, mar_n, nde_n] if np.isfinite(p)]
    return float(np.mean(parts)) if parts else float("nan")

def valuation_score(stats: dict[str,Any]) -> float:
    pe = _safe_float(stats.get("trailingPE") or stats.get("priceEarnings"))
    pb = _safe_float(stats.get("priceToBook"))

    pe_n = (20 - np.clip(pe, 5, 40)) / 15 * 10 if np.isfinite(pe) else np.nan
    pe_n = np.clip(pe_n, 0, 10) if np.isfinite(pe_n) else np.nan

    pb_n = (2.5 - np.clip(pb, 0.8, 5)) / 1.7 * 10 if np.isfinite(pb) else np.nan
    pb_n = np.clip(pb_n, 0, 10) if np.isfinite(pb_n) else np.nan

    parts = [p for p in [pe_n, pb_n] if np.isfinite(p)]
    return float(np.mean(parts)) if parts else float("nan")

def momentum_score(mom: float) -> float:
    if not np.isfinite(mom):
        return float("nan")
    return float(np.clip((mom + 0.20) / 0.50 * 10, 0, 10))

def rank_universe(as_of: date, quotes_hist: list[dict[str,Any]], quotes_modules: list[dict[str,Any]], w: ScoreWeights) -> pd.DataFrame:
    mod_map = {q.get("symbol"): q for q in quotes_modules if q.get("symbol")}
    rows = []
    for q in quotes_hist:
        sym = q.get("symbol")
        if not sym:
            continue
        mom = compute_momentum_12_1(q.get("historicalDataPrice") or [], as_of=as_of)

        mods = mod_map.get(sym, {})
        stats = mods.get("defaultKeyStatistics") or {}
        fin = mods.get("financialData") or {}

        q_score = quality_score(stats, fin)
        v_score = valuation_score(stats)
        m_score = momentum_score(mom)

        total = float("nan")
        if np.isfinite(q_score) and np.isfinite(v_score) and np.isfinite(m_score):
            total = (w.quality*q_score + w.valuation*v_score + w.momentum*m_score)

        rows.append({
            "ticker": sym,
            "momentum_12_1": mom,
            "score_quality": q_score,
            "score_valuation": v_score,
            "score_momentum": m_score,
            "score_total": total,
            "last_price": q.get("regularMarketPrice"),
            "market_cap": q.get("marketCap"),
            "volume": q.get("regularMarketVolume"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.dropna(subset=["score_total"]).sort_values("score_total", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df
