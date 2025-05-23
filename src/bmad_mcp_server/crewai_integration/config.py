"""
CrewAI configuration for BMAD MCP Server.
"""

import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


from typing import Optional

@dataclass
class CrewAIConfig:
    """Configuration for CrewAI agent behavior."""
    
    verbose: bool = False
    max_iter: int = 15  # Default max iterations for agent tasks
    memory: bool = True   # Whether agents should use memory by default
    
    def __post_init__(self):
        """Load configuration from environment variables, overriding defaults."""
        self.verbose = os.getenv("CREWAI_VERBOSE", str(self.verbose)).lower() == "true"
        self.max_iter = int(os.getenv("CREWAI_MAX_ITER", str(self.max_iter)))
        self.memory = os.getenv("CREWAI_MEMORY_ENABLED", str(self.memory)).lower() == "true"
        
        logger.info(
            f"CrewAIConfig loaded: verbose={self.verbose}, max_iter={self.max_iter}, memory={self.memory}"
        )

# Global instance for easy access by agent creation functions
crew_ai_config = CrewAIConfig()
