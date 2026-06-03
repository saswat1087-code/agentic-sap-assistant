import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import tempfile
import logging
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration - MUST be the first Streamlit command
st.set_page_config(
    page_title="Agentic SAP Assistant",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules with error handling
try:
    from src.agent import agent
    from src.database import db
    from src.embeddings import embedder
    from src.parsers import parser
except Exception as e:
    st.error(f"Failed to import modules: {e}")
    logger.error(f"Import error: {e}")
    agent = None
    db = None
    embedder = None
    parser = None

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
        color: #333333;
    }
    .upload-box {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f9f9f9;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #f44336;
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

# Initialize session state variables cleanly
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'import_status' not in st.session_state:
    st.session_state.import_status = None
if 'txt_area_value' not in st.session_state:
    st.session_state.txt_area_value = ""

# Sidebar
with st.sidebar:
    try:
        st.image("https://img.icons8.com/color/96/000000/sap.png", width=80)
    except:
        st.markdown("## 🛠️")
    
    st.title("📊 Dashboard")
    
    # Get statistics with error handling
    if db:
        try:
            stats = db.get_statistics() if db else {"total_incidents": 0, "modules": {}}
            st.metric("Total Incidents", stats.get("total_incidents", 0))
            
            st.subheader("Module Distribution")
            for module, count in stats.get("modules", {}).items():
                st.metric(module, count)
        except Exception as e:
            st.error(f"Database connection error: {e}")
            st.info("Please check your Supabase credentials")
    else:
        st.warning("⚠️ Database not connected")
        st.info("Add SUPABASE_URL and SUPABASE_KEY to environment variables")
    
    st.markdown("---")
    
    st.subheader("📁 Data Management")
    if st.session_state.import_status:
        if "success" in st.session_state.import_status.lower():
            st.success(st.session_state.import_status)
        else:
            st.error(st.session_state.import_status)
    
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.info(
        "This AI assistant uses Gemini 1.5 Pro and semantic search "
        "to help resolve SAP errors across EWM, MM, QM, PP, AMM, and MFG modules."
    )
    
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Main content
st.markdown("""
<div class="main-header">
    <h1>🛠️ Agentic SAP Assistant</h1>
    <p><strong>AI-powered resolution for SAP errors</strong> | Supports EWM, MM, QM, PP, AMM, MFG | Powered by Gemini 1.5 Pro</p>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🔍 Search Errors", "📤 Upload Data", "📊 Analytics"])

# ==================== TAB 1: SEARCH ERRORS ====================
with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col2:
        module_filter = st.selectbox(
            "🎯 **Filter by module** (optional)",
            ["All", "MFG", "QM", "AMM", "EWM", "MM", "PP"]
        )
        
        st.markdown("---")
        st.markdown("### 🔧 Examples")
        if st.button("📦 EWM Example"):
            st.session_state.txt_area_value = "Storage bin not found in EWM during putaway for warehouse number 001"
            st.rerun()
        if st.button("🏭 MFG Example"):
            st.session_state.txt_area_value = "Control recipe not generated for Process Order 39601585"
            st.rerun()
        if st.button("🔬 QM Example"):
            st.session_state.txt_area_value = "Inspection lot 04 cannot be released, status shows 'Not released'"
            st.rerun()
            
    with col1:
        error_message = st.text_area(
            "📝 **Paste your SAP error message here**",
            value=st.session_state.txt_area_value,
            height=150,
            placeholder="Example: 'Storage bin not found in EWM during putaway' or 'Error in MIGO: Storage type Z45 not suitable as an interface'"
        )
    
    col1_btn, col2_btn, col3_btn = st.columns([1, 1, 1])
    with col2_btn:
        solve_button = st.button("🚀 Find Solution", use_container_width=True)
    
    if solve_button and error_message.strip():
        if agent:
            with st.spinner("🤖 Agentic AI is analyzing your error..."):
                try:
                    result = agent.resolve_error(error_message, module_filter)
                    
                    if result and result.get("success"):
                        st.success(f"✅ Resolution found (Module: {result.get('module', 'Unknown')})")
                        st.markdown("---")
                        st.markdown("## 💡 Resolution")
                        st.markdown('<div class="resolution-box">', unsafe_allow_html=True)
                        st.markdown(result.get("response", ""))
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("❌ Unable to resolve the error")
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.markdown(f"**Error**: {result.get('error', 'Unknown response breakdown.')}")
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
        else:
            st.error("Agent module failed to initialize. Please check Render environment configurations.")
    elif solve_button and not error_message.strip():
        st.warning("⚠️ Please enter an error message first.")

# ==================== TAB 2: UPLOAD DATA ====================
with tab2:
    st.markdown("## 📤 Upload SAP Incidents Data")
    st.markdown("Upload your Excel file containing SAP incidents to add them to the knowledge base.")
    
    if db and embedder:
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=['xlsx', 'xls'],
            help="Upload your SAP incidents Excel file"
        )
        
        if uploaded_file is not None:
            st.markdown('<div class="upload-box">', unsafe_allow_html=True)
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.info(f"📊 File size: {uploaded_file.size:,} bytes")
            
            try:
                df = pd.read_excel(uploaded_file, sheet_name=0)
                st.markdown("### 📊 Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"Total rows: {len(df)}")
                
                required_cols = ['Number', 'Short description', 'Resolution notes']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {missing_cols}")
                else:
                    st.success("✅ All required columns found!")
                    
                    if st.button("🚀 Import to Database", use_container_width=True):
                        # Simple placeholder layout execution matching your design template
                        st.info("Import engine actively listening. Ready to execute pipeline parsing maps.")
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Database or Embeddings not available. Please check your configuration.")

# ==================== TAB 3: ANALYTICS ====================
with tab3:
    st.markdown("## 📊 Knowledge Base Analytics")
    
    if db:
        try:
            stats = db.get_statistics()
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Module Distribution")
                if stats.get("modules"):
                    for module, count in stats["modules"].items():
                        st.metric(module, count)
                else:
                    st.info("No data available yet. Upload some incidents first!")
            
            with col2:
                st.markdown("### 🔧 Top Transaction Codes")
                st.info("Upload data to see transaction code analytics")
        except Exception as e:
            st.error(f"Error loading statistics: {e}")
    else:
        st.warning("Database not connected")

# Footer
st.markdown("---")
st.markdown(
    "<center><small>Powered by Google Gemini 1.5 Pro | Built with Streamlit | Data from SAP Incidents Database</small></center>",
    unsafe_allow_html=True
)
