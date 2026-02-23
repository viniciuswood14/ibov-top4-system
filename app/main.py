from __future__ import annotations

from datetime import date, datetime

from fastapi import FastAPI, HTTPException

from .config import settings
from .providers.ibov_b3 import fetch_ibov_tickers
from .providers.brapi import BrapiClient
from .strategy import rank_universe, ScoreWeights
from .schemas import PortfolioInput, RecommendationsResponse, RecommendationItem
from .rebalance import build_orders

app = FastAPI(title="IBOV Top4 System", version="0.1.0-free")


@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.get("/universe/ibov")
def universe_ibov():
    tickers = fetch_ibov_tickers()
    if not tickers:
        raise HTTPException(
            status_code=502,
            detail="Não consegui extrair a composição do IBOV da B3.",
        )
    return {"count": len(tickers), "tickers": tickers}


def _get_ranking(as_of: date):
    tickers = fetch_ibov_tickers()
    if not tickers:
        raise HTTPException(
            status_code=502,
            detail="Falha ao extrair composição do IBOV (B3).",
        )

    client = BrapiClient(token=settings.brapi_token)

    # Histórico (para momentum 12-1)
    quotes_hist = client.quote_with_history(tickers, range_="2y", interval="1d")

    # Fundamentais / módulos (para score de qualidade + valuation)
    quotes_mods = client.quote_with_modules(tickers)

    weights = ScoreWeights(
        quality=settings.w_quality,
        valuation=settings.w_valuation,
        momentum=settings.w_momentum,
    )

    df = rank_universe(
        as_of=as_of,
        quotes_hist=quotes_hist,
        quotes_modules=quotes_mods,
        w=weights,
    )

    return df, len(tickers)


@app.get("/ranking")
def ranking(as_of: str | None = None):
    """
    Retorna o ranking atual (ou em uma data específica) e o Top N (default = 4).
    Ex.: /ranking?as_of=2026-02-23
    """
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()

    df, universe_size = _get_ranking(as_of_date)

    if df.empty:
        raise HTTPException(
            status_code=502,
            detail="Ranking vazio (possível falha de dados da API/mercado).",
        )

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
    """
    Recebe a carteira atual (caixa + posições) e devolve ordens sugeridas
    para rebalancear no Top 4 (troca mensal).
    """
    as_of_date = date.fromisoformat(as_of) if as_of else date.today()

    df, universe_size = _get_ranking(as_of_date)
    if df.empty:
        raise HTTPException(
            status_code=502,
            detail="Ranking vazio (possível falha de dados).",
        )

    top_n = df.head(settings.target_positions)
    top_tickers = top_n["ticker"].tolist()

    orders, notes = build_orders(top_tickers, df, payload.model_dump())

    return RecommendationsResponse(
        as_of=as_of_date.isoformat(),
        top4=top_tickers,  # mantém compatibilidade com schema atual
        orders=[RecommendationItem(**o) for o in orders],
        notes=notes
        + [
            f"Universo IBOV: {universe_size} tickers; ranqueados: {df.shape[0]}.",
            f"Troca mensal ativa: carteira-alvo = Top {settings.target_positions}.",
        ],
    )