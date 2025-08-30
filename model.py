powershell -Command "@'
from typing import Dict, List, Optional
from utils import load_db, age_group, parse_prescription
from dataclasses import dataclass
import os

@dataclass
class DrugRecord:
    name: str
    adult_dose: str
    child_dose: str
    aliases: List[str]

class DrugDB:
    def __init__(self, path: str = "datasets/drug_data.json"):
        self.db = load_db(path)

    def list_drugs(self) -> List[str]:
        return [d["name"] for d in self.db["drugs"]]

    def normalize(self, name: str) -> Optional[str]:
        n = name.lower().strip()
        for d in self.db["drugs"]:
            if d["name"].lower() == n or n in [a.lower() for a in d.get("aliases", [])]:
                return d["name"]
        return None

    def default_dose_for_age(self, drug: str, age: int) -> Optional[str]:
        d = next((x for x in self.db["drugs"] if x["name"] == drug), None)
        if not d: return None
        grp = age_group(age)
        if grp in ("child", "adolescent"):
            return d.get("child_dose")
        return d.get("adult_dose")

    def max_daily_mg(self, drug: str, age: int) -> Optional[int]:
        m = self.db.get("max_daily_dose_mg", {}).get(drug)
        if not m: return None
        grp = age_group(age)
        if grp in ("child", "adolescent"):
            return m.get("child")
        return m.get("adult")

    def interactions_for(self, drugs: List[str]) -> List[Dict]:
        pairs = set()
        out = []
        for a in drugs:
            for b in drugs:
                if a >= b:  # avoid duplicates
                    continue
                key = (a,b)
                if key in pairs: continue
                pairs.add(key)
                for it in self.db["interactions"]:
                    p = it["pair"]
                    if set(p) == set([a,b]):
                        out.append(it)
        return out

    def alternatives(self, drug: str) -> List[str]:
        return self.db.get("alternatives", {}).get(drug, [])

class IBMClient:
    """
    Placeholder for IBM Watson/Granite. If IBM_API_KEY and IBM_URL exist,
    you could add real calls here to enrich interactions, contraindications, etc.
    """
    def __init__(self):
        self.api_key = os.getenv("IBM_API_KEY", "")
        self.url = os.getenv("IBM_URL", "")

    def available(self) -> bool:
        return bool(self.api_key and self.url)

    def enrich_interactions(self, drugs: List[str]) -> List[Dict]:
        # TODO: implement actual IBM calls
        return []

class Analyzer:
    def __init__(self, db_path: str = "datasets/drug_data.json"):
        self.db = DrugDB(db_path)
        self.ibm = IBMClient()

    def extract(self, text: Optional[str], explicit_drugs: Optional[List[Dict]]) -> List[Dict]:
        if explicit_drugs and len(explicit_drugs) > 0:
            # sanitize names to canonical
            cleaned = []
            for d in explicit_drugs:
                nm = self.db.normalize(d.get("drug","")) or d.get("drug","")
                cleaned.append({
                    "drug": nm,
                    "dose_mg": d.get("dose_mg"),
                    "frequency_per_day": d.get("frequency_per_day")
                })
            return cleaned
        if text:
            return parse_prescription(text, self.db.db)
        return []

    def check(self, items: List[Dict], age: int) -> Dict:
        drugs = [i["drug"] for i in items]
        interactions = self.db.interactions_for(drugs)

        # OPTIONAL: add IBM results if available
        if self.ibm.available():
            interactions += self.ibm.enrich_interactions(drugs)

        # dosage recommendations + max daily checks
        recs = {}
        warnings = []
        for it in items:
            nm = it["drug"]
            dose = it.get("dose_mg")
            freq = it.get("frequency_per_day")
            recommended = self.db.default_dose_for_age(nm, age)
            max_daily = self.db.max_daily_mg(nm, age)
            total = dose * freq if dose and freq else None
            if total and max_daily and total > max_daily:
                warnings.append({
                    "drug": nm,
                    "issue": "Dose exceeds max daily limit",
                    "computed_mg_per_day": total,
                    "max_daily_mg": max_daily
                })
            recs[nm] = {
                "recommended_dose_for_age": recommended,
                "max_daily_mg": max_daily
            }

        # alternatives
        alts = {nm: self.db.alternatives(nm) for nm in drugs}

        return {
            "drugs_parsed": items,
            "interactions": interactions,
            "dosage_guidance": recs,
            "warnings": warnings,
            "alternatives": alts
        }
'@ | Set-Content -Encoding UTF8 model.py"
