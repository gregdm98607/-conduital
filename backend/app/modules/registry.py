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
    # Conduital Basic: Core functionality only (free tier)
    "basic": {
        "core",
        "projects",
    },

    # Conduital Workflow: Full workflow support
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


def get_modules_for_tier(tier: str) -> set[str]:
    """
    Get the set of module names allowed for a commercial tier.

    Tier-to-preset mapping:
        free → basic   (core, projects)
        gtd  → gtd     (core, projects, gtd_inbox)
        full → full    (core, projects, gtd_inbox, memory_layer, ai_context)

    Args:
        tier: Commercial tier name (free, gtd, full)

    Returns:
        Set of module names the tier permits
    """
    tier_to_preset = {
        "free": "basic",
        "gtd": "gtd",
        "full": "full",
    }
    preset_name = tier_to_preset.get(tier, "basic")
    return COMMERCIAL_PRESETS.get(preset_name, COMMERCIAL_PRESETS["basic"]).copy()


def is_module_allowed_for_tier(module_name: str, tier: str) -> bool:
    """
    Check if a module is permitted under a given commercial tier.

    This is the license-aware complement to is_module_enabled().
    is_module_enabled() checks whether the module is loaded in the runtime.
    is_module_allowed_for_tier() checks whether the user's license permits it.

    Both must be True for a user to access a gated module.

    Args:
        module_name: Name of the module to check
        tier: User's effective commercial tier (free, gtd, full)

    Returns:
        True if the tier allows this module
    """
    return module_name in get_modules_for_tier(tier)


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
