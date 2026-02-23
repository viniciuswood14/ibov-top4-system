from __future__ import annotations
from datetime import date, datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from .config import settings
from .providers.ibov_b3 import fetch_ibov_tickers
from .providers.brapi import BrapiClient
from .strategy import rank_universe, ScoreWeights
from .schemas import PortfolioInput, RecommendationsResponse, RecommendationItem
from .rebalance import build_orders

app = FastAPI(title="IBOV Top4 System", version="0.1.0-free")

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IBOV Top4</title>
<style>
body { font-family: Arial, sans-serif; max-width: 860px; margin: 36px auto; padding: 0 16px; color:#111; }
.card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin: 14px 0; }
a.btn { display:inline-block; padding:10px 14px; margin:6px 8px 0 0; border-radius:8px; text-decoration:none; border:1px solid #ccc; color:#111; }
code { background:#f5f5f5; padding:2px 6px; border-radius:6px; }
.small { color:#555; }
</style>
</head>
<body>
  <h1>IBOV Top4 — Render Free (Manual)</h1>
  <p>API para ranking (IBOV + momentum 12-1 + fundamentais) e recomendações de rebalanceamento mensal.</p>

  <div class="card">
    <h3>Ações rápidas</h3>
    <a class="btn" href="/health">Health</a>
    <a class="btn" href="/ranking">Ver Ranking (Top 4)</a>
    <a class="btn" href="/docs">Abrir Swagger Docs</a>
    <a class="btn" href="/universe/ibov">Universo IBOV</a>
  </div>

  <div class="card">
    <h3>Como usar</h3>
    <ol>
      <li>Abra <code>/ranking</code> para ver o Top 4.</li>
      <li>Abra <code>/docs</code> e use <code>POST /recommendations</code>.</li>
      <li>Envie seu caixa + posições para receber BUY/SELL/HOLD.</li>
      <li>Salve o JSON do ranking no seu GitHub (manual).</li>
    </ol>
  </div>

  <p class="small">Lembrete: configure a variável de ambiente <code>BRAPI_TOKEN</code> no Render.</p>
</body>
</html>
"""

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.get("/universe/ibov")
def universe_ibov():
    tickers = fetch_ibov_tickers()
    if not tickers:
        raise HTTPException(status_code=502, detail="Não consegui extrair a composição do IBOV da B3.")
    return {"count": len(tickers), "tickers": tickers}

def _get_ranking(as_of: date):
    tickers = fetch_ibov_tickers()
    if not tickers:
        raise HTTPException(status_code=502, detail="Falha ao extrair composição do IBOV (B3).")
    client = BrapiClient(token=settings.brapi_token)
    quotes_hist = client.quote_with_history(tickers, range_="2y", interval="1d")
    quotes_mods = client.quote_with_modules(tickers)
    weights = ScoreWeights(settings.w_quality, settings.w_valuation, settings.w_momentum)
    df = rank_universe(as_of=as_of, quotes_hist=quotes_hist, quotes_modules=quotes_mods, w=weights)
    return df, len(tickers)

@app.get("/ranking")
def ranking(as_of: str | None = None):
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()
    df, universe_size = _get_ranking(as_of_date)
    if df.empty:
        raise HTTPException(status_code=502, detail="Ranking vazio (possível falha de dados da API/mercado).")
    top = df.head(settings.target_positions).to_dict(orient="records")
    return {
        "as_of": as_of_date.isoformat(),
        "universe_size": universe_size,
        "count_ranked": int(df.shape[0]),
        "target_positions": settings.target_positions,
        "top": top,
    }

@app.post("/recommendations", response_model=RecommendationsResponse)
def recommendations(payload: PortfolioInput, as_of: str | None = None):
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()
    df, universe_size = _get_ranking(as_of_date)
    if df.empty:
        raise HTTPException(status_code=502, detail="Ranking vazio (possível falha de dados).")
    top_tickers = df.head(settings.target_positions)["ticker"].tolist()
    orders, notes = build_orders(top_tickers, df, payload.model_dump())
    return RecommendationsResponse(
        as_of=as_of_date.isoformat(),
        top4=top_tickers,
        orders=[RecommendationItem(**o) for o in orders],
        notes=notes + [
            f"Universo IBOV: {universe_size} tickers; ranqueados: {df.shape[0]}.",
            f"Troca mensal ativa: carteira-alvo = Top {settings.target_positions}.",
        ],
    )
