"""
Supabase database client for Agentic SAP Assistant
Handles vector similarity search, CRUD operations, and statistics
"""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from src.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase database client with vector search capabilities"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.client: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("✅ Supabase client initialized successfully")
            logger.info(f"   URL: {settings.supabase_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            raise
    
    # ==================== SEARCH METHODS ====================
    
    def search_similar(
        self, 
        embedding: List[float], 
        threshold: float = None, 
        limit: int = None,
        module_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar incidents using vector similarity
        
        Args:
            embedding: Query embedding vector (must be 768 dimensions)
            threshold: Minimum similarity score (0-1), default from settings
            limit: Maximum number of results, default from settings
            module_filter: Optional filter by SAP module
        
        Returns:
            List of incident dictionaries with similarity scores
        """
        threshold = threshold or settings.match_threshold
        limit = limit or settings.max_results
        
        try:
            # Call Supabase RPC function
            response = self.client.rpc(
                "match_sap_kb",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()
            
            results = response.data if response.data else []
            
            # Apply module filter if specified
            if module_filter and module_filter != "All":
                results = [r for r in results if r.get('module') == module_filter]
            
            logger.info(f"🔍 Search completed: {len(results)} results found (threshold: {threshold})")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching similar incidents: {e}")
            return []
    
    def search_by_keyword(
        self, 
        keyword: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search incidents by keyword in error_text or resolution
        
        Args:
            keyword: Search keyword
            limit: Maximum number of results
        
        Returns:
            List of matching incidents
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .or_(f"error_text.ilike.%{keyword}%,resolution.ilike.%{keyword}%")\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Error searching by keyword: {e}")
            return []
    
    def search_by_transaction(
        self, 
        transaction_code: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search incidents by transaction code
        
        Args:
            transaction_code: SAP transaction code (e.g., MIGO, COR2, QA32)
            limit: Maximum number of results
        
        Returns:
            List of incidents using this transaction
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .ilike("transaction_code", f"%{transaction_code}%")\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Error searching by transaction: {e}")
            return []
    
    def search_by_module(
        self, 
        module: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all incidents for a specific module
        
        Args:
            module: SAP module (MFG, QM, AMM, EWM, MM, PP)
            limit: Maximum number of results
        
        Returns:
            List of incidents for the module
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .eq("module", module)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"❌ Error searching by module: {e}")
            return []
    
    # ==================== INSERT METHODS ====================
    
    def insert_incident(self, incident_data: Dict[str, Any]) -> bool:
        """
        Insert a new incident into the database
        
        Args:
            incident_data: Dictionary with incident fields
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure required fields are present
            required_fields = ['inc_number', 'error_text', 'embedding']
            for field in required_fields:
                if field not in incident_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Add timestamps
            incident_data['created_at'] = datetime.now().isoformat()
            
            response = self.client.table("sap_kb").insert(incident_data).execute()
            
            if response.data:
                logger.info(f"✅ Inserted incident: {incident_data.get('inc_number')}")
                return True
            else:
                logger.error("❌ Insert returned no data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error inserting incident: {e}")
            return False
    
    def insert_batch(self, incidents: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert multiple incidents in batch
        
        Args:
            incidents: List of incident dictionaries
        
        Returns:
            Dictionary with success and error counts
        """
        success_count = 0
        error_count = 0
        
        for incident in incidents:
            if self.insert_incident(incident):
                success_count += 1
            else:
                error_count += 1
        
        logger.info(f"📊 Batch insert completed: {success_count} success, {error_count} errors")
        return {"success": success_count, "errors": error_count}
    
    # ==================== UPDATE METHODS ====================
    
    def update_incident(
        self, 
        inc_number: str, 
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing incident
        
        Args:
            inc_number: Incident number to update
            update_data: Dictionary with fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add updated timestamp
            update_data['updated_at'] = datetime.now().isoformat()
            
            response = self.client.table("sap_kb")\
                .update(update_data)\
                .eq("inc_number", inc_number)\
                .execute()
            
            if response.data:
                logger.info(f"✅ Updated incident: {inc_number}")
                return True
            else:
                logger.warning(f"⚠️ Incident not found: {inc_number}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating incident: {e}")
            return False
    
    def update_embedding(
        self, 
        inc_number: str, 
        embedding: List[float]
    ) -> bool:
        """
        Update embedding for an incident
        
        Args:
            inc_number: Incident number
            embedding: New embedding vector
        
        Returns:
            True if successful, False otherwise
        """
        return self.update_incident(inc_number, {"embedding": embedding})
    
    # ==================== DELETE METHODS ====================
    
    def delete_incident(self, inc_number: str) -> bool:
        """
        Delete an incident by incident number
        
        Args:
            inc_number: Incident number to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.table("sap_kb")\
                .delete()\
                .eq("inc_number", inc_number)\
                .execute()
            
            if response.data:
                logger.info(f"✅ Deleted incident: {inc_number}")
                return True
            else:
                logger.warning(f"⚠️ Incident not found: {inc_number}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting incident: {e}")
            return False
    
    def delete_by_module(self, module: str) -> int:
        """
        Delete all incidents for a module
        
        Args:
            module: SAP module name
        
        Returns:
            Number of incidents deleted
        """
        try:
            # First get count
            incidents = self.search_by_module(module, limit=1000)
            count = len(incidents)
            
            if count == 0:
                logger.info(f"No incidents found for module: {module}")
                return 0
            
            # Delete them
            for incident in incidents:
                self.delete_incident(incident.get('inc_number'))
            
            logger.info(f"✅ Deleted {count} incidents for module: {module}")
            return count
            
        except Exception as e:
            logger.error(f"❌ Error deleting by module: {e}")
            return 0
    
    # ==================== RETRIEVAL METHODS ====================
    
    def get_by_inc_number(self, inc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve incident by incident number
        
        Args:
            inc_number: Incident number (e.g., INC22521394)
        
        Returns:
            Incident dictionary or None if not found
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .eq("inc_number", inc_number)\
                .limit(1)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting incident by number: {e}")
            return None
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve incident by UUID
        
        Args:
            id: UUID of the incident
        
        Returns:
            Incident dictionary or None if not found
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .eq("id", id)\
                .limit(1)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting incident by ID: {e}")
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all incidents with pagination
        
        Args:
            limit: Maximum number of records
            offset: Number of records to skip
        
        Returns:
            List of incident dictionaries
        """
        try:
            response = self.client.table("sap_kb")\
                .select("*")\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting all incidents: {e}")
            return []
    
    # ==================== STATISTICS METHODS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with total counts, module distribution, etc.
        """
        try:
            # Get total count
            total_response = self.client.table("sap_kb")\
                .select("count", count="exact")\
                .execute()
            total_incidents = total_response.count if total_response.count else 0
            
            # Get module distribution
            modules_response = self.client.table("sap_kb")\
                .select("module")\
                .execute()
            
            module_counts = {}
            resolution_counts = {}
            
            for item in modules_response.data:
                module = item.get("module", "Unknown")
                module_counts[module] = module_counts.get(module, 0) + 1
                
                resolution = item.get("resolution_category", "Unknown")
                resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1
            
            # Get date range
            date_response = self.client.table("sap_kb")\
                .select("created_at")\
                .order("created_at", desc=False)\
                .limit(1)\
                .execute()
            
            oldest_date = date_response.data[0]['created_at'] if date_response.data else None
            
            newest_response = self.client.table("sap_kb")\
                .select("created_at")\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            newest_date = newest_response.data[0]['created_at'] if newest_response.data else None
            
            return {
                "total_incidents": total_incidents,
                "modules": module_counts,
                "resolution_categories": resolution_counts,
                "date_range": {
                    "oldest": oldest_date,
                    "newest": newest_date
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {
                "total_incidents": 0,
                "modules": {},
                "resolution_categories": {},
                "date_range": {"oldest": None, "newest": None}
            }
    
    def get_module_statistics(self, module: str) -> Dict[str, Any]:
        """
        Get statistics for a specific module
        
        Args:
            module: SAP module name
        
        Returns:
            Dictionary with module-specific statistics
        """
        incidents = self.search_by_module(module, limit=1000)
        
        if not incidents:
            return {"module": module, "count": 0}
        
        # Count resolution categories
        resolution_counts = {}
        for inc in incidents:
            resolution = inc.get("resolution_category", "Unknown")
            resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1
        
        # Get unique transaction codes
        transactions = set()
        for inc in incidents:
            tcode = inc.get("transaction_code")
            if tcode:
                for t in tcode.split(", "):
                    transactions.add(t)
        
        return {
            "module": module,
            "count": len(incidents),
            "resolution_categories": resolution_counts,
            "unique_transactions": list(transactions)[:20]  # Top 20
        }
    
    # ==================== UTILITY METHODS ====================
    
    def health_check(self) -> bool:
        """
        Check if database connection is working
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            response = self.client.table("sap_kb")\
                .select("count", count="exact")\
                .limit(1)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def count_incidents(self, module: str = None) -> int:
        """
        Count total incidents, optionally filtered by module
        
        Args:
            module: Optional module filter
        
        Returns:
            Number of incidents
        """
        try:
            query = self.client.table("sap_kb").select("count", count="exact")
            
            if module and module != "All":
                query = query.eq("module", module)
            
            response = query.execute()
            return response.count if response.count else 0
            
        except Exception as e:
            logger.error(f"❌ Error counting incidents: {e}")
            return 0
    
    def get_recent_incidents(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent incidents from the last N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
        
        Returns:
            List of recent incidents
        """
        try:
            # Calculate date threshold
            from datetime import timedelta
            threshold = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.client.table("sap_kb")\
                .select("*")\
                .gte("created_at", threshold)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting recent incidents: {e}")
            return []
    
    def get_top_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently occurring transaction codes
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of transactions with counts
        """
        try:
            response = self.client.table("sap_kb")\
                .select("transaction_code")\
                .execute()
            
            # Count occurrences
            transaction_counts = {}
            for item in response.data:
                tcode = item.get("transaction_code")
                if tcode:
                    for t in tcode.split(", "):
                        transaction_counts[t] = transaction_counts.get(t, 0) + 1
            
            # Sort by count
            sorted_transactions = sorted(
                transaction_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return [{"transaction": t, "count": c} for t, c in sorted_transactions]
            
        except Exception as e:
            logger.error(f"❌ Error getting top transactions: {e}")
            return []
    
    def clear_database(self, confirm: bool = False) -> bool:
        """
        Delete all incidents (use with caution!)
        
        Args:
            confirm: Must be True to actually delete
        
        Returns:
            True if successful, False otherwise
        """
        if not confirm:
            logger.warning("⚠️ Clear database called without confirmation")
            return False
        
        try:
            response = self.client.table("sap_kb")\
                .delete()\
                .neq("id", "00000000-0000-0000-0000-000000000000")\
                .execute()
            
            logger.warning("🗑️ All incidents deleted from database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error clearing database: {e}")
            return False


# ==================== SINGLETON INSTANCE ====================

# Create a single instance to be used across the application
try:
    db = SupabaseClient()
    logger.info("✅ Database client ready")
except Exception as e:
    logger.error(f"❌ Failed to create database client: {e}")
    db = None
