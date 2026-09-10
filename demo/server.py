"""AgentPay pitch console — local HTTP API + static UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import require_operator, require_reader
from engine import AgentPayEngine

STATIC = Path(__file__).resolve().parent / "static"
engine = AgentPayEngine()
app = FastAPI(title="AgentPay Demo", version="0.1.0")


class DiscoverBody(BaseModel):
    query: str = ""


class PayBody(BaseModel):
    resource_id: str
    params: str = "{}"


@app.get("/api/state")
def state():
    return engine.snapshot()


@app.post("/api/reset")
def reset(_: str = Depends(require_operator)):
    return engine.reset_demo()


@app.post("/api/discover")
def discover(body: DiscoverBody, _: str = Depends(require_reader)):
    return {"query": body.query, "results": engine.discover(body.query)}


@app.get("/api/budget")
def budget(_: str = Depends(require_reader)):
    snap = engine.snapshot()
    return {
        "remaining_stroops": snap["remaining_stroops"],
        "remaining_xlm": snap["remaining_xlm"],
        "period_ledgers": snap["period_ledgers"],
        "rule_count": snap["rule_count"],
        "rules": snap["rules"],
    }


@app.post("/api/generate-policy")
def generate_policy(_: str = Depends(require_operator)):
    return engine.generate_policy()


@app.post("/api/pay")
def pay(body: PayBody, _: str = Depends(require_operator)):
    try:
        return engine.pay_and_call(body.resource_id, body.params)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Resource not found: {body.resource_id}")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8080, reload=False)
