"""
Base classes and interfaces for BMAD MCP tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import logging

from ..utils.state_manager import StateManager
from ..crewai_integration.config import CrewAIConfig

logger = logging.getLogger(__name__)


class BMadTool(ABC):
    """
    Abstract base class for all BMAD MCP tools.
    
    All BMAD tools must inherit from this class and implement the required methods.
    This ensures consistent interface and behavior across all tools.
    """
    
    def __init__(self, state_manager: StateManager, crew_ai_config: CrewAIConfig):
        """
        Initialize BMAD tool.
        
        Args:
            state_manager: StateManager instance for artifact persistence and context reading.
            crew_ai_config: CrewAIConfig instance for agent configurations.
        """
        if state_manager is None:
            raise ValueError("StateManager instance is required for BMadTool.")
        if crew_ai_config is None:
            raise ValueError("CrewAIConfig instance is required for BMadTool.")
            
        self.state_manager = state_manager
        self.crew_ai_config = crew_ai_config
        
        # Tool name derived from class name (e.g., CreateProjectBriefTool -> create_project_brief)
        class_name = self.__class__.__name__
        if class_name.endswith('Tool'):
            class_name = class_name[:-4]  # Remove 'Tool' suffix
        
        # Convert CamelCase to snake_case
        self.name = self._camel_to_snake(class_name)
        
        # Description from docstring or default
        self.description = self.__doc__ or f"BMAD {self.name} tool"
        
        # Default category, can be overridden by subclasses
        self.category = "general"
        
        logger.debug(f"Initialized tool: {self.name}")
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given arguments.
        Should return a dictionary containing:
        - 'content': The generated artifact content (e.g., Markdown string).
        - 'suggested_path': A string suggesting where the artifact might be saved (relative to .bmad).
        - 'metadata': A dictionary of metadata for the artifact (e.g., type, status).
        - 'message': (Optional) A message for the user/assistant.
        
        Args:
            arguments: Tool input arguments validated against input schema
            
        Returns:
            A dictionary with the tool's output.
            
        Raises:
            Exception: If tool execution fails
        """
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for tool input validation.
        
        Returns:
            JSON schema dictionary defining required and optional parameters
        """
        pass
    
    def validate_input(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize input arguments.
        
        Args:
            arguments: Raw input arguments
            
        Returns:
            Validated and normalized arguments
            
        Raises:
            ValueError: If validation fails
        """
        schema = self.get_input_schema()
        required_fields = schema.get("required", [])
        
        # Check required fields
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required field: {field}")
        
        # Apply defaults for optional fields
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in arguments and "default" in field_schema:
                arguments[field] = field_schema["default"]
        
        return arguments
    
    def create_suggested_metadata(self, artifact_type: str, status: str = "draft", **kwargs) -> Dict[str, Any]:
        """
        Create standard suggested metadata for artifacts to be returned to the assistant.
        
        Args:
            artifact_type: The type of artifact (e.g., "project_brief", "prd").
            status: Suggested artifact status (draft, review, approved, etc.)
            **kwargs: Additional metadata fields
            
        Returns:
            Metadata dictionary with standard fields for suggestion.
        """
        metadata = {
            "artifact_type": artifact_type,
            "status": status,
            "suggested_created_at": datetime.now().isoformat(),
            "suggested_updated_at": datetime.now().isoformat(),
            "generated_by_tool": self.name,
            "bmad_version": "1.0"
        }
        metadata.update(kwargs)
        return metadata
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get tool information for registration.
        
        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "input_schema": self.get_input_schema()
        }


class BMadValidationError(Exception):
    """Exception raised when tool input validation fails."""
    pass


class BMadExecutionError(Exception):
    """Exception raised when tool execution fails."""
    pass
