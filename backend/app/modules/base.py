"""
Base classes for the module system

A module represents a discrete feature set that can be enabled/disabled.
Modules can declare dependencies on other modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any

from fastapi import APIRouter


class ModuleCategory(str, Enum):
    """Categories for organizing modules"""
    CORE = "core"           # Always enabled, fundamental functionality
    FEATURE = "feature"     # Optional feature modules
    INTEGRATION = "integration"  # External integrations (AI, sync, etc.)


@dataclass
class ModuleInfo:
    """
    Metadata about a module
    """
    name: str                           # Unique identifier (e.g., "memory_layer")
    display_name: str                   # Human-readable name
    description: str                    # Module description
    category: ModuleCategory            # Module category
    version: str = "1.0.0"              # Module version
    dependencies: list[str] = field(default_factory=list)  # Required modules
    optional_dependencies: list[str] = field(default_factory=list)  # Optional enhancements


class ModuleBase(ABC):
    """
    Abstract base class for all modules.

    Each module must implement:
    - info: ModuleInfo with metadata
    - initialize(): Setup logic called on startup
    - router (optional): FastAPI router for API endpoints

    Example:
        class MemoryLayerModule(ModuleBase):
            @property
            def info(self) -> ModuleInfo:
                return ModuleInfo(
                    name="memory_layer",
                    display_name="Memory Layer",
                    description="Persistent memory for AI assistants",
                    category=ModuleCategory.FEATURE,
                    dependencies=["core", "projects"]
                )

            @property
            def router(self) -> Optional[APIRouter]:
                from app.modules.memory_layer.routes import router
                return router

            async def initialize(self, app_context: dict) -> None:
                # Register models, setup services, etc.
                pass
    """

    @property
    @abstractmethod
    def info(self) -> ModuleInfo:
        """Return module metadata"""
        pass

    @property
    def router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this module's endpoints (optional)"""
        return None

    @property
    def prefix(self) -> str:
        """URL prefix for this module's routes (defaults to module name)"""
        return self.info.name.replace("_", "-")

    @property
    def tags(self) -> list[str]:
        """OpenAPI tags for this module's endpoints"""
        return [self.info.display_name]

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """
        Initialize module on application startup.

        Override this to perform setup tasks like:
        - Registering event handlers
        - Starting background tasks
        - Initializing services

        Args:
            app_context: Shared context dict with 'app', 'settings', etc.
        """
        pass

    async def shutdown(self) -> None:
        """
        Cleanup module on application shutdown.

        Override this to perform cleanup like:
        - Stopping background tasks
        - Closing connections
        """
        pass

    def check_dependencies(self, enabled_modules: set[str]) -> list[str]:
        """
        Check if all required dependencies are enabled.

        Returns:
            List of missing dependency names (empty if all satisfied)
        """
        missing = []
        for dep in self.info.dependencies:
            if dep not in enabled_modules:
                missing.append(dep)
        return missing


class ModuleRegistry:
    """
    Registry for all available modules.

    Handles module registration, dependency resolution, and initialization order.
    """

    def __init__(self):
        self._modules: dict[str, ModuleBase] = {}
        self._initialized: set[str] = set()

    def register(self, module: ModuleBase) -> None:
        """Register a module"""
        name = module.info.name
        if name in self._modules:
            raise ValueError(f"Module '{name}' is already registered")
        self._modules[name] = module

    def get(self, name: str) -> Optional[ModuleBase]:
        """Get a module by name"""
        return self._modules.get(name)

    def all(self) -> list[ModuleBase]:
        """Get all registered modules"""
        return list(self._modules.values())

    def get_enabled(self, enabled_names: set[str]) -> list[ModuleBase]:
        """
        Get modules that should be enabled, in dependency order.

        Args:
            enabled_names: Set of module names to enable

        Returns:
            List of modules in initialization order (dependencies first)

        Raises:
            ValueError: If dependencies are not satisfied
        """
        # First, validate all dependencies
        for name in enabled_names:
            module = self._modules.get(name)
            if not module:
                raise ValueError(f"Unknown module: {name}")

            missing = module.check_dependencies(enabled_names)
            if missing:
                raise ValueError(
                    f"Module '{name}' requires modules: {missing}"
                )

        # Topological sort for initialization order
        ordered = []
        visited = set()
        temp_mark = set()

        def visit(name: str):
            if name in temp_mark:
                raise ValueError(f"Circular dependency detected involving '{name}'")
            if name in visited:
                return
            if name not in enabled_names:
                return

            module = self._modules[name]
            temp_mark.add(name)

            for dep in module.info.dependencies:
                visit(dep)

            temp_mark.remove(name)
            visited.add(name)
            ordered.append(module)

        for name in enabled_names:
            visit(name)

        return ordered

    async def initialize_all(
        self,
        enabled_names: set[str],
        app_context: dict[str, Any]
    ) -> list[ModuleBase]:
        """
        Initialize all enabled modules in dependency order.

        Args:
            enabled_names: Set of module names to enable
            app_context: Shared context for initialization

        Returns:
            List of initialized modules
        """
        modules = self.get_enabled(enabled_names)

        for module in modules:
            if module.info.name not in self._initialized:
                await module.initialize(app_context)
                self._initialized.add(module.info.name)

        return modules

    async def shutdown_all(self) -> None:
        """Shutdown all initialized modules in reverse order"""
        # Reverse order for shutdown
        for name in reversed(list(self._initialized)):
            module = self._modules.get(name)
            if module:
                await module.shutdown()

        self._initialized.clear()
