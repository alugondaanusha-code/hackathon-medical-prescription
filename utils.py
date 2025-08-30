powershell -Command "@'
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

FREQ_MAP = {
    "once": 1, "twice": 2, "thrice": 3,
    "od": 1, "bd": 2, "tid": 3, "qid": 4,
    "daily": 1, "per day": 1
}

def load_db(path: str = "datasets/drug_data.json") -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def norm(s: str) -> str:
    return re.sub(r"\\s+", " ", s.strip()).lower()

def find_known_drug(token: str, db: Dict) -> Optional[str]:
    token_l = norm(token)
    for d in db["drugs"]:
        names = [d["name"]] + d.get("aliases", [])
        for n in names:
            if norm(n) == token_l:
                return d["name"]
    return None

def tokens_from_text(text: str) -> List[str]:
    # keep words like 500mg, 2x, etc.
    return re.findall(r"[A-Za-z][A-Za-z\\-]*|\\d+\\.?\\d*|mg|mcg|g|x|/|day|daily|hours|hourly|every", text, flags=re.I)

def parse_prescription(text: str, db: Dict) -> List[Dict]:
    """
    Very simple extractor:
    - finds known drug names appearing in text
    - captures nearest dose like 500 mg
    - captures simple frequency (twice daily, 2x daily, every 8 hours)
    """
    toks = tokens_from_text(text)
    results = []
    i = 0
    while i < len(toks):
        t = toks[i]
        # Try single- or double-token drug names (e.g., "Paracetamol", "Amoxicillin", "Acetaminophen")
        cand = t
        drug = find_known_drug(cand, db)
        if not drug and i + 1 < len(toks):
            cand2 = f"{t} {toks[i+1]}"
            drug = find_known_drug(cand2, db)
            if drug:
                i += 1  # consumed two tokens

        if drug:
            # look ahead for dose
            dose_mg = None
            freq = None
            look = toks[i+1 : i+8]
            # dose like 500 mg / 0.5 g / 250mcg
            m = re.search(r"(\\d+\\.?\\d*)\\s*(mg|mcg|g)", " ".join(look), flags=re.I)
            if m:
                val = float(m.group(1))
                unit = m.group(2).lower()
                if unit == "g":
                    dose_mg = int(val * 1000)
                elif unit == "mcg":
                    dose_mg = int(val / 1000)
                else:
                    dose_mg = int(val)
            # frequency like "twice daily", "2x daily", "every 8 hours"
            text_look = " ".join(look).lower()
            # words
            for k,v in FREQ_MAP.items():
                if k in text_look:
                    freq = v
                    break
            # 2x daily
            m2 = re.search(r"(\\d+)\\s*x\\s*(?:daily|/\\s*day)?", text_look)
            if m2:
                freq = int(m2.group(1))
            # every N hours
            m3 = re.search(r"every\\s*(\\d+)\\s*hours?", text_look)
            if m3:
                h = int(m3.group(1))
                if h > 0:
                    freq = max(1, round(24/h))

            results.append({"drug": drug, "dose_mg": dose_mg, "frequency_per_day": freq})
        i += 1
    # deduplicate by drug, keep first details
    seen = {}
    for r in results:
        seen.setdefault(r["drug"], r)
    return list(seen.values())

def age_group(age: int) -> str:
    if age < 13: return "child"
    if age < 18: return "adolescent"
    if age < 65: return "adult"
    return "senior"
'@ | Set-Content -Encoding UTF8 utils.py"
