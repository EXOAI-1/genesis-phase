"""
phase/plugin_base.py — Plugin interface for PHASE.

Adding a new FLUX node type (e.g. SKYNET logistics, a translator,
a database manager) requires:

  1. Create a file in plugins/  e.g.  plugins/skynet/__init__.py
  2. Subclass FluxNode and implement execute()
  3. Create a PhasePlugin descriptor in your __init__.py
  4. Add the node model to model_config.yaml under flux:
       your_node_type: "google/gemini-flash-1.5"
  5. Add the plugin name to bootstrap.py PLUGINS list
     OR use /phase plugin load <name> in Telegram

PHASE will auto-discover and load the plugin.

─────────────────────────────────────────────────────────
MINIMAL PLUGIN EXAMPLE
─────────────────────────────────────────────────────────

# plugins/translator/__init__.py

from flux_base import FluxNode
from task import Task
from plugin_base import PhasePlugin

class TranslatorNode(FluxNode):
    node_type     = "translator"
    system_prompt = "You are a professional translator. Translate accurately."

    async def execute(self, task: Task) -> str:
        return await self.llm(task.goal, max_tokens=800)

PLUGIN = PhasePlugin(
    name        = "translator",
    version     = "1.0.0",
    description = "Translates text between languages",
    node_class  = TranslatorNode,
    author      = "your name",
    requires    = [],   # other plugin names this depends on
)

─────────────────────────────────────────────────────────
PLUGIN WITH CONFIG
─────────────────────────────────────────────────────────
Add to model_config.yaml:
  flux:
    translator: "google/gemini-flash-1.5"

PLASMA will use this model for all translator tasks.
─────────────────────────────────────────────────────────
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Type

from flux_base import FluxNode

logger = logging.getLogger(__name__)

PLUGINS_DIR = Path(__file__).parent / "plugins"


@dataclass
class PhasePlugin:
    """Descriptor for a PHASE plugin."""
    name:        str
    version:     str
    description: str
    node_class:  Type[FluxNode]
    author:      str       = "unknown"
    requires:    list[str] = field(default_factory=list)
    tags:        list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Returns list of validation errors (empty = OK)."""
        errors = []
        if not self.name:
            errors.append("Plugin name is required")
        if not issubclass(self.node_class, FluxNode):
            errors.append("node_class must subclass FluxNode")
        if not hasattr(self.node_class, "execute"):
            errors.append("node_class must implement execute()")
        if not self.node_class.node_type or self.node_class.node_type == "base":
            errors.append("node_class must set node_type class attribute")
        return errors

    def info(self) -> str:
        return (
            f"Plugin: {self.name} v{self.version}\n"
            f"  Node type: {self.node_class.node_type}\n"
            f"  Description: {self.description}\n"
            f"  Author: {self.author}\n"
            f"  Tags: {', '.join(self.tags) or 'none'}"
        )


class PluginRegistry:
    """
    Manages loaded plugins. PLASMA uses this to spawn plugin nodes.

    Usage:
        from plugin_base import plugin_registry
        plugin_registry.load("skynet")
        node = plugin_registry.create_node("skynet")
        await node.start()
    """

    def __init__(self):
        self._plugins: dict[str, PhasePlugin] = {}

    def register(self, plugin: PhasePlugin) -> bool:
        """Manually register a plugin (for testing or dynamic loading)."""
        errors = plugin.validate()
        if errors:
            logger.error("plugin: %s validation failed: %s", plugin.name, errors)
            return False
        self._plugins[plugin.name] = plugin
        logger.info("plugin: registered '%s' v%s", plugin.name, plugin.version)
        return True

    def load(self, plugin_name: str) -> bool:
        """
        Load a plugin from the plugins/ directory.
        The plugin directory must contain __init__.py with a PLUGIN = PhasePlugin(...).
        """
        plugin_path = PLUGINS_DIR / plugin_name / "__init__.py"
        if not plugin_path.exists():
            logger.error("plugin: '%s' not found at %s", plugin_name, plugin_path)
            return False

        try:
            spec   = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, "PLUGIN"):
                logger.error("plugin: '%s' has no PLUGIN descriptor", plugin_name)
                return False

            return self.register(module.PLUGIN)

        except Exception as exc:
            logger.error("plugin: failed to load '%s': %s", plugin_name, exc)
            return False

    def load_all(self) -> int:
        """Load all plugins found in the plugins/ directory."""
        if not PLUGINS_DIR.exists():
            return 0
        count = 0
        for entry in PLUGINS_DIR.iterdir():
            if entry.is_dir() and (entry / "__init__.py").exists():
                if self.load(entry.name):
                    count += 1
        return count

    def create_node(self, plugin_name: str) -> Optional[FluxNode]:
        """Create a new instance of a plugin's node class."""
        plugin = self._plugins.get(plugin_name)
        if not plugin:
            logger.error("plugin: '%s' not loaded", plugin_name)
            return None
        return plugin.node_class()

    def list_plugins(self) -> list[PhasePlugin]:
        return list(self._plugins.values())

    def get(self, name: str) -> Optional[PhasePlugin]:
        return self._plugins.get(name)

    def is_loaded(self, name: str) -> bool:
        return name in self._plugins

    def summary(self) -> str:
        if not self._plugins:
            return "No plugins loaded."
        lines = [f"Loaded plugins ({len(self._plugins)}):"]
        for p in self._plugins.values():
            lines.append(f"  · {p.name} v{p.version} — {p.description}")
        return "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────
plugin_registry = PluginRegistry()


# ─────────────────────────────────────────────────────────────────────────────
# PLUGIN TEMPLATE (copy this to create a new plugin)
# Save as:  plugins/your_plugin_name/__init__.py
# ─────────────────────────────────────────────────────────────────────────────

PLUGIN_TEMPLATE = '''\
"""
plugins/YOUR_PLUGIN_NAME/__init__.py

PHASE Plugin: YOUR PLUGIN NAME
Description: What this plugin does
Author: Your name
Version: 1.0.0
"""

from flux_base import FluxNode
from task import Task
from plugin_base import PhasePlugin


class YourNode(FluxNode):
    """Your custom FLUX node."""

    node_type     = "your_node_type"      # must be unique across all nodes
    system_prompt = """
You are the YourNode FLUX node in the PHASE multi-agent system.
Describe your role here. Be specific about what you do and how.
"""

    async def execute(self, task: Task) -> str:
        """
        Implement your node\'s logic here.
        task.goal      — what PLASMA wants you to do
        task.context   — extra metadata including SOLID feedback on retries
        Returns the result as a string. Return "" on failure.
        """
        feedback = task.context.get("solid_feedback", "")
        feedback_block = (
            f"\\n\\nPREVIOUS ATTEMPT REJECTED. Fix this:\\n{feedback}\\n"
            if feedback else ""
        )

        return await self.llm(
            user_message = task.goal + feedback_block,
            max_tokens   = 800,
            temperature  = 0.7,
        )


# Required: PHASE discovers your plugin via this descriptor
PLUGIN = PhasePlugin(
    name        = "your_plugin_name",
    version     = "1.0.0",
    description = "Short description of what this plugin does",
    node_class  = YourNode,
    author      = "Your Name",
    requires    = [],   # names of other plugins this depends on
    tags        = ["category", "subcategory"],
)
'''
