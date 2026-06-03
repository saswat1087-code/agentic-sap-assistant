import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime
import tempfile

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import agent
from src.database import db
from src.embeddings import embedder
from src.parsers import parser
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

# Initialize session state
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'import_status' not in st.session_state:
    st.session_state.import_status = None

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/sap.png", width=80)
    st.title("📊 Dashboard")
    
    stats = db.get_statistics() if db else {"total_incidents": 0, "modules": {}}
    st.metric("Total Incidents", stats.get("total_incidents", 0))
    
    st.subheader("Module Distribution")
    for module, count in stats.get("modules", {}).items():
        st.metric(module, count)
    
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
    
    with col1:
        error_message = st.text_area(
            "📝 **Paste your SAP error message here**",
            height=150,
            placeholder="Example: 'Storage bin not found in EWM during putaway' or 'Error in MIGO: Storage type Z45 not suitable as an interface'"
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
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        solve_button = st.button("🚀 Find Solution", use_container_width=True)
    
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
                else:
                    st.error("❌ Unable to resolve the error")
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**Error**: {result.get('error', 'Unknown error')}")
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
    elif solve_button and not error_message.strip():
        st.warning("⚠️ Please enter an error message first.")

# ==================== TAB 2: UPLOAD DATA ====================
with tab2:
    st.markdown("## 📤 Upload SAP Incidents Data")
    st.markdown("Upload your Excel file containing SAP incidents to add them to the knowledge base.")
    
    st.markdown("### 📋 File Requirements")
    st.markdown("""
    - **Format**: Excel (.xlsx)
    - **Required columns**: `Number`, `Short description`, `Resolution notes`
    - **Optional columns**: `Description`, `Feature`, `Category`
    - **Maximum file size**: 50MB
    """)
    
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
            df = pd.read_excel(uploaded_file, sheet_name="Page 1")
            st.markdown("### 📊 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Total rows: {len(df)}")
            
            required_cols = ['Number', 'Short description', 'Resolution notes']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {missing_cols}")
            else:
                st.success("✅ All required columns found!")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("🚀 Import to Database", use_container_width=True):
                        with st.spinner("Importing data to Supabase..."):
                            uploaded_file.seek(0)
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                                tmp_file.write(uploaded_file.getvalue())
                                tmp_path = tmp_file.name
                            
                            df = pd.read_excel(tmp_path, sheet_name="Page 1")
                            success_count = 0
                            error_count = 0
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, row in df.iterrows():
                                status_text.text(f"Processing row {idx+1}/{len(df)}...")
                                try:
                                    inc_number = row.get('Number', '')
                                    short_desc = row.get('Short description', '')
                                    description = row.get('Description', '')
                                    resolution_notes = row.get('Resolution notes', '')
                                    feature = row.get('Feature', '')
                                    
                                    if pd.isna(resolution_notes) or not str(resolution_notes).strip():
                                        error_count += 1
                                        continue
                                    
                                    resolution_text = str(resolution_notes)
                                    root_cause = parser.extract_root_cause(resolution_text)
                                    action_taken = parser.extract_action_taken(resolution_text)
                                    transaction_codes = parser.extract_transaction_codes(resolution_text)
                                    resolution_category = parser.extract_resolution_category(resolution_text)
                                    
                                    text_to_embed = f"{short_desc} {description} {root_cause} {action_taken}"[:4000]
                                    embedding = embedder.generate(text_to_embed)
                                    module = parser.extract_module(f"{feature} {short_desc} {description}")
                                    
                                    incident_data = {
                                        "inc_number": str(inc_number),
                                        "module": module,
                                        "error_text": str(short_desc)[:500],
                                        "root_cause": root_cause[:2000],
                                        "resolution": action_taken[:3000],
                                        "transaction_code": ", ".join(transaction_codes[:5]),
                                        "resolution_category": resolution_category,
                                        "embedding": embedding
                                    }
                                    
                                    if db.insert_incident(incident_data):
                                        success_count += 1
                                    else:
                                        error_count += 1
                                except Exception as e:
                                    error_count += 1
                                    logger.error(f"Error row {idx}: {e}")
                                
                                progress_bar.progress((idx + 1) / len(df))
                            
                            os.unlink(tmp_path)
                            
                            st.markdown('<div class="success-box">', unsafe_allow_html=True)
                            st.success(f"""
                            ## ✅ Import Complete!
                            - **Successfully imported**: {success_count} incidents
                            - **Errors**: {error_count} incidents
                            - **Total processed**: {len(df)} rows
                            """)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.session_state.import_status = f"Imported {success_count} incidents successfully!"
                            st.balloons()
                            st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 📥 Need a template?")
    if st.button("Download Excel Template"):
        template_df = pd.DataFrame({
            'Number': ['INC001', 'INC002'],
            'Short description': ['Error message 1', 'Error message 2'],
            'Description': ['Detailed description 1', 'Detailed description 2'],
            'Resolution notes': ['Root Cause: X\nAction Taken: Y', 'Root Cause: A\nAction Taken: B'],
            'Feature': ['MFG', 'QM']
        })
        
        from io import BytesIO
        buffer = BytesIO()
        template_df.to_excel(buffer, sheet_name='Page 1', index=False)
        buffer.seek(0)
        
        st.download_button(
            label="Download Template.xlsx",
            data=buffer,
            file_name="sap_incidents_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==================== TAB 3: ANALYTICS ====================
with tab3:
    st.markdown("## 📊 Knowledge Base Analytics")
    
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
        top_transactions = db.get_top_transactions(10) if db else []
        if top_transactions:
            for t in top_transactions[:5]:
                st.metric(t['transaction'], t['count'])
        else:
            st.info("No transaction data available")
    
    st.markdown("### 📅 Recent Activity")
    recent = db.get_recent_incidents(days=30, limit=10) if db else []
    if recent:
        recent_df = pd.DataFrame(recent)[['inc_number', 'module', 'created_at']]
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No recent activity")

st.markdown("---")
st.markdown(
    "<center><small>Powered by Google Gemini 1.5 Pro | Built with Streamlit | Data from SAP Incidents Database</small></center>",
    unsafe_allow_html=True
)
