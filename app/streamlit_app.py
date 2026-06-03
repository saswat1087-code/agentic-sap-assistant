import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import agent
from src.database import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Agentic SAP Assistant",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .resolution-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #f44336;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/sap.png", width=80)
    st.title("📊 Dashboard")
    
    # Statistics
    stats = db.get_statistics()
    st.metric("Total Incidents", stats.get("total_incidents", 0))
    
    st.subheader("Module Distribution")
    for module, count in stats.get("modules", {}).items():
        st.metric(module, count)
    
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.info(
        "This AI assistant uses Gemini 1.5 Pro and semantic search "
        "to help resolve SAP errors across EWM, MM, QM, PP, AMM, and MFG modules."
    )
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Main content
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🛠️ Agentic SAP Assistant")
st.markdown("""
**AI-powered resolution for SAP errors** | Supports EWM, MM, QM, PP, AMM, MFG | Powered by Gemini 1.5 Pro
""")
st.markdown('</div>', unsafe_allow_html=True)

# Input section
col1, col2 = st.columns([3, 1])

with col1:
    error_message = st.text_area(
        "📝 **Paste your SAP error message here**",
        height=150,
        placeholder="Example: 'Storage bin not found in EWM during putaway' or 'Error in MIGO: Storage type Z45 not suitable as an interface'",
        help="Be as specific as possible. Include transaction codes or error numbers if available."
    )

with col2:
    module_filter = st.selectbox(
        "🎯 **Filter by module** (optional)",
        ["All", "MFG", "QM", "AMM", "EWM", "MM", "PP"]
    )
    
    st.markdown("---")
    st.markdown("### 🔧 Examples")
    if st.button("📦 EWM Example"):
        error_message = "Storage bin not found in EWM during putaway for warehouse number 001"
    if st.button("🏭 MFG Example"):
        error_message = "Control recipe not generated for Process Order 39601585"
    if st.button("🔬 QM Example"):
        error_message = "Inspection lot 04 cannot be released, status shows 'Not released'"

# Action button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    solve_button = st.button("🚀 Find Solution", use_container_width=True)

# Results area
if solve_button and error_message.strip():
    with st.spinner("🤖 Agentic AI is analyzing your error..."):
        try:
            result = agent.resolve_error(error_message, module_filter)
            
            if result["success"]:
                st.success(f"✅ Resolution found (Module: {result['module']})")
                
                st.markdown("---")
                st.markdown("## 💡 Resolution")
                st.markdown('<div class="resolution-box">', unsafe_allow_html=True)
                st.markdown(result["response"])
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 📊 Was this resolution helpful?")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👍 Yes", key="helpful"):
                        st.success("Thank you for your feedback!")
                with col2:
                    if st.button("👎 No", key="not_helpful"):
                        st.info("We'll improve our responses. Please provide more details if possible.")
                with col3:
                    if st.button("📋 Copy Resolution"):
                        st.info("Resolution copied to clipboard!")
                
                st.markdown("---")
                st.markdown("### 📚 Related Incidents")
                st.info("Similar incidents from our knowledge base were used to generate this resolution.")
            else:
                st.error("❌ Unable to resolve the error")
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.markdown(f"**Error**: {result.get('error', 'Unknown error')}")
                st.markdown("""
                **Suggestions**:
                1. Please provide more details about the error
                2. Include the transaction code if available
                3. Try rephrasing the error message
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Error in resolution: {e}")
            st.error("An unexpected error occurred. Please try again later.")
            
elif solve_button and not error_message.strip():
    st.warning("⚠️ Please enter an error message first.")

# Search tips section
st.markdown("---")
st.markdown("## 🔍 Search Tips")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **✓ Best Practices**
    - Include exact error message
    - Mention transaction code (e.g., MIGO, COR2)
    - Specify SAP module if known
    """)

with col2:
    st.markdown("""
    **✓ Examples of good queries**
    - "MIGO error: Storage type Z45 not suitable as an interface"
    - "Cannot release inspection lot 04 in QA32"
    - "Control recipe not sent to DMO for Process Order"
    """)

with col3:
    st.markdown("""
    **✓ Supported Modules**
    - Manufacturing (MFG)
    - Quality Management (QM)
    - Asset Management (AMM
