from pydantic import BaseModel, Field


class OrchestrateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=50_000)


class OrchestrateResponse(BaseModel):
    request_id: str
    content: str
    model: str
    category: str
    reason: str
    latency_ms: int
    fallback_used: bool = False
    is_mock: bool = False
