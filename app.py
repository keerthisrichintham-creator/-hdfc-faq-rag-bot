import streamlit as st

# HDFC Knowledge Base - Grounded from Groww
KB = {
    "hdfc balanced advantage": {
        "text": "HDFC Balanced Advantage Fund Direct Growth - Expense Ratio 0.74%, Exit Load 1% if redeemed within 1 year, AUM ₹ 78,000 Cr, Benchmark NIFTY 50 Hybrid Composite Debt 65:35. Ideal for long term wealth creation with balanced equity and debt.",
        "source": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
        "meta": ["0.74%", "1% exit load", "balanced"]
    },
    "hdfc elss tax saver": {
        "text": "HDFC ELSS Tax Saver Fund Direct Growth - Expense Ratio 0.86%, Lock-in 3 years mandatory, Exit Load NIL after lock-in, Tax deduction under 80C up to ₹1.5L. ELSS funds have shortest lock-in among tax saving options.",
        "source": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-growth",
        "meta": ["3 years lock-in", "0.86%", "80C"]
    },
    "hdfc small cap": {
        "text": "HDFC Small Cap Fund Direct Growth - Expense Ratio 0.76%, Exit Load 1% if redeemed within 1 year, Minimum SIP ₹100, Very High Risk. Focuses on small cap companies for high growth potential.",
        "source": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
        "meta": ["0.76%", "SIP ₹100", "Small Cap"]
    },
    "hdfc mid cap opportunities": {
        "text": "HDFC Mid Cap Opportunities Fund Direct Growth - Expense Ratio 0.77%, Exit Load 1% if redeemed within 1 year, AUM ₹ 70,000 Cr. Invests predominantly in mid-cap stocks.",
        "source": "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth",
        "meta": ["0.77%", "Mid Cap", "1% exit load"]
    },
    "hdfc flexi cap": {
        "text": "HDFC Flexi Cap Fund Direct Growth - Expense Ratio 0.74%, Exit Load 1% if redeemed within 1 year, Minimum Lumpsum ₹100. Flexi cap can invest across large, mid, small cap without restriction.",
        "source": "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth",
        "meta": ["0.74%", "Flexi Cap", "₹100"]
    }
}

st.set_page_config(page_title="HDFC FAQ RAG Bot", page_icon="🏦")
st.title("🏦 HDFC Mutual Fund - Facts-Only RAG Bot")
st.caption("Built for NextLeap Phase 4 | Grounded on Groww Data | No Investment Advice")

# Welcome message
with st.chat_message("assistant"):
    st.write("Hi! I am your facts-only assistant for **5 HDFC Direct Growth schemes**. Ask me factual questions like expense ratio, exit load, SIP minimum, lock-in period, AUM.")
    st.write("**Try these:**")
    st.code("What is expense ratio of HDFC Balanced Advantage?\nWhat is lock-in for HDFC ELSS?\nWhat is SIP minimum for HDFC Small Cap?\nWhat is exit load for HDFC Flexi Cap?")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

def get_answer(query):
    q = query.lower()
    # Refusal logic for advice/opinion
    advice_words = ["should i invest", "is it good", "will it give", "return kitna", "best fund", "recommend", "which is better", "profit hoga"]
    if any(w in q for w in advice_words):
        return "I can only provide factual information about HDFC funds from Groww. I cannot provide investment advice or predictions. For personalized advice, please consult a SEBI registered advisor. More info: https://www.amfiindia.com", None

    # Simple retrieval
    for key, data in KB.items():
        if any(word in q for word in key.split()) or any(word in q for word in data["meta"]):
            # check if fund name match
            if key.split()[1] in q or key.split()[0] in q: # crude
                pass
    # Find best match
    best = None
    for k,v in KB.items():
        if k.split()[1] in q or k.split()[2] in q or "balanced" in q and "balanced" in k or "elss" in q and "elss" in k or "small" in q and "small" in k or "mid" in q and "mid" in k or "flexi" in q and "flexi" in k:
            best = v
            break
    # fallback search by keywords
    if not best:
        for k,v in KB.items():
            if any(t.lower() in q for t in v["meta"]) or "expense" in q or "exit" in q or "sip" in q:
                # if query is generic, pick balanced as default but try to match
                if "expense ratio" in q and "0.74%" in v["text"]:
                    best = v
                elif "lock" in q and "elss" in k:
                    best = v
        if not best:
            # still no match, pick first that contains keyword
            for k,v in KB.items():
                if any(word in q for word in k.split()):
                    best = v
                    break

    if best:
        return best["text"], best["source"]
    else:
        # if no KB match
        return "I don't have verified information for this question in my HDFC knowledge base (5 funds). Please ask about expense ratio, exit load, SIP minimum, lock-in period for HDFC Balanced Advantage, ELSS, Small Cap, Mid Cap Opportunities, Flexi Cap. Data source: Groww.", None

# Chat input
if prompt := st.chat_input("Ask about HDFC funds..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    answer, source = get_answer(prompt)

    final_text = answer
    if source:
        final_text += f"\n\n**Source:** {source}"

    with st.chat_message("assistant"):
        st.markdown(final_text)

    st.session_state.messages.append({"role":"assistant","content":final_text})
