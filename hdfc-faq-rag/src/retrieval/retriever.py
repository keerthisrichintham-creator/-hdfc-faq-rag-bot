import os, json
from pathlib import Path

class Doc:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

class SimpleRetriever:
    def __init__(self, docs):
        self.docs = docs

    def get_relevant_documents(self, query):
        q = query.lower()
        scored = []
        for d in self.docs:
            text = (d.page_content + " " + d.metadata.get("fund_name","")).lower()
            score = sum(1 for w in q.split() if w in text)
            for fund in ["balanced advantage","flexi cap","small cap","elss","mid cap"]:
                if fund in q and fund in text:
                    score += 10
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [d for s,d in scored[:3] if s>0]
        return result if result else self.docs[:3]

def get_retriever():
    base = Path(__file__).resolve().parents[2]
    candidates = [
        base/"data"/"hdfc_faqs.json",
        base/"data"/"faqs.json",
        base/"src"/"data"/"hdfc_faqs.json"
    ]
    docs = []
    for p in candidates:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for item in data:
                    if isinstance(item, dict):
                        content = item.get("content") or item.get("answer") or item.get("text") or str(item)
                        meta = {"fund_name": item.get("fund_name",""), "source": item.get("source", str(p))}
                        docs.append(Doc(content, meta))
            except:
                pass
    if not docs:
        docs = [
            Doc("HDFC Balanced Advantage Fund Direct Growth: Expense Ratio 0.71%, Exit Load 1% if redeemed within 1 year, SIP Minimum Rs 100, No lock-in. Source: Groww", {"fund_name":"Balanced Advantage","source":"Groww"}),
            Doc("HDFC Flexi Cap Fund Direct Growth: Expense Ratio 0.72%, Exit Load 1% if redeemed within 1 year, SIP Minimum Rs 100", {"fund_name":"Flexi Cap","source":"Groww"}),
            Doc("HDFC Small Cap Fund Direct Growth: Expense Ratio 0.71%, Exit Load 1% within 1 year, SIP Minimum Rs 100", {"fund_name":"Small Cap","source":"Groww"}),
            Doc("HDFC ELSS Tax Saver Direct Growth: Expense Ratio 0.72%, No Exit Load, SIP Minimum Rs 500, Lock-in 3 years", {"fund_name":"ELSS","source":"Groww"}),
            Doc("HDFC Mid Cap Opportunities Direct Growth: Expense Ratio 0.74%, Exit Load 1% within 1 year, SIP Minimum Rs 100", {"fund_name":"Mid Cap","source":"Groww"}),
        ]
    return SimpleRetriever(docs)