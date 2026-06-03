import os
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

# Import your database and embedding singleton instances directly
from src.database import db
from src.embeddings import embedder

logger = logging.getLogger(__name__)

# ==================== TOOL 1: LOCAL KNOWLEDGE BASE LOOKUP ====================

@tool
def query_sap_knowledge_base(error_message: str, module_filter: str = "All") -> str:
    """
    Searches the internal Supabase SAP knowledge base for historical incidents,
    root causes, transaction codes, and resolutions matching an error text.
    ALWAYS use this tool first when investigating any SAP error.
    """
    try:
        logger.info(f"🤖 Tool Execution: Querying local DB for error: '{error_message}' (Filter: {module_filter})")
        
        # 1. Generate the embedding vector dictionary payload using our direct REST wrapper
        embedding_response = embedder.generate(error_message)
        raw_vector = embedding_response.get("embedding")
        
        if not raw_vector:
            return "Could not generate vector embedding for the search query."
            
        # 2. Run the vector similarity match RPC function against Supabase (table: sap_kb)
        matches = db.search_similar(embedding=raw_vector, module_filter=module_filter)
        
        if not matches:
            return "No historical incidents matching this error description were found in the local database."
            
        # 3. Format matches into a structured text context block for Gemini to reason over
        context_blocks = []
        for idx, match in enumerate(matches[:3]):  # Analyze top 3 most relevant matches
            block = (
                f"--- Local Match #{idx+1} (Incident: {match.get('inc_number', 'N/A')}) ---\n"
                f"Module: {match.get('module', 'Unknown')}\n"
                f"Error Text: {match.get('error_text', '')}\n"
                f"Root Cause: {match.get('root_cause', '')}\n"
                f"Resolution Notes: {match.get('resolution', '')}\n"
                f"Transaction Codes: {match.get('transaction_code', 'N/A')}\n"
            )
            context_blocks.append(block)
            
        return "\n".join(context_blocks)
        
    except Exception as e:
        logger.error(f"Error while running query_sap_knowledge_base tool: {e}")
        return f"Error executing database lookup tool: {str(e)}"


# ==================== TOOL 2: EXTERNAL SAP WEB SEARCH ====================

@tool
def search_sap_web_resources(query: str) -> str:
    """
    Searches public SAP forums, SCN notes, and technical blogs for error resolutions.
    ONLY use this tool if query_sap_knowledge_base returns nothing or insufficient data.
    """
    try:
        logger.info(f"🌐 Tool Execution: Searching the web for query: '{query}'")
        
        # Format a highly targeted search query restricted to trusted SAP technical ecosystems
        sanitized_query = f"{query} site:answers.sap.com OR site:blogs.sap.com OR site:sap-experts.com"
        url = f"https://www.google.com/search?q={urllib.parse.quote(sanitized_query)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"Web search failed with status code {response.status_code}"
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract meaningful snippets from Google search results markup card containers
        search_results = []
        for g in soup.find_all('div', class_='g')[:3]:  # Retrieve top 3 public community threads
            anchors = g.find('a')
            title = g.find('h3')
            snippet = g.find('div', class_='VwiC3b')
            
            if anchors and title and snippet:
                search_results.append(
                    f"Title: {title.text}\nURL: {anchors['href']}\nSummary: {snippet.text}\n"
                )
                
        if not search_results:
            return "Web search returned no accessible public results or snippets."
            
        return "\n--- Web Search Results ---\n" + "\n".join(search_results)
        
    except Exception as e:
        logger.error(f"Error executing external web search: {e}")
        return f"Error executing external web search: {str(e)}"


# ==================== AGENT COMPILER CLASS ====================

class SAPAgentWrapper:
    def __init__(self):
        # Dynamically pull the standard API key from Render's environment variables
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.error("❌ Failed to initialize LLM: No Gemini API Key found in environment variables.")
            self.agent_executor = None
            return

        try:
            # Using the highly optimized gemini-2.5-flash token ensures immediate compatibility with your SDK version
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.api_key,
                temperature=0.0
            )
            logger.info("✅ ChatGoogleGenerativeAI (Gemini 2.5 Flash) initialized successfully.")
            
            # Formulate clear multi-resource triage rules within systemic guidelines
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert SAP technical assistant specializing in EWM, MM, QM, PP, AMM, and MFG modules. "
                           "Your objective is to provide comprehensive, actionable resolution steps for errors.\n\n"
                           "Follow these steps sequentially to build your answer:\n"
                           "1. Call 'query_sap_knowledge_base' first to pull historical internal resolution text.\n"
                           "2. If the local search returns no records or insufficient context, immediately call 'search_sap_web_resources' to collect community insights.\n"
                           "3. Synthesize your findings into a unified troubleshooting roadmap, explicitly citing whether it derived from historical company records or active public community contexts."),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # REGISTER BOTH TOOLS HERE
            self.tools = [query_sap_knowledge_base, search_sap_web_resources] 
            
            # Compile using modern Tool Calling architecture
            self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
            self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
            logger.info("✅ SAP Agent Executor compiled cleanly with dual-source lookup capabilities.")
            
        except Exception as e:
            logger.error(f"❌ Failed to create SAP Agent: {e}")
            self.agent_executor = None

    def resolve_error(self, error_message: str, module_filter: str = "All") -> dict:
        """
        Executes the agent executor pipeline to evaluate and fix the incoming error message.
        """
        if not self.agent_executor:
            return {"success": False, "error": "Agent architecture runtime is uninitialized."}
        
        try:
            input_context = f"Context Module Filter: {module_filter}\nIncoming SAP Error: {error_message}"
            response = self.agent_executor.invoke({"input": input_context})
            return {
                "success": True,
                "module": module_filter,
                "response": response.get("output", "No response text generated.")
            }
        except Exception as e:
            logger.error(f"Error encountered during agent execution: {e}")
            return {"success": False, "error": str(e)}

# Instantiate the singleton instance for use by streamlit_app.py
agent = SAPAgentWrapper()
