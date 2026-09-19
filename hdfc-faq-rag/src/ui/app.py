import streamlit as st
import sys
from pathlib import Path

# Fix import
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.retrieval.retriever import get_retriever
from src.retrieval.llm_client import generate_answer

st.set_page_config(page_title="HDFC FAQ Bot", page_icon="🏦")
st.title("🏦 HDFC Mutual Fund FAQ Chatbot")

# Fund to Groww link mapping
GROWW_LINKS = {
    "Flexi Cap": "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth",
    "Balanced Advantage": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    "Small Cap": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "ELSS": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-direct-growth",
    "Mid Cap": "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth"
}

def get_groww_link(fund_name):
    for key, link in GROWW_LINKS.items():
        if key.lower() in fund_name.lower():
            return link
    return "https://groww.in/mutual-funds"

@st.cache_resource
def load_retriever():
    return get_retriever()

retriever = load_retriever()

# Sample questions
st.write("Try these:")
col1, col2 = st.columns(2)
with col1:
    if st.button("What is SIP minimum for HDFC Small Cap?"):
        st.session_state.query = "What is SIP minimum for HDFC Small Cap?"
    if st.button("What is expense ratio for HDFC Balanced Advantage?"):
        st.session_state.query = "What is expense ratio for HDFC Balanced Advantage?"
with col2:
    if st.button("What is exit load for HDFC Flexi Cap?"):
        st.session_state.query = "What is exit load for HDFC Flexi Cap?"
    if st.button("What is lock-in for HDFC ELSS?"):
        st.session_state.query = "What is lock-in for HDFC ELSS?"

query = st.chat_input("Ask about HDFC funds...") or st.session_state.get("query", "")

if query:
    st.chat_message("user").write(query)
    docs = retriever.get_relevant_documents(query)
    answer = generate_answer(query, docs) if 'generate_answer' in globals() else docs[0].page_content

    with st.chat_message("assistant"):
        st.write(answer)

        # FIXED: Show clickable source link
        fund = docs[0].metadata.get("fund_name", "HDFC Fund") if docs else "HDFC Fund"
        link = get_groww_link(fund)
        st.markdown(f"**Source:** [Groww - {fund}]({link})")

        with st.expander("Source Documents"):
            for d in docs:
                f = d.metadata.get("fund_name","")
                l = get_groww_link(f)
                st.write(d.page_content)
                st.markdown(f"**Source:** [Groww]({l})")
                st.divider()

    st.session_state.query = ""