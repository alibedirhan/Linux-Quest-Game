"""
Command implementations.

All commands are automatically registered when this module is imported.
"""

from .base import BaseCommand, CommandResult, CommandRegistry, get_registry, register_command

# Import all command modules to trigger registration
from . import navigation
from . import files
from . import text
from . import system

__all__ = [
    "BaseCommand", "CommandResult", "CommandRegistry", 
    "get_registry", "register_command",
]
