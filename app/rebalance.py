from dataclasses import dataclass
from .config import settings

@dataclass(frozen=True)
class RebalanceConfig:
    target_positions: int = settings.target_positions
    target_weight: float = settings.target_weight

def build_orders(top, ranking_df, portfolio, cfg=None):
    cfg = cfg or RebalanceConfig()
    notes, orders = [], []
    cash = float(portfolio.get("cash_brl", 0.0))
    pos_map = {p["ticker"].upper(): p for p in portfolio.get("positions", [])}
    price_map = dict(zip(ranking_df["ticker"], ranking_df["last_price"]))
    total_pos = sum(float(p["quantity"]) * float(p["last_price"]) for p in pos_map.values())
    total = total_pos + cash
    if total <= 0: return [], ["Carteira sem valor total (0)."]
    target_each = total * cfg.target_weight
    for t, p in pos_map.items():
        if t not in top:
            cur = float(p["quantity"]) * float(p["last_price"])
            orders.append({"ticker":t,"action":"SELL","target_value":0.0,"current_value":cur,"diff_value":-cur,"est_qty":float(p["quantity"])})
            notes.append(f"{t} fora do Top {cfg.target_positions} (troca mensal): sugerido vender.")
    for t in top:
        px = float(price_map.get(t) or 0.0)
        if px <= 0:
            notes.append(f"{t}: sem preço disponível; pulei.")
            continue
        cur_qty = float(pos_map.get(t, {}).get("quantity", 0.0))
        cur_last = float(pos_map.get(t, {}).get("last_price", px))
        cur_val = cur_qty * cur_last
        diff = target_each - cur_val
        est_qty = diff / px
        action = "HOLD"
        if diff > 0.01 * target_each: action = "BUY"
        elif diff < -0.01 * target_each: action = "SELL"
        orders.append({"ticker":t,"action":action,"target_value":target_each,"current_value":cur_val,"diff_value":diff,"est_qty":est_qty})
    orders.sort(key=lambda x: 0 if x["action"]=="SELL" else (1 if x["action"]=="HOLD" else 2))
    return orders, notes
