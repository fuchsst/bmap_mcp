"""
CrewAI configuration for BMAD MCP Server.
Handles global CrewAI settings and agent-specific LLM configurations.
LLM configurations are stored as string identifiers (e.g., "openai/gpt-4o-mini")
and passed directly to CrewAI's Agent class.
"""

import os
import logging
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CrewAIConfig(BaseModel):
    """Configuration for CrewAI agent behavior and LLM selection."""
    
    # Global CrewAI settings
    verbose_logging: bool = Field(default_factory=lambda: os.getenv("CREWAI_VERBOSE", "false").lower() == "true")
    max_iter: int = Field(default_factory=lambda: int(os.getenv("CREWAI_MAX_ITER", "15")))
    memory_enabled: bool = Field(default_factory=lambda: os.getenv("CREWAI_MEMORY_ENABLED", "true").lower() == "true")
    
    # Default LLM identifier if no agent-specific one is set
    default_llm_identifier: str = Field(default_factory=lambda: os.getenv("BMAD_DEFAULT_LLM", "openai/gpt-4o-mini"))

    # Agent-specific LLM identifiers from environment variables
    # These will be string identifiers like "openai/gpt-4-turbo" or "anthropic/claude-3-sonnet"
    analyst_agent_llm_identifier: Optional[str] = Field(default_factory=lambda: os.getenv("BMAD_ANALYST_AGENT_LLM"))
    pm_agent_llm_identifier: Optional[str] = Field(default_factory=lambda: os.getenv("BMAD_PM_AGENT_LLM"))
    architect_agent_llm_identifier: Optional[str] = Field(default_factory=lambda: os.getenv("BMAD_ARCHITECT_AGENT_LLM"))
    # Add other agent LLM identifiers here as new agents are defined
    # e.g., developer_agent_llm_identifier: Optional[str] = Field(default_factory=lambda: os.getenv("BMAD_DEVELOPER_AGENT_LLM"))

    # Internal cache for LLM string identifiers
    _llm_identifiers_map: Dict[str, Optional[str]] = {}

    def model_post_init(self, __context: Any) -> None:
        """Initialize LLM identifiers after Pydantic model initialization."""
        self._initialize_llm_identifiers()
        logger.info(
            f"CrewAIConfig loaded: verbose={self.verbose_logging}, max_iter={self.max_iter}, "
            f"memory={self.memory_enabled}, default_llm='{self.default_llm_identifier}'"
        )
        logger.debug(f"Agent-specific LLM identifiers: Analyst='{self.analyst_agent_llm_identifier}', PM='{self.pm_agent_llm_identifier}', Architect='{self.architect_agent_llm_identifier}'")

    def _initialize_llm_identifiers(self) -> None:
        """Populates the internal map of agent type to LLM string identifier."""
        self._llm_identifiers_map['default'] = self.default_llm_identifier
        
        agent_llm_config_map = {
            "analyst": self.analyst_agent_llm_identifier,
            "pm": self.pm_agent_llm_identifier,
            "architect": self.architect_agent_llm_identifier,
            # "developer": self.developer_agent_llm_identifier, # Example
        }

        for agent_key, model_id_str in agent_llm_config_map.items():
            if model_id_str: # If an agent-specific LLM identifier is defined
                self._llm_identifiers_map[agent_key] = model_id_str
            else: # Otherwise, use the default LLM identifier string
                self._llm_identifiers_map[agent_key] = self._llm_identifiers_map['default']
        
        if self.verbose_logging:
            logger.debug(f"Initialized LLM identifiers map: {self._llm_identifiers_map}")

    def get_llm_identifier_for_agent(self, agent_type: str) -> Optional[str]:
        """
        Returns the LLM string identifier for a given agent type.
        Falls back to the default LLM identifier if no specific one is configured for the agent.
        Agent types should be simple keys like "analyst", "pm", "architect".
        """
        return self._llm_identifiers_map.get(agent_type, self._llm_identifiers_map.get('default'))

# Note: A global instance `crew_ai_config` is no longer created here.
# The BMadMCPServer instance will create and hold its own CrewAIConfig instance.
