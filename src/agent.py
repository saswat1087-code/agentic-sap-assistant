from typing import Dict, Any, List
import logging
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from src.config import settings
from src.database import db
from src.embeddings import embedder
from src.parsers import parser

logger = logging.getLogger(__name__)

class SAPAgent:
    def __init__(self):
        self.llm = ChatVertexAI(
            model=settings.gemini_model,
            project=settings.gemini_project_id,
            location=settings.gemini_location,
            temperature=0.3,
            max_output_tokens=2048
        )
        
        tools = [
            Tool(
                name="Search_SAP_Knowledge_Base",
                func=self.search_knowledge_base,
                description="Search historical SAP incidents for similar errors and resolutions"
            )
        ]
        
        prompt = PromptTemplate.from_template("""
You are an expert SAP support specialist with deep knowledge of EWM, MM, QM, PP, AMM, and MFG modules.

## User Query
Module filter: {module_filter}
Error message: {error_message}

## Retrieved Knowledge
Use the tool to search for similar past incidents.
{tool_output}

## Your Task
Based on the retrieved knowledge and your expertise, provide:

1. **Identified SAP Module**: (EWM, MM, QM, PP, AMM, or MFG)
2. **Root Cause Analysis**: Explain why this error occurs
3. **Step-by-Step Resolution**: Clear, actionable steps including transaction codes if applicable
4. **Prevention Tips**: How to avoid this issue in the future

If no exact match exists in the knowledge base, provide the best possible solution based on similar patterns or standard SAP best practices.

Be specific, practical, and safety-conscious.
""")
        
        self.agent = create_react_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        logger.info("SAP Agent initialized")
    
    def search_knowledge_base(self, query: str) -> str:
        """Search the knowledge base and return formatted results"""
        try:
            # Generate embedding for query
            query_embedding = embedder.generate(query)
            
            # Search similar incidents
            results = db.search_similar(query_embedding)
            
            if not results:
                return "No similar incidents found in the knowledge base."
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results[:3], 1):
                formatted_results.append(f"""
### Similar Incident {idx}
- **Incident**: {result.get('inc_number', 'N/A')}
- **Module**: {result.get('module', 'Unknown')}
- **Error**: {result.get('error_text', 'N/A')[:200]}
- **Root Cause**: {result.get('root_cause', 'N/A')[:300]}
- **Resolution**: {result.get('resolution', 'N/A')[:400]}
- **Similarity Score**: {result.get('similarity', 0):.2%}
""")
            
            return "\n".join(formatted_results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return "Error searching knowledge base. Please try again."
    
    def resolve_error(self, error_message: str, module_filter: str = "All") -> Dict[str, Any]:
        """Resolve an SAP error using agentic AI"""
        try:
            # First, try to detect module if not specified
            if module_filter == "All":
                detected_module = parser.extract_module(error_message)
                module_filter = detected_module
            
            response = self.agent_executor.invoke({
                "input": f"Module filter: {module_filter}\nError message: {error_message}",
                "module_filter": module_filter,
                "error_message": error_message
            })
            
            return {
                "success": True,
                "response": response.get("output", ""),
                "module": module_filter
            }
        except Exception as e:
            logger.error(f"Error resolving error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Unable to resolve the error. Please check your input and try again."
            }
    
    def get_incident_details(self, inc_number: str) -> Dict[str, Any]:
        """Get detailed information about a specific incident"""
        return db.get_by_inc_number(inc_number)

# Singleton instance
agent = SAPAgent()
