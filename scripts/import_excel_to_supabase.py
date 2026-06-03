#!/usr/bin/env python3
"""
Import SAP incidents from Excel to Supabase with embeddings
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database import db
from src.embeddings import embedder
from src.parsers import parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_excel_to_supabase(excel_path: str):
    """Import Excel data to Supabase with embeddings"""
    
    logger.info(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path, sheet_name="Page 1")
    
    total_rows = len(df)
    logger.info(f"Found {total_rows} incidents to process")
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Extract data from Excel
            inc_number = row.get('Number', '')
            short_desc = row.get('Short description', '')
            description = row.get('Description', '')
            resolution_notes = row.get('Resolution notes', '')
            feature = row.get('Feature', '')
            
            # Skip rows with no resolution
            if pd.isna(resolution_notes) or not str(resolution_notes).strip():
                logger.warning(f"Skipping INC {inc_number}: No resolution notes")
                continue
            
            # Parse resolution notes
            resolution_text = str(resolution_notes)
            root_cause = parser.extract_root_cause(resolution_text)
            action_taken = parser.extract_action_taken(resolution_text)
            transaction_codes = parser.extract_transaction_codes(resolution_text)
            resolution_category = parser.extract_resolution_category(resolution_text)
            
            # Combine text for embedding
            text_to_embed = f"{short_desc} {description} {root_cause} {action_taken}"
            text_to_embed = text_to_embed[:4000]  # Truncate for embedding limit
            
            # Generate embedding
            logger.info(f"Processing INC {inc_number} ({idx+1}/{total_rows})")
            embedding = embedder.generate(text_to_embed)
            
            # Determine module
            module = parser.extract_module(f"{feature} {short_desc} {description}")
            
            # Prepare data for insertion
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
            
            # Insert into Supabase
            if db.insert_incident(incident_data):
                success_count += 1
                logger.info(f"✅ Successfully imported INC {inc_number}")
            else:
                error_count += 1
                logger.error(f"❌ Failed to import INC {inc_number}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ Error processing INC {row.get('Number', 'Unknown')}: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Import completed!")
    logger.info(f"✅ Success: {success_count}")
    logger.info(f"❌ Errors: {error_count}")
    logger.info(f"📊 Total: {total_rows}")
    logger.info(f"{'='*50}")

if __name__ == "__main__":
    # Check if Excel file exists
    excel_path = "data/sap_incidents.xlsx"
    
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        logger.info("Please place your SAP incidents Excel file at: data/sap_incidents.xlsx")
        sys.exit(1)
    
    import_excel_to_supabase(excel_path)
