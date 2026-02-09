"""
Module system for Conduital

This module system enables commercial feature flags and modular architecture.
Each module can contain models, routes, services, and schemas.

Commercial Configurations:
- basic: Core + Projects (default)
- gtd: Core + Projects + Inbox + Weekly Review
- proactive_assistant: Core + Projects + Memory Layer + AI Context
- full: Everything enabled

Usage:
    from app.modules import ModuleRegistry, get_enabled_modules

    registry = ModuleRegistry()
    for module in get_enabled_modules():
        if module.router:
            app.include_router(module.router, prefix=module.prefix)
"""

from app.modules.base import ModuleBase, ModuleInfo, ModuleRegistry
from app.modules.registry import registry, get_enabled_modules, is_module_enabled

__all__ = [
    "ModuleBase",
    "ModuleInfo",
    "ModuleRegistry",
    "registry",
    "get_enabled_modules",
    "is_module_enabled",
]
