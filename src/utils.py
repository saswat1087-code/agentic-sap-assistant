import logging
import sys
from rich.console import Console
from rich.table import Table
from src.config import settings

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/agentic_sap.log')
        ]
    )
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)

def print_statistics():
    """Print database statistics in a formatted table"""
    from src.database import db
    
    console = Console()
    stats = db.get_statistics()
    
    table = Table(title="SAP Knowledge Base Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Incidents", str(stats.get("total_incidents", 0)))
    
    console.print(table)
    
    if stats.get("modules"):
        module_table = Table(title="Module Distribution")
        module_table.add_column("Module", style="cyan")
        module_table.add_column("Count", style="green")
        
        for module, count in stats["modules"].items():
            module_table.add_row(module, str(count))
        
        console.print(module_table)

def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
