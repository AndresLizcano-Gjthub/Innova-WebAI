import logging
import os
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.providers import ProviderError, get_provider
from app.router import choose_route, fallback_models
from app.schemas import OrchestrateRequest, OrchestrateResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("orchestrator")

app = FastAPI(title="IA Gestora / Orquestadora — Web IA INNOVA", version="0.1.0")

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["POST", "GET"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "provider_mode": os.getenv("PROVIDER_MODE", "mock")}


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest):
    start = time.time()
    request_id = str(uuid.uuid4())
    provider = get_provider()
    is_mock = os.getenv("PROVIDER_MODE", "mock").lower() != "real"

    decision = choose_route(req.message)
    model, reason, fallback_used = decision.model, decision.reason, False

    try:
        content = provider.generate(model, req.message)
    except ProviderError as exc:
        log.warning("Falló %s: %s. Probando respaldo.", model, exc)
        content = None
        for backup in fallback_models(model):
            try:
                content = provider.generate(backup, req.message)
                model, fallback_used = backup, True
                reason = f"{reason} (respaldo: falló el modelo principal)"
                break
            except ProviderError:
                continue
        if content is None:
            # Error normalizado sin exponer detalles internos.
            raise HTTPException(status_code=502, detail="Ningún proveedor disponible en este momento.")

    latency_ms = int((time.time() - start) * 1000)
    # Registro de la decisión (el contenido del usuario NO se guarda en logs).
    log.info("req=%s category=%s model=%s fallback=%s latency_ms=%s",
             request_id, decision.category, model, fallback_used, latency_ms)

    return OrchestrateResponse(
        request_id=request_id, content=content, model=model, category=decision.category,
        reason=reason, latency_ms=latency_ms, fallback_used=fallback_used, is_mock=is_mock,
    )
