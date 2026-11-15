import os
import glob
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError, ClientError

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("🚨 GOOGLE_API_KEY not found in .env file! Please add it before proceeding.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=api_key)

# Page Configuration
st.set_page_config(page_title="WatchdogAI: Compliance Auditor", page_icon="🛡️", layout="wide")

# Session State Initialization for Chat History & Audit State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "audit_completed" not in st.session_state:
    st.session_state.audit_completed = False

# Minimalist Custom CSS (Fonts: Redaction 50 for headings, Space Grotesk for body + Green Gradient effect)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Redaction+50&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* Green Gradient Styling for All Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Redaction 50', serif !important;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #00E620, #00ffaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }
    
    /* Make main title even more prominent */
    h1 {
        font-size: 3.2rem !important;
        font-weight: 700;
    }
    
    .stTextArea textarea {
        font-family: 'Space Grotesk', sans-serif;
        border-radius: 8px;
        border: 1px solid #333333;
    }
    
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
        width: 100%;
        font-family: 'Space Grotesk', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Top Title Header (No subtitle, no custom toggle button)
st.markdown("# WatchdogAI")
st.markdown("---")

# --- LOAD COMPLIANCE DOCUMENTS ---
@st.cache_resource
def load_all_documents():
    docs = {}
    filepaths = glob.glob("./data/**/*.txt", recursive=True)
    for path in filepaths:
        filename = os.path.basename(path)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            docs[filename] = f.read()
    return docs

all_docs = load_all_documents()
combined_context = "\n\n".join([f"--- FILE: {name} ---\n{content}" for name, content in all_docs.items()])

# --- TWO-COLUMN SPLIT LAYOUT ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### Input Scenario")
    st.markdown("Provide the LLM claim or suspicious suggestion you want to audit:")
    
    user_query = st.text_area(
        "Suspicious LLM Suggestion",
        placeholder="e.g., ChatGPT said it's fine to scrape user emails or bring alcohol into the hostel...",
        height=220,
        label_visibility="collapsed"
    )
    
    run_audit = st.button("Run Audit", type="primary")

with col_right:
    st.markdown("### Audit Stream & Conversation")
    
    # Handle audit trigger
    if run_audit:
        if not user_query.strip():
            st.warning("Please enter a prompt or suggestion to audit on the left.")
        else:
            with st.spinner("Evaluating rules against compliance policies..."):
                prompt = f"""
                You are WatchdogAI, an independent legal and compliance auditor. Your job is to check whether an AI model (like ChatGPT) gave a user dangerous, illegal, or rule-breaking advice.
                
                Based strictly on the following official source documents, evaluate the user's scenario.
                
                OFFICIAL SOURCE DOCUMENTS:
                {combined_context}
                
                USER SCENARIO / LLM CLAIM:
                {user_query}
                
                INSTRUCTIONS:
                Provide your response in the following structured format:
                1. **Verdict:** Choose strictly between [SUPPORTED], [CONTRADICTED], or [UNVERIFIABLE].
                2. **Explanation:** Explain why the LLM's advice is correct or why it hallucinated safety/legality, citing the relevant policy or law.
                3. **Evidence Snippet:** Quote the specific rule from the documents that proves your verdict.
                """
                
                models_to_try = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-1.5-flash"]
                audit_result = None
                
                for model_name in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt
                        )
                        audit_result = response.text
                        break
                    except (ServerError, ClientError):
                        continue
                
                if not audit_result:
                    audit_result = "Google AI servers are busy. Please try clicking audit again."
                
                # Reset chat history with the initial audit result
                st.session_state.chat_history = [
                    {"role": "user", "content": f"Audit this claim: {user_query}"},
                    {"role": "assistant", "content": audit_result}
                ]
                st.session_state.audit_completed = True

    # Render chat container and history if audit has been performed
    if st.session_state.audit_completed:
        chat_container = st.container(height=380)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Follow-up conversational input box enabled only after audit
        follow_up_query = st.chat_input("Ask a follow-up or discuss this audit...")
        if follow_up_query:
            st.session_state.chat_history.append({"role": "user", "content": follow_up_query})
            
            with st.spinner("Generating response..."):
                chat_prompt = f"""
                You are WatchdogAI, an expert compliance chatbot. Continue the conversation with the user based on the previous context and source documents.
                
                OFFICIAL SOURCE DOCUMENTS:
                {combined_context}
                
                CONVERSATION HISTORY:
                """
                for m in st.session_state.chat_history:
                    chat_prompt += f"\n{m['role'].upper()}: {m['content']}"
                
                chat_prompt += f"\nASSISTANT:"
                
                reply_text = None
                for model_name in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-1.5-flash"]:
                    try:
                        res = client.models.generate_content(model=model_name, contents=chat_prompt)
                        reply_text = res.text
                        break
                    except (ServerError, ClientError):
                        continue
                
                if not reply_text:
                    reply_text = "Server busy. Please try sending your message again."
                
                st.session_state.chat_history.append({"role": "assistant", "content": reply_text})
                st.rerun()
    else:
        st.info("Submit an audit scenario on the left panel to initialize the audit report and unlock the conversational chat stream.")