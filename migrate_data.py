import pandas as pd
import json
import logging
from src.database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_embedding(val):
    """
    Ensures the embedding is returned strictly as a flat list of floats.
    Handles JSON strings, dictionary structures, and malformed entries.
    """
    if not val or pd.isna(val):
        return None
        
    # Step 1: If it's a string representation, parse it into a Python native type
    if isinstance(val, str):
        val = val.strip()
        try:
            val = json.loads(val)
        except json.JSONDecodeError:
            # Fallback for plain array text representations missing brackets
            if "," in val and not val.startswith("["):
                try:
                    return [float(x.strip()) for x in val.split(",")]
                except ValueError:
                    return None
            return None

    # Step 2: Unnest if the item is a dictionary containing the vector key
    if isinstance(val, dict):
        if "embedding" in val:
            val = val["embedding"]
        elif "vectors" in val:
            val = val["vectors"]
            
    # Step 3: Validate that we have a clean list of floats
    if isinstance(val, list):
        try:
            return [float(x) for x in val]
        except ValueError:
            return None
            
    return None

def run_migration(csv_file_path: str):
    if not db:
        logger.error("❌ Database client is not initialized. Check your environment variables.")
        return

    logger.info(f"📋 Reading dataset: {csv_file_path}")
    df = pd.read_csv(csv_file_path)
    
    # Print columns to easily confirm against database keys
    logger.info(f"Columns discovered in file: {list(df.columns)}")
    
    cleaned_incidents = []
    
    for idx, row in df.iterrows():
        # Mapping file column schemas directly to database required fields
        # Fallbacks keep your batch processing pipeline alive if fields are named differently
        inc_num = row.get("inc_number") or row.get("Incident Number") or row.get("Incident")
        err_text = row.get("error_text") or row.get("Error Text") or row.get("Description")
        
        # Pull the vector field and sanitize it completely
        raw_embedding = row.get("embedding") or row.get("Embedding") or row.get("vector")
        sanitized_embedding = clean_embedding(raw_embedding)
        
        if pd.isna(inc_num) or pd.isna(err_text) or not sanitized_embedding:
            logger.warning(f"⚠️ Skipping row {idx}: Missing required inc_number, error_text, or flat vector array.")
            continue
            
        # Standardize record object properties for insert_incident payload
        incident_record = {
            "inc_number": str(inc_num).strip(),
            "error_text": str(err_text).strip(),
            "embedding": sanitized_embedding,  # Explicitly guaranteed flat list [fl, fl, fl]
            "module": str(row.get("module") or row.get("Module") or "All").strip(),
            "transaction_code": str(row.get("transaction_code") or row.get("T-Code") or "").strip(),
            "resolution": str(row.get("resolution") or row.get("Resolution") or "").strip(),
            "resolution_category": str(row.get("resolution_category") or row.get("Category") or "Unknown").strip()
        }
        
        cleaned_incidents.append(incident_record)
        
    logger.info(f"🔄 Preparing batch ingestion workflow for {len(cleaned_incidents)} sanitized records...")
    
    # Execute batch workflow via the database helper wrapper
    results = db.insert_batch(cleaned_incidents)
    
    logger.info(f"🏁 Migration Complete: {results['success']} updated/inserted, {results['errors']} failed.")

if __name__ == "__main__":
    # Change path string to point to your target local environment or container workspace
    CSV_PATH = "SAP Incidents 2025 Till May1.xlsx - Page 1.csv"
    run_migration(CSV_PATH)
