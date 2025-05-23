"""
Template loading and management for BMAD documents.
"""

from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent

# Template cache
_template_cache: Dict[str, str] = {}


def load_template(template_name: str) -> str:
    """
    Load a BMAD template by name.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        Template content as string
        
    Raises:
        FileNotFoundError: If template doesn't exist
    """
    if template_name in _template_cache:
        return _template_cache[template_name]
    
    template_path = TEMPLATE_DIR / template_name
    
    if not template_path.exists():
        logger.error(f"Template not found: {template_name}")
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        _template_cache[template_name] = content
        logger.debug(f"Loaded template: {template_name}")
        return content
        
    except Exception as e:
        logger.error(f"Error loading template {template_name}: {e}")
        raise


def list_templates() -> List[str]:
    """
    List available templates.
    
    Returns:
        List of template file names
    """
    return [f.name for f in TEMPLATE_DIR.glob("*.md")]


def get_template_path(template_name: str) -> Path:
    """
    Get the full path to a template file.
    
    Args:
        template_name: Name of the template file
        
    Returns:
        Path to the template file
    """
    return TEMPLATE_DIR / template_name


def clear_template_cache() -> None:
    """Clear the template cache."""
    global _template_cache
    _template_cache.clear()
    logger.debug("Template cache cleared")
