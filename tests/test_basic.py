"""
Basic tests for BMAD MCP Server.
"""

import json
from typing import Any, Dict
import pytest
from pathlib import Path
import tempfile
from unittest.mock import MagicMock

from bmad_mcp_server.utils.state_manager import StateManager
from bmad_mcp_server.tools.base import BMadTool
from bmad_mcp_server.server import BMadMCPServer
from bmad_mcp_server.checklists.loader import load_checklist, list_checklists, Checklist
from bmad_mcp_server.crewai_integration.config import CrewAIConfig
from datetime import datetime

# Mock CrewAIConfig fixture
@pytest.fixture
def mock_crew_ai_config():
    """Fixture for a CrewAIConfig instance with default test settings."""
    return CrewAIConfig(verbose_logging=False)


class MockTool(BMadTool):
    """Mock tool for testing."""
    
    def __init__(self, state_manager=None, crew_ai_config=None):
        # Provide a default mock_crew_ai_config if None is passed for basic instantiation
        if crew_ai_config is None:
            crew_ai_config = CrewAIConfig(verbose_logging=False)
        super().__init__(state_manager, crew_ai_config)
        self.category = "test"
        self.name = "mocktool" # Explicitly set name for consistency if needed
    
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "test_param": {"type": "string"}
            },
            "required": ["test_param"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        param = arguments.get("test_param", "default_value")
        content = f"Mock tool executed with: {param}"
        
        # Tools now return a dict, they don't save directly.
        # If testing interaction with state_manager, it would be indirect.
        # For this mock, we just return the expected structure.
        
        suggested_metadata = self.create_suggested_metadata(
            artifact_type="mock_artifact",
            status="mock_completed", 
            input_param=param
        )
        
        return {
            "content": content,
            "suggested_path": f"mock_outputs/{self.name}_output.md",
            "metadata": suggested_metadata,
            "message": "Mock tool executed successfully."
        }

class MockToolWithState(MockTool):
    """Mock tool that uses StateManager (though tools no longer save directly)."""
    # The premise of this class might need rethinking as tools don't save.
    # However, for testing the base class or if a tool *reads* state, it's still useful.
    def __init__(self, state_manager, crew_ai_config): # Added crew_ai_config
        super().__init__(state_manager, crew_ai_config) # Pass both
        self.name = "mock_with_state" # Ensure name is set

    # Execute method would be similar to MockTool, perhaps reading from state_manager
    # For now, let's keep it simple and inherit execute from MockTool or override if needed.

class TestStateManager:
    """Test StateManager functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def state_manager(self, temp_dir):
        """Create a StateManager instance for testing."""
        return StateManager(project_root=temp_dir)
    
    @pytest.mark.asyncio
    async def test_state_manager_initialization(self, state_manager):
        """Test StateManager initialization."""
        # Check that .bmad directory was created
        bmad_dir = state_manager.get_bmad_dir()
        assert bmad_dir.exists()
        
        # Check that project metadata was created
        meta_path = bmad_dir / "project_meta.json"
        assert meta_path.exists()
        meta = await state_manager.get_project_meta()
        assert meta["bmad_version"] == "1.0"
        assert meta["current_phase"] == "initialization" # Default initial phase
    
    @pytest.mark.asyncio
    async def test_save_and_load_artifact(self, state_manager):
        """Test saving and loading artifacts."""
        content = "# Test Artifact\n\nThis is a test."
        metadata = {"status": "test", "type": "test_artifact"}
        
        # Save artifact
        path = await state_manager.save_artifact("test/test_artifact.md", content, metadata)
        assert Path(path).exists()
        
        # Load artifact
        loaded = await state_manager.load_artifact("test/test_artifact.md")
        assert loaded["content"] == content
        assert loaded["metadata"]["status"] == "test"
        assert loaded["metadata"]["type"] == "test_artifact"
    
    @pytest.mark.asyncio
    async def test_update_project_phase(self, state_manager):
        """Test updating project phase."""
        await state_manager.update_project_phase("testing_phase")
        
        meta = await state_manager.get_project_meta()
        assert meta["current_phase"] == "testing_phase"
        assert "phase_testing_phase_started_at" in meta


class TestBMadTool:
    """Test BMadTool base class."""
    
    def test_tool_name_generation(self, mock_crew_ai_config):
        """Test tool name generation from class name."""
        tool = MockTool(crew_ai_config=mock_crew_ai_config)
        assert tool.name == "mocktool"
    
    def test_input_validation(self, mock_crew_ai_config):
        """Test input validation."""
        tool = MockTool(crew_ai_config=mock_crew_ai_config)
        
        # Valid input
        valid_args = {"test_param": "test_value"}
        validated = tool.validate_input(valid_args)
        assert validated["test_param"] == "test_value"
        
        # Invalid input (missing required field)
        with pytest.raises(ValueError, match="Missing required field"):
            tool.validate_input({})
    
    def test_metadata_creation(self, mock_crew_ai_config):
        """Test suggested metadata creation."""
        tool = MockTool(crew_ai_config=mock_crew_ai_config)
        metadata = tool.create_suggested_metadata(artifact_type="test_artifact", status="test", custom_field="value")
        
        assert metadata["artifact_type"] == "test_artifact"
        assert metadata["status"] == "test"
        assert metadata["generated_by_tool"] == "mocktool"
        assert metadata["bmad_version"] == "1.0"
        assert metadata["custom_field"] == "value"
        assert "suggested_created_at" in metadata
    
    @pytest.mark.asyncio
    async def test_tool_execution(self, mock_crew_ai_config):
        """Test tool execution."""
        tool = MockTool(crew_ai_config=mock_crew_ai_config)
        result = await tool.execute({"test_param": "hello"})
        
        assert isinstance(result, dict)
        assert result["content"] == "Mock tool executed with: hello"
        assert "suggested_path" in result
        assert "metadata" in result
        assert result["metadata"]["input_param"] == "hello"

    @pytest.mark.asyncio
    async def test_tool_with_state_manager_execution(self, state_manager, mock_crew_ai_config): # Add fixture
        """Test tool execution that uses StateManager (conceptually, as tools don't save directly)."""
        tool = MockToolWithState(state_manager, mock_crew_ai_config)
        param_value = "stateful_hello"
        result_dict = await tool.execute({"test_param": param_value})
        
        assert result_dict["content"] == f"Mock tool executed with: {param_value}"
        # The tool itself doesn't save. If we wanted to test saving,
        # we'd call state_manager.save_artifact with the tool's output.
        # For example:
        # await state_manager.save_artifact(
        #     result_dict["suggested_path"], 
        #     result_dict["content"], 
        #     result_dict["metadata"]
        # )
        # artifact_path = state_manager.get_bmad_dir() / result_dict["suggested_path"]
        # assert artifact_path.exists()
        # loaded_artifact = await state_manager.load_artifact(result_dict["suggested_path"])
        # assert loaded_artifact["content"] == result_dict["content"]
        # assert loaded_artifact["metadata"]["input_param"] == param_value


class TestChecklistLoader:
    """Tests for checklist loading functionality."""

    @pytest.fixture
    def checklist_dir(self, tmp_path):
        """Create a temporary checklist directory."""
        chk_dir = tmp_path / "checklists"
        chk_dir.mkdir()
        # Create dummy checklist files
        (chk_dir / "test_checklist_1.md").write_text("# Test Checklist 1\n\n## Section 1\n- [ ] Item 1.1")
        (chk_dir / "pm_checklist.md").write_text("# PM Checklist\n\n## Planning\n- [ ] Define project scope")
        return chk_dir

    def test_list_checklists(self, checklist_dir, monkeypatch):
        """Test listing available checklists."""
        # Patch CHECKLIST_DIR to use the temporary directory
        monkeypatch.setattr("bmad_mcp_server.checklists.loader.CHECKLIST_DIR", checklist_dir)
        
        available_checklists = list_checklists()
        assert "test_checklist_1" in available_checklists
        assert "pm_checklist" in available_checklists
        assert len(available_checklists) == 2

    def test_load_checklist(self, checklist_dir, monkeypatch):
        """Test loading a specific checklist."""
        monkeypatch.setattr("bmad_mcp_server.checklists.loader.CHECKLIST_DIR", checklist_dir)
        
        checklist = load_checklist("pm_checklist")
        assert isinstance(checklist, Checklist)
        assert checklist.name == "pm_checklist"
        assert len(checklist.sections) == 1
        assert checklist.sections[0].title == "Planning"
        assert len(checklist.sections[0].items) == 1
        assert checklist.sections[0].items[0].text == "Define project scope"
        assert checklist.total_items == 1

    def test_load_nonexistent_checklist(self, checklist_dir, monkeypatch):
        """Test loading a non-existent checklist raises FileNotFoundError."""
        monkeypatch.setattr("bmad_mcp_server.checklists.loader.CHECKLIST_DIR", checklist_dir)
        with pytest.raises(FileNotFoundError):
            load_checklist("nonexistent_checklist")


class TestBMadMCPServer:
    """Tests for the BMadMCPServer class."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for server testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
            
    @pytest.fixture
    def server_config_file(self, temp_project_dir):
        """Create a dummy server config file."""
        config_content = {"log_level": "DEBUG"}
        config_path = temp_project_dir / "server_config.json"
        with open(config_path, "w") as f:
            json.dump(config_content, f)
        return config_path

    @pytest.mark.asyncio
    async def test_server_initialization(self, temp_project_dir, server_config_file):
        """Test server initialization and tool registration."""
        # Mock tool imports within _register_tools to avoid actual file dependencies for this basic test
        # This is a bit of a hack; ideally, tools would be injectable or mocked more cleanly.
        
        original_import = __import__

        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith("bmad_mcp_server.tools."):
                # Return a mock module that has mock tool classes
                mock_module = MagicMock()
                mock_module.CreateProjectBriefTool = MagicMock(spec=BMadTool)
                mock_module.CreateProjectBriefTool.return_value = MockTool() # Return an instance
                # Add other tools as needed for registration
                mock_module.GeneratePRDTool = MagicMock(spec=BMadTool)
                mock_module.GeneratePRDTool.return_value = MockTool()
                mock_module.ValidateRequirementsTool = MagicMock(spec=BMadTool)
                mock_module.ValidateRequirementsTool.return_value = MockTool()
                mock_module.CreateArchitectureTool = MagicMock(spec=BMadTool)
                mock_module.CreateArchitectureTool.return_value = MockTool()
                mock_module.CreateFrontendArchitectureTool = MagicMock(spec=BMadTool)
                mock_module.CreateFrontendArchitectureTool.return_value = MockTool()
                mock_module.CreateNextStoryTool = MagicMock(spec=BMadTool)
                mock_module.CreateNextStoryTool.return_value = MockTool()
                mock_module.ValidateStoryTool = MagicMock(spec=BMadTool)
                mock_module.ValidateStoryTool.return_value = MockTool()
                mock_module.RunChecklistTool = MagicMock(spec=BMadTool)
                mock_module.RunChecklistTool.return_value = MockTool()
                mock_module.CorrectCourseTool = MagicMock(spec=BMadTool)
                mock_module.CorrectCourseTool.return_value = MockTool()
                return mock_module
            return original_import(name, globals, locals, fromlist, level)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("builtins.__import__", mock_import)
            server = BMadMCPServer(config_path=server_config_file, project_root=temp_project_dir)
        
        assert server is not None
        assert server.project_root == temp_project_dir
        assert server.config["log_level"] == "DEBUG"
        
        # Check if tools were "registered" with FastMCP
        registered_mcp_tools = await server.mcp.get_tools()
        assert len(registered_mcp_tools) > 0 # Check that some tools are registered
        
        # With the current mocking, all tools are instances of MockTool, 
        # and their names when registered via the async def wrappers in server.py 
        # will be like 'create_project_brief', 'generate_prd', etc.
        # The mock_import replaces the *classes* (e.g., CreateProjectBriefTool)
        # with a MagicMock that returns a MockTool instance.
        # The server.py then uses these class names to define its async functions.
        
        # Check for a few key tool names that should be registered by _register_native_tools
        assert "create_project_brief" in registered_mcp_tools
        assert "generate_prd" in registered_mcp_tools
        assert "run_checklist" in registered_mcp_tools
        # Add more checks if necessary for other tools

    # Add more server tests, e.g., for run_stdio, run_sse, if they can be tested without full I/O.
    # Testing run_stdio/run_sse might require more complex mocking of FastMCP's methods.


if __name__ == "__main__":
    pytest.main([__file__])
