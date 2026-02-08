"""
Module registry and commercial configuration presets

This file defines:
1. The global module registry
2. Commercial configuration presets
3. Helper functions for checking module status
"""

from typing import Optional
from app.modules.base import ModuleRegistry, ModuleBase

# Global registry instance
registry = ModuleRegistry()


# =============================================================================
# Commercial Configuration Presets
# =============================================================================

COMMERCIAL_PRESETS: dict[str, set[str]] = {
    # Conduital Basic: Core functionality only
    "basic": {
        "core",
        "projects",
    },

    # Conduital GTD: Full workflow support
    "gtd": {
        "core",
        "projects",
        "gtd_inbox",
    },

    # Proactive Assistant: AI memory and context
    "proactive_assistant": {
        "core",
        "projects",
        "memory_layer",
        "ai_context",
    },

    # Full Suite: Everything enabled
    "full": {
        "core",
        "projects",
        "gtd_inbox",
        "memory_layer",
        "ai_context",
    },
}


def get_preset_modules(preset_name: str) -> set[str]:
    """
    Get module set for a commercial preset.

    Args:
        preset_name: Name of preset (basic, gtd, proactive_assistant, full)

    Returns:
        Set of module names to enable

    Raises:
        ValueError: If preset name is unknown
    """
    if preset_name not in COMMERCIAL_PRESETS:
        valid = ", ".join(COMMERCIAL_PRESETS.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Valid presets: {valid}")
    return COMMERCIAL_PRESETS[preset_name].copy()


# =============================================================================
# Runtime State
# =============================================================================

# Set of currently enabled module names (populated at startup)
_enabled_modules: set[str] = set()


def set_enabled_modules(modules: set[str]) -> None:
    """Set the enabled modules (called during app startup)"""
    global _enabled_modules
    _enabled_modules = modules.copy()


def get_enabled_modules() -> list[ModuleBase]:
    """
    Get list of enabled module instances.

    Returns:
        List of enabled ModuleBase instances
    """
    return registry.get_enabled(_enabled_modules)


def is_module_enabled(module_name: str) -> bool:
    """
    Check if a specific module is enabled.

    Useful for conditional logic in services/routes:

        if is_module_enabled("memory_layer"):
            # Include memory context
            pass

    Args:
        module_name: Name of module to check

    Returns:
        True if module is enabled
    """
    return module_name in _enabled_modules


def get_enabled_module_names() -> set[str]:
    """Get set of enabled module names"""
    return _enabled_modules.copy()


# =============================================================================
# Module Registration
# =============================================================================

def register_all_modules() -> None:
    """
    Register all available modules with the registry.

    Called once during application initialization.
    """
    # Import and register each module
    # Core modules (always available)
    from app.modules.core import CoreModule
    from app.modules.projects import ProjectsModule

    registry.register(CoreModule())
    registry.register(ProjectsModule())

    # Feature modules (optional)
    try:
        from app.modules.gtd_inbox import GTDInboxModule
        registry.register(GTDInboxModule())
    except ImportError:
        pass  # Module not yet implemented

    try:
        from app.modules.memory_layer import MemoryLayerModule
        registry.register(MemoryLayerModule())
    except ImportError:
        pass  # Module not yet implemented

    try:
        from app.modules.ai_context import AIContextModule
        registry.register(AIContextModule())
    except ImportError:
        pass  # Module not yet implemented
