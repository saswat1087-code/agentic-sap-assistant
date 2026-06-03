import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

class SAPAgentWrapper:
    def __init__(self):
        # Dynamically pull the standard API key
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            logger.error("❌ Failed to initialize LLM: No Gemini API Key found in environment variables.")
            self.agent_executor = None
            return

        try:
            # Initialize using the standard GenAI library that matches your requirements.txt matrix
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=self.api_key,
                temperature=0.0
            )
            logger.info("✅ ChatGoogleGenerativeAI (Gemini 1.5 Pro) initialized successfully.")
            
            # Reconstruct the agent's prompt blueprint
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert SAP technical assistant specializing in EWM, MM, QM, PP, AMM, and MFG modules. "
                           "Use the provided database context to give precise, actionable resolution steps for errors."),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Build the core execution runtime block (Pass an empty list if tools aren't loaded yet)
            self.tools = [] 
            self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
            self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
            logger.info("✅ SAP Agent Executor compiled cleanly.")
            
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
