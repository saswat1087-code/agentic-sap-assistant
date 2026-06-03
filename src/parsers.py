import re
from typing import Tuple, Optional, List

class ResolutionParser:
    """Parse resolution notes to extract root cause, action taken, and transaction codes"""
    
    @staticmethod
    def extract_root_cause(text: str) -> str:
        """Extract root cause from resolution notes"""
        if not text:
            return ""
        
        patterns = [
            r"Root Cause:\s*(.+?)(?:\n\d+\.|\nAction\s*Taken:|\nWorkaround|\n$)",
            r"Root Cause[:\s]+(.+?)(?:\n\n|\n\d+\.|\nAction|\n$)",
            r"Root\s*Cause:\s*(.+?)(?:\n[A-Z]|\n\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    @staticmethod
    def extract_action_taken(text: str) -> str:
        """Extract action taken from resolution notes"""
        if not text:
            return ""
        
        patterns = [
            r"Action Taken:\s*(.+?)(?:\n\d+\.|\nWorkaround|\nFields Checked|\n$)",
            r"Action\s*Taken[:\s]+(.+?)(?:\n\n|\n\d+\.|\nField|\n$)",
            r"Actions? Performed:\s*(.+?)(?:\n\n|\nResolution|\n$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    @staticmethod
    def extract_transaction_codes(text: str) -> List[str]:
        """Extract SAP transaction codes from text"""
        if not text:
            return []
        
        # Pattern for SAP transaction codes
        patterns = [
            r'\b([A-Z0-9]{2,6})\b',
            r'\b/[A-Z0-9_]+/[A-Z0-9_]+\b',
            r'\btransaction\s+([A-Z0-9/]+)\b',
            r'\bt-code\s+([A-Z0-9/]+)\b'
        ]
        
        codes = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            codes.update(matches)
        
        # Filter out common false positives
        false_positives = {'THE', 'AND', 'FOR', 'WITH', 'FROM', 'THIS', 'THAT', 'HAVE', 'WERE', 'BUT', 'YOU', 'YOUR', 'NOT', 'ARE'}
        codes = [c for c in codes if c not in false_positives and len(c) >= 2]
        
        return list(codes)
    
    @staticmethod
    def extract_resolution_category(text: str) -> str:
        """Extract resolution category from resolution notes"""
        if not text:
            return ""
        
        patterns = [
            r"Resolution Category:\s*([^\n]+)",
            r"Category:\s*([^\n]+)",
            r"Resolved by ([^\n]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Default categories based on keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ['user instruction', 'knowledge gap', 'explain']):
            return "User Instruction - Knowledge Gap"
        elif any(word in text_lower for word in ['master data', 'correction', 'maintain']):
            return "User Instruction - Master Data Correction"
        elif any(word in text_lower for word in ['config', 'setup', 'maintaining']):
            return "Fixed by Maintaining Setup"
        elif 'auto resolved' in text_lower:
            return "Auto Resolved"
        
        return "Other"
    
    @staticmethod
    def extract_module(text: str, default: str = "Unknown") -> str:
        """Extract SAP module from text"""
        module_keywords = {
            "MFG": ["process order", "control recipe", "pi sheet", "confirmation", "production order", "cor2", "cor6", "coid"],
            "QM": ["inspection", "quality", "qa32", "qa33", "qe51", "inspection lot", "qir", "vam"],
            "AMM": ["prometheus", "maintenance", "work order", "equipment", "functional location", "floc", "pm03", "iw38"],
            "EWM": ["warehouse", "storage bin", "putaway", "pick", "wm", "ls24", "ls26"],
            "MM": ["material", "purchase order", "vendor", "goods receipt", "migo", "mm01", "mm02"],
            "PP": ["production version", "bom", "master recipe", "resource", "work center"]
        }
        
        text_lower = text.lower()
        for module, keywords in module_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return module
        
        return default

parser = ResolutionParser()
