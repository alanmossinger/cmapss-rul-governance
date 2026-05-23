"""FastAPI service entry point."""
from fastapi import FastAPI

from cmapss_rul import __version__

app = FastAPI(
    title="C-MAPSS RUL Prediction Service",
    description=(
        "Industrial AI predictive maintenance with governance-by-design. "
        "NIST AI RMF + EU AI Act aligned."
    ),
    version=__version__,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "cmapss-rul-predictor",
        "docs": "/docs",
        "governance": "See /governance directory in repository",
    }
