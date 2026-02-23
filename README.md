# IBOV 12-1 (momentum) + Fundamentais (automático) — Top 4 + Troca Mensal

MVP pronto para subir no **Render** (Web Service + Postgres + Cron Job) e hospedar um sistema que:

- Baixa o **universo do IBOV** (composição) a partir da página oficial da B3
- Consulta preços e dados fundamentalistas via **brapi.dev**
- Calcula **momentum 12-1**
- Calcula um **score** (Qualidade + Valuation + Momentum)
- Seleciona **Top 4** e recomenda **troca mensal**
- Gera **ordens sugeridas** para rebalancear (25% cada)

> Você precisa de um token da brapi.dev para produção (para acessar todos os tickers).

## Rodar local
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export BRAPI_TOKEN="SEU_TOKEN"
export DATABASE_URL="sqlite:///./dev.db"  # ou Postgres
uvicorn app.main:app --reload
```

Abra:
- http://127.0.0.1:8000/docs

## Variáveis de ambiente
- `BRAPI_TOKEN` (obrigatório em produção)
- `DATABASE_URL` (Postgres no Render ou SQLite local)
- `TARGET_POSITIONS` (padrão: 4)
- `TARGET_WEIGHT` (padrão: 0.25)
- `SCORE_W_QUALITY` (padrão: 0.4)
- `SCORE_W_VALUATION` (padrão: 0.3)
- `SCORE_W_MOMENTUM` (padrão: 0.3)

## Render
- Web Service: start command `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- Postgres: adicione e coloque `DATABASE_URL` no Environment Group
- Cron Job: comando `python -m cron.run_monthly_rebalance`

## Endpoints
- `GET /universe/ibov`
- `GET /ranking?as_of=YYYY-MM-DD`
- `POST /recommendations` (envia sua carteira/caixa e recebe ordens sugeridas)
- `POST /snapshot/run` (força uma rodada e salva no banco)
