"""
State management for BMAD artifacts and project metadata.

This module handles all file system interactions within the .bmad directory,
including creating directory structure, saving/loading artifacts, and managing
project metadata.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml
import aiofiles
import asyncio

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages BMAD project state and artifacts in the file system.
    
    All BMAD artifacts are stored in a .bmad directory with the following structure:
    - .bmad/project_meta.json: Project metadata and current phase
    - .bmad/prd/: Product Requirements Documents
    - .bmad/stories/: User stories
    - .bmad/architecture/: Architecture documents
    - .bmad/decisions/: Technical decision logs
    - .bmad/ideation/: Project briefs and ideation notes
    - .bmad/checklists/: Quality validation results
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize StateManager for a project.
        
        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.bmad_dir_name = ".bmad"
        self.bmad_dir = self.project_root / self.bmad_dir_name
        self._lock = asyncio.Lock()  # For concurrent access protection
        
        # Ensure directory structure exists
        asyncio.create_task(self._ensure_structure())
    
    async def _ensure_structure(self) -> None:
        """Ensure .bmad directory structure exists."""
        async with self._lock:
            directories = [
                self.bmad_dir,
                self.bmad_dir / "prd",
                self.bmad_dir / "stories", 
                self.bmad_dir / "architecture",
                self.bmad_dir / "decisions",
                self.bmad_dir / "ideation",
                self.bmad_dir / "checklists",
                self.bmad_dir / "templates",
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            meta_path = self.bmad_dir / "project_meta.json"
            if not meta_path.exists():
                await self._init_project_meta()
    
    async def _init_project_meta(self) -> None:
        """Initialize project metadata file."""
        meta = {
            "project_name": self.project_root.name,
            "bmad_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_phase": "initialization",
            "artifact_paths": {
                "prd": "prd/",
                "stories": "stories/",
                "architecture": "architecture/",
                "decisions": "decisions/",
                "ideation": "ideation/",
                "checklists": "checklists/"
            },
            "artifact_count": {
                "prd": 0,
                "stories": 0,
                "architecture": 0,
                "decisions": 0,
                "ideation": 0,
                "checklists": 0
            }
        }
        await self.save_json("project_meta.json", meta)
        logger.info(f"Initialized BMAD project metadata for '{meta['project_name']}'")
    
    async def save_artifact(
        self, 
        path_in_bmad: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save artifact with optional YAML frontmatter.
        
        Args:
            path_in_bmad: Relative path within .bmad directory
            content: Main content of the artifact
            metadata: Optional metadata to include as YAML frontmatter
            
        Returns:
            Absolute path to the saved file
        """
        async with self._lock:
            full_path = self.bmad_dir / path_in_bmad
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add YAML frontmatter for markdown files if metadata provided
            if metadata and path_in_bmad.endswith('.md'):
                # Ensure metadata has required fields
                if 'created_at' not in metadata:
                    metadata['created_at'] = datetime.now().isoformat()
                metadata['updated_at'] = datetime.now().isoformat()
                
                frontmatter_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
                file_content = f"---\n{frontmatter_str}---\n\n{content}"
            else:
                file_content = content
            
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(file_content)
            
            # Update artifact count in project metadata
            await self._update_artifact_count(path_in_bmad, increment=True)
            
            logger.info(f"Saved artifact: {path_in_bmad}")
            return str(full_path)
    
    async def load_artifact(self, path_in_bmad: str) -> Dict[str, Any]:
        """
        Load artifact and parse YAML frontmatter if present.
        
        Args:
            path_in_bmad: Relative path within .bmad directory
            
        Returns:
            Dictionary with 'content', 'metadata', and 'path' keys
            
        Raises:
            FileNotFoundError: If artifact doesn't exist
        """
        full_path = self.bmad_dir / path_in_bmad
        if not full_path.exists():
            raise FileNotFoundError(f"Artifact not found: {path_in_bmad}")
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            raw_content = await f.read()
        
        parsed_metadata = {}
        main_content = raw_content
        
        # Parse YAML frontmatter for markdown files
        if path_in_bmad.endswith('.md') and raw_content.startswith('---'):
            try:
                parts = raw_content.split('---', 2)
                if len(parts) >= 3:
                    parsed_metadata = yaml.safe_load(parts[1]) or {}
                    main_content = parts[2].strip()
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML frontmatter in {path_in_bmad}: {e}")
        
        return {
            "content": main_content,
            "metadata": parsed_metadata,
            "path": str(full_path)
        }
    
    async def save_json(self, path_in_bmad: str, data: Dict[str, Any]) -> str:
        """
        Save JSON data to file within .bmad directory.
        
        Args:
            path_in_bmad: Relative path within .bmad directory
            data: Data to save as JSON
            
        Returns:
            Absolute path to the saved file
        """
        async with self._lock:
            full_path = self.bmad_dir / path_in_bmad
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            logger.debug(f"Saved JSON: {path_in_bmad}")
            return str(full_path)
    
    async def load_json(self, path_in_bmad: str) -> Dict[str, Any]:
        """
        Load JSON data from file within .bmad directory.
        
        Args:
            path_in_bmad: Relative path within .bmad directory
            
        Returns:
            Loaded JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self.bmad_dir / path_in_bmad
        if not full_path.exists():
            raise FileNotFoundError(f"JSON file not found: {path_in_bmad}")
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    
    async def update_project_phase(self, phase: str) -> None:
        """
        Update the current BMAD phase in project metadata.
        
        Args:
            phase: New phase name
        """
        try:
            meta = await self.load_json("project_meta.json")
            meta["current_phase"] = phase
            meta["updated_at"] = datetime.now().isoformat()
            meta[f"phase_{phase}_started_at"] = datetime.now().isoformat()
            await self.save_json("project_meta.json", meta)
            logger.info(f"Updated project phase to: {phase}")
        except Exception as e:
            logger.error(f"Failed to update project phase: {e}")
            raise
    
    async def get_project_meta(self) -> Dict[str, Any]:
        """
        Get current project metadata.
        
        Returns:
            Project metadata dictionary
        """
        return await self.load_json("project_meta.json")
    
    async def list_artifacts(
        self, 
        artifact_type: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List artifacts in the .bmad directory.
        
        Args:
            artifact_type: Filter by artifact type (prd, stories, etc.)
            status_filter: Filter by status in metadata
            
        Returns:
            List of artifact information dictionaries
        """
        artifacts = []
        search_dir = self.bmad_dir
        
        if artifact_type:
            search_dir = self.bmad_dir / artifact_type
            if not search_dir.exists():
                return artifacts
        
        # Find all markdown and json files
        for file_path in search_dir.rglob("*.md"):
            try:
                relative_path = file_path.relative_to(self.bmad_dir)
                artifact_info = await self.load_artifact(str(relative_path))
                
                # Apply status filter if specified
                if status_filter:
                    artifact_status = artifact_info.get("metadata", {}).get("status", "")
                    if artifact_status != status_filter:
                        continue
                
                artifacts.append({
                    "path": str(relative_path),
                    "type": str(relative_path).split("/")[0] if "/" in str(relative_path) else "root",
                    "status": artifact_info.get("metadata", {}).get("status", "unknown"),
                    "created_at": artifact_info.get("metadata", {}).get("created_at", ""),
                    "updated_at": artifact_info.get("metadata", {}).get("updated_at", "")
                })
            except Exception as e:
                logger.warning(f"Failed to process artifact {file_path}: {e}")
        
        return sorted(artifacts, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    async def _update_artifact_count(self, path_in_bmad: str, increment: bool = True) -> None:
        """Update artifact count in project metadata."""
        try:
            artifact_type = path_in_bmad.split("/")[0] if "/" in path_in_bmad else "root"
            meta = await self.load_json("project_meta.json")
            
            if artifact_type in meta.get("artifact_count", {}):
                current_count = meta["artifact_count"][artifact_type]
                meta["artifact_count"][artifact_type] = max(0, current_count + (1 if increment else -1))
                meta["updated_at"] = datetime.now().isoformat()
                await self.save_json("project_meta.json", meta)
        except Exception as e:
            logger.warning(f"Failed to update artifact count: {e}")
    
    async def delete_artifact(self, path_in_bmad: str) -> bool:
        """
        Delete an artifact file.
        
        Args:
            path_in_bmad: Relative path within .bmad directory
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with self._lock:
                full_path = self.bmad_dir / path_in_bmad
                if full_path.exists():
                    full_path.unlink()
                    await self._update_artifact_count(path_in_bmad, increment=False)
                    logger.info(f"Deleted artifact: {path_in_bmad}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete artifact {path_in_bmad}: {e}")
            return False
    
    def get_bmad_dir(self) -> Path:
        """Get the .bmad directory path."""
        return self.bmad_dir
    
    def get_project_root(self) -> Path:
        """Get the project root directory path."""
        return self.project_root
