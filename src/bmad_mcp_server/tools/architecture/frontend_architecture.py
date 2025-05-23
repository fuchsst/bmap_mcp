"""
Frontend architecture creation tool using BMAD methodology.
"""

from typing import Any, Dict, Optional
from crewai import Agent, Crew, Task, Process
from pydantic import BaseModel, Field
import logging

from ..base import BMadTool
from ...crewai_integration.agents import get_architect_agent
from ...utils.state_manager import StateManager

logger = logging.getLogger(__name__)


class FrontendArchitectureRequest(BaseModel):
    """Request model for frontend architecture creation."""
    main_architecture: str = Field(..., description="Main architecture document content")
    ux_specification: str = Field(
        default="",
        description="UI/UX requirements and specifications"
    )
    framework_preference: str = Field(
        default="",
        description="Preferred frontend framework"
    )
    component_strategy: str = Field(
        default="atomic",
        description="Component design strategy"
    )
    state_management: str = Field(
        default="",
        description="Preferred state management approach"
    )


class CreateFrontendArchitectureTool(BMadTool):
    """
    Generate frontend-specific architecture specifications using BMAD methodology.
    
    This tool creates detailed frontend architecture documents that complement
    the main technical architecture with frontend-specific concerns and patterns.
    """
    
    def __init__(self, state_manager: StateManager):
        super().__init__(state_manager)
        self.category = "architecture"
        self.description = "Generate frontend-specific architecture specifications"
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for frontend architecture creation using Pydantic model."""
        schema = FrontendArchitectureRequest.model_json_schema()
        # Add enum constraints
        schema["properties"]["component_strategy"]["enum"] = ["atomic", "modular", "feature-based", "layered"]
        schema["properties"]["framework_preference"]["enum"] = ["React", "Vue", "Angular", "Svelte", "React Native", "Flutter", ""]
        schema["properties"]["state_management"]["enum"] = ["Redux", "Zustand", "Context API", "Vuex", "Pinia", "NgRx", ""]
        return schema
    
    async def execute(self, arguments: Dict[str, Any]) -> str:
        """Execute frontend architecture generation."""
        # Validate input using Pydantic
        request = FrontendArchitectureRequest(**arguments)
        
        logger.info("Starting frontend architecture generation")
        
        # Analyze main architecture for frontend context
        frontend_complexity = self._analyze_frontend_complexity(request.main_architecture)
        
        # Create architect agent
        architect_agent = get_architect_agent()
        
        # Create frontend architecture generation task
        frontend_task = Task(
            description=f"""
            Create a comprehensive frontend architecture document based on the main architecture:
            
            {request.main_architecture}
            
            Frontend Parameters:
            - Framework Preference: {request.framework_preference or 'To be determined based on requirements'}
            - Component Strategy: {request.component_strategy}
            - State Management: {request.state_management or 'To be determined based on complexity'}
            - Frontend Complexity Score: {frontend_complexity}/10
            
            UX Specification:
            {request.ux_specification or 'No specific UX requirements provided'}
            
            Follow the BMAD frontend architecture template structure:
            1. Frontend Technical Summary
            2. Framework and Core Libraries Selection
            3. Component Architecture Strategy
            4. State Management Approach
            5. Routing and Navigation Design
            6. Build and Bundling Configuration
            7. Performance Optimization Strategy
            8. Accessibility and Internationalization
            9. Testing Strategy (Unit, Integration, E2E)
            10. Development Workflow and Standards
            11. Deployment and CI/CD Pipeline
            12. Security Considerations
            13. Error Handling and Monitoring
            
            Ensure the frontend architecture:
            - Aligns with the main technical architecture
            - Follows modern frontend best practices
            - Is optimized for AI agent implementation
            - Includes specific library versions and justifications
            - Addresses scalability and maintainability
            - Provides clear development guidelines
            """,
            expected_output="Complete frontend architecture document in markdown format",
            agent=architect_agent
        )
        
        # Execute frontend architecture generation
        crew = Crew(
            agents=[architect_agent],
            tasks=[frontend_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        frontend_content = result.raw if hasattr(result, 'raw') else str(result)
        
        # Format the final frontend architecture
        formatted_arch = self._format_frontend_architecture(
            frontend_content,
            request.framework_preference,
            frontend_complexity
        )
        
        # Save the artifact
        metadata = self.create_metadata(
            status="completed",
            framework_preference=request.framework_preference,
            component_strategy=request.component_strategy,
            state_management=request.state_management,
            complexity_score=frontend_complexity
        )
        
        # Generate filename
        framework_suffix = request.framework_preference.lower().replace(" ", "_") if request.framework_preference else "generic"
        file_name = f"frontend_architecture_{framework_suffix}.md"
        artifact_path = f"architecture/{file_name}"
        
        await self.state_manager.save_artifact(artifact_path, formatted_arch, metadata)
        await self.state_manager.update_project_phase("frontend_architecture_completed")
        
        logger.info(f"Frontend architecture saved to: {artifact_path}")
        
        return formatted_arch
    
    def _analyze_frontend_complexity(self, main_architecture: str) -> int:
        """Analyze frontend complexity based on main architecture."""
        arch_lower = main_architecture.lower()
        
        # Calculate complexity factors
        ui_complexity = 0
        if "dashboard" in arch_lower or "admin" in arch_lower:
            ui_complexity += 2
        if "real-time" in arch_lower or "websocket" in arch_lower:
            ui_complexity += 2
        if "mobile" in arch_lower or "responsive" in arch_lower:
            ui_complexity += 1
        if "authentication" in arch_lower or "auth" in arch_lower:
            ui_complexity += 1
        if "api" in arch_lower:
            ui_complexity += 1
        if "microservice" in arch_lower:
            ui_complexity += 2
        if "spa" in arch_lower or "single page" in arch_lower:
            ui_complexity += 1
        
        return min(ui_complexity, 10)
    
    def _format_frontend_architecture(self, content: str, framework: str, complexity: int) -> str:
        """Format frontend architecture document with proper structure."""
        formatted = content
        
        # Add implementation guidance
        implementation_guidance = f"""
---

## Implementation Guidance for AI Agents

### Development Priority Order
1. **Setup and Configuration** - Framework setup, build tools, and development environment
2. **Core Components** - Base components and design system foundation
3. **State Management** - Data flow and state management implementation
4. **Routing and Navigation** - Application structure and navigation
5. **Feature Components** - Business logic and feature-specific components
6. **Integration** - API integration and backend connectivity
7. **Testing and Quality** - Test implementation and quality assurance
8. **Performance and Optimization** - Performance tuning and optimization

### AI Agent Development Notes
- Framework: {framework or 'To be selected based on requirements'}
- Complexity Level: {complexity}/10
- Recommended approach: {'Component-first development' if complexity <= 5 else 'Architecture-first development'}
- Testing strategy: {'Unit tests focus' if complexity <= 5 else 'Full testing pyramid'}

### Key Implementation Patterns
- Use TypeScript for type safety and better AI agent understanding
- Implement atomic design principles for component reusability
- Follow consistent naming conventions for AI agent navigation
- Include comprehensive JSDoc comments for AI agent context
"""
        
        formatted += implementation_guidance
        formatted += "\n\n---\n*Generated using BMAD MCP Server - Frontend Architecture Tool*"
        return formatted
