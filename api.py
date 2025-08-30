powershell -Command "@'
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from model import Analyzer

app = FastAPI(title="AI Medical Prescription Verifier")
analyzer = Analyzer()

class DrugItem(BaseModel):
    drug: str
    dose_mg: Optional[int] = None
    frequency_per_day: Optional[int] = None

class AnalyzeRequest(BaseModel):
    age: int = Field(..., ge=0, le=120)
    prescription_text: Optional[str] = None
    drugs: Optional[List[DrugItem]] = None
    # Optional tokens if you want to pass per-request (backend also reads env)
    hf_token: Optional[str] = None
    ibm_api_key: Optional[str] = None
    ibm_url: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    items = analyzer.extract(req.prescription_text, [d.dict() for d in req.drugs] if req.drugs else None)
    result = analyzer.check(items, req.age)
    return {"age": req.age, **result}
'@ | Set-Content -Encoding UTF8 api.py"
