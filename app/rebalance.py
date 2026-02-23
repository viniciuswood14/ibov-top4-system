from __future__ import annotations
from dataclasses import dataclass
from typing import List
import pandas as pd
from .config import settings

@dataclass(frozen=True)
class RebalanceConfig:
    target_positions: int = settings.target_positions
    target_weight: float = settings.target_weight

def build_orders(top: List[str], ranking_df: pd.DataFrame, portfolio: dict, cfg: RebalanceConfig | None = None):
    cfg = cfg or RebalanceConfig()
    notes: list[str] = []

    cash = float(portfolio.get("cash_brl", 0.0))
    positions = portfolio.get("positions", [])

    pos_map = {p["ticker"].upper(): p for p in positions}
    price_map = dict(zip(ranking_df["ticker"], ranking_df["last_price"]))

    total_positions_value = sum(float(p["quantity"]) * float(p["last_price"]) for p in pos_map.values())
    total = total_positions_value + cash
    if total <= 0:
        return [], ["Carteira sem valor total (0)."]

    target_value_each = total * cfg.target_weight
    orders = []

    for t, p in pos_map.items():
        if t not in top:
            current_val = float(p["quantity"]) * float(p["last_price"])
            orders.append({"ticker": t, "action": "SELL", "target_value": 0.0, "current_value": current_val, "diff_value": -current_val, "est_qty": float(p["quantity"])})
            notes.append(f"{t} fora do Top {cfg.target_positions} (troca mensal): sugerido vender.")

    for t in top:
        last_price = float(price_map.get(t) or 0.0)
        if last_price <= 0:
            notes.append(f"{t}: sem preço; pulei.")
            continue

        cur_qty = float(pos_map.get(t, {}).get("quantity", 0.0))
        cur_last = float(pos_map.get(t, {}).get("last_price", last_price))
        current_value = cur_qty * cur_last

        diff_value = target_value_each - current_value
        est_qty = diff_value / last_price

        action = "HOLD"
        if diff_value > (0.01 * target_value_each):
            action = "BUY"
        elif diff_value < (-0.01 * target_value_each):
            action = "SELL"

        orders.append({"ticker": t, "action": action, "target_value": target_value_each, "current_value": current_value, "diff_value": diff_value, "est_qty": est_qty})

    orders.sort(key=lambda x: 0 if x["action"]=="SELL" else (1 if x["action"]=="HOLD" else 2))
    return orders, notes
