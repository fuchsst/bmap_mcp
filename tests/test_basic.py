"""
Basic tests for BMAD MCP Server.
"""

import json
import pytest
from pathlib import Path
import tempfile
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock

from bmad_mcp_server.utils.state_manager import StateManager
from bmad_mcp_server.tools.base import BMadTool
from bmad_mcp_server.server import BMadMCPServer
from bmad_mcp_server.checklists.loader import load_checklist, list_checklists, Checklist


class MockTool(BMadTool):
    """Mock tool for testing."""
    
    def __init__(self, state_manager=None):
        super().__init__(state_manager)
        self.category = "test"
    
    def get_input_schema(self):
        return {
            "type": "object",
            "properties": {
                "test_param": {"type": "string"}
            },
            "required": ["test_param"]
        }
    
    async def execute(self, arguments):
        if self.state_manager:
            # Simulate saving an artifact
            await self.state_manager.save_artifact(
                f"test/{self.name}_output.md", 
                f"Output for {arguments['test_param']}",
                self.create_metadata(status="completed", input_param=arguments['test_param'])
            )
        return f"Mock tool executed with: {arguments['test_param']}"

class MockToolWithState(MockTool):
    """Mock tool that uses StateManager."""
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.name = "mock_with_state"

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
    
    def test_tool_name_generation(self):
        """Test tool name generation from class name."""
        tool = MockTool()
        assert tool.name == "mock"
    
    def test_input_validation(self):
        """Test input validation."""
        tool = MockTool()
        
        # Valid input
        valid_args = {"test_param": "test_value"}
        validated = tool.validate_input(valid_args)
        assert validated["test_param"] == "test_value"
        
        # Invalid input (missing required field)
        with pytest.raises(ValueError, match="Missing required field"):
            tool.validate_input({})
    
    def test_metadata_creation(self):
        """Test metadata creation."""
        tool = MockTool()
        metadata = tool.create_metadata(status="test", custom_field="value")
        
        assert metadata["status"] == "test"
        assert metadata["tool_name"] == "mock"
        assert metadata["bmad_version"] == "1.0"
        assert metadata["custom_field"] == "value"
        assert "created_at" in metadata
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        tool = MockTool()
        result = await tool.execute({"test_param": "hello"})
        assert result == "Mock tool executed with: hello"

    @pytest.mark.asyncio
    async def test_tool_with_state_manager_execution(self, state_manager):
        """Test tool execution that uses StateManager."""
        tool = MockToolWithState(state_manager)
        param_value = "stateful_hello"
        result = await tool.execute({"test_param": param_value})
        assert result == f"Mock tool executed with: {param_value}"

        # Verify artifact was saved
        artifact_path = state_manager.get_bmad_dir() / f"test/{tool.name}_output.md"
        assert artifact_path.exists()
        
        loaded_artifact = await state_manager.load_artifact(f"test/{tool.name}_output.md")
        assert loaded_artifact["content"] == f"Output for {param_value}"
        assert loaded_artifact["metadata"]["input_param"] == param_value
        assert loaded_artifact["metadata"]["status"] == "completed"


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

    def test_server_initialization(self, temp_project_dir, server_config_file):
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
        # Check if tools were "registered" (mocked tools in this case)
        # The number of tools registered depends on how many are mocked in _register_tools
        # Based on the current server.py, it registers 9 tools.
        assert len(server.tools) > 0 # Check that some tools are registered
        assert "create_project_brief" in server.tools # Example tool name
        assert "run_checklist" in server.tools

    # Add more server tests, e.g., for run_stdio, run_sse, if they can be tested without full I/O.
    # Testing run_stdio/run_sse might require more complex mocking of FastMCP's methods.


if __name__ == "__main__":
    pytest.main([__file__])
