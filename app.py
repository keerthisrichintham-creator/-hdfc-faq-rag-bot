import streamlit as st

st.title("HDFC FAQ Bot - Groww")
st.write("Welcome! I answer factual questions about 5 HDFC Direct Growth schemes from Groww.")
st.info("Facts-only. No investment advice.")

CORPUS = {
    "expense ratio flexi": {"answer": "HDFC Flexi Cap Direct Growth expense ratio is 0.74% (Regular is 1.64%). Direct plan has lower expense ratio.", "source": "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth"},
    "elss lock": {"answer": "HDFC ELSS Tax Saver has a 3-year lock-in period from date of allotment. No redemption allowed before 3 years.", "source": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-direct-growth"},
    "capital gains": {"answer": "To download capital gains statement: Groww App > You > Reports > Capital Gains Statement > Select FY > Download.", "source": "https://groww.in/mutual-funds/how-to-download-capital-gains-statement"},
    "payment failed": {"answer": "Payment failed but debited happens when bank confirms debit but response doesn't reach MFOnline. Amount is auto-reversed within 5-7 business days. Check Transaction Status before retrying.", "source": "docs/common_app_issues.txt"},
    "sip not showing": {"answer": "SIP deducted but not showing takes T+1 day to reflect after bank confirmation. Check after 24 hours under Transaction Status. Units will still be allotted at applicable NAV.", "source": "docs/common_app_issues.txt"},
    "app slow": {"answer": "App slow / 30 seconds loading is server-load or cache issue. Update app, clear cache, retry off-peak hours.", "source": "docs/common_app_issues.txt"},
    "redemption stuck": {"answer": "Redemption stuck settles in T+1 to T+3 working days depending on fund type. Check Transaction Status for rejection reason.", "source": "docs/common_app_issues.txt"},
}

def get_key(q):
    if not q: return None
    q_low = q.lower()
    for k in CORPUS:
        if k in q_low:
            return k
    if "elss" in q_low and "lock" in q_low: return "elss lock"
    if "expense" in q_low and "flexi" in q_low: return "expense ratio flexi"
    if "capital" in q_low and "gain" in q_low: return "capital gains"
    if "payment" in q_low and ("fail" in q_low or "debit" in q_low): return "payment failed"
    if "sip" in q_low and ("not" in q_low or "show" in q_low or "deduct" in q_low): return "sip not showing"
    if "slow" in q_low or "30" in q_low or "loading" in q_low: return "app slow"
    if "redemption" in q_low and ("stuck" in q_low or "not" in q_low): return "redemption stuck"
    if "why" in q_low and "sip" in q_low: return "sip not showing"
    return None

# Initialize text box state
if "ask_box" not in st.session_state:
    st.session_state.ask_box = ""

def fill_box(text):
    st.session_state.ask_box = text

st.write("Try these example questions:")
col1, col2, col3 = st.columns(3)
with col1:
    st.button("What is expense ratio of HDFC F...", on_click=fill_box, args=("What is expense ratio of HDFC Flexi Cap Direct Growth?",))
with col2:
    st.button("What is ELSS lock-in period?", on_click=fill_box, args=("What is ELSS lock-in period?",))
with col3:
    st.button("How to download capital gains...", on_click=fill_box, args=("How to download capital gains statement?",))

# Extra user issues buttons for Phase 4 testing
st.write("Common user issues:")
c1, c2, c3 = st.columns(3)
with c1:
    st.button("Payment failed but debited", on_click=fill_box, args=("My payment failed but amount debited",))
with c2:
    st.button("SIP deducted not showing", on_click=fill_box, args=("SIP amount deducted but not showing in Groww",))
with c3:
    st.button("App slow 30 sec", on_click=fill_box, args=("Why is Groww app slow taking 30 seconds to load?",))

st.write("Ask question")
st.text_input("Ask question", key="ask_box", placeholder="Type your question here", label_visibility="collapsed")

# Only show answer AFTER Get Answer is clicked
if st.button("Get Answer"):
    q = st.session_state.ask_box
    key = get_key(q)
    if key:
        st.subheader(f"Answer for: {q}")
        st.success(CORPUS[key]["answer"])
        st.caption(f"Source: {CORPUS[key]['source']}")
    else:
        if q.strip() == "":
            st.warning("Please type a question or click a sample question.")
        else:
            st.subheader(f"Answer for: {q}")
            st.warning("I don't know based on allowed sources. I only answer about 5 HDFC funds + common app issues (payment, SIP, app slow, redemption).")