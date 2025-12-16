"""
Linux Command Quest - Command System Base
==========================================

Plugin-style command architecture allowing easy addition of new commands.
Each command is a class with execute(), autocomplete(), and help methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..simulation.filesystem import VirtualFileSystem


@dataclass
class CommandResult:
    """Result of command execution."""
    
    success: bool
    output: str = ""
    error: str = ""
    clear_screen: bool = False
    exit_game: bool = False
    
    @classmethod
    def ok(cls, output: str = "") -> CommandResult:
        """Shortcut for successful result."""
        return cls(success=True, output=output)
    
    @classmethod
    def fail(cls, error: str) -> CommandResult:
        """Shortcut for failure result."""
        return cls(success=False, error=error)
    
    @classmethod
    def clear(cls) -> CommandResult:
        """Shortcut for clear screen result."""
        return cls(success=True, clear_screen=True)


class BaseCommand(ABC):
    """
    Abstract base class for all commands.
    
    To create a new command:
    
    1. Create a class inheriting from BaseCommand
    2. Set name, aliases, help_short, help_long, usage
    3. Implement execute() method
    4. Register with CommandRegistry
    
    Example:
        class PwdCommand(BaseCommand):
            name = "pwd"
            help_short = "Print working directory"
            
            def execute(self, args: list[str]) -> CommandResult:
                return CommandResult.ok(self.fs.cwd)
    """
    
    name: str = ""
    aliases: list[str] = []
    help_short: str = ""
    help_long: str = ""
    usage: str = ""
    min_args: int = 0
    max_args: int | None = None
    
    def __init__(self, fs: VirtualFileSystem, shell: "Shell"):
        self.fs = fs
        self.shell = shell
    
    @abstractmethod
    def execute(self, args: list[str]) -> CommandResult:
        """
        Execute the command with given arguments.
        
        Args:
            args: List of command arguments (without command name)
            
        Returns:
            CommandResult with output or error
        """
        pass
    
    def validate_args(self, args: list[str]) -> str | None:
        """
        Validate argument count.
        
        Returns error message if invalid, None if valid.
        """
        if len(args) < self.min_args:
            return f"{self.name}: missing operand"
        
        if self.max_args is not None and len(args) > self.max_args:
            return f"{self.name}: too many arguments"
        
        return None
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        """
        Provide tab completion suggestions.
        
        Args:
            partial: Partial text being completed
            args: Arguments entered so far
            
        Returns:
            List of completion suggestions
        """
        # Default: complete file/directory names
        return self._complete_path(partial)
    
    def _complete_path(self, partial: str) -> list[str]:
        """Complete file/directory path."""
        if not partial:
            # List current directory
            try:
                items = self.fs.ls(show_hidden=partial.startswith("."))
                return [name + ("/" if is_dir else "") for name, is_dir in items]
            except Exception:
                return []
        
        # Determine directory and prefix
        if "/" in partial:
            dir_path = partial.rsplit("/", 1)[0] or "/"
            prefix = partial.rsplit("/", 1)[1]
        else:
            dir_path = "."
            prefix = partial
        
        try:
            items = self.fs.ls(dir_path, show_hidden=prefix.startswith("."))
            matches = []
            for name, is_dir in items:
                if name.startswith(prefix):
                    if dir_path == ".":
                        matches.append(name + ("/" if is_dir else ""))
                    else:
                        matches.append(f"{dir_path}/{name}" + ("/" if is_dir else ""))
            return matches
        except Exception:
            return []
    
    def get_help(self) -> str:
        """Get full help text for command."""
        lines = []
        
        if self.help_long:
            lines.append(self.help_long)
        else:
            lines.append(self.help_short)
        
        if self.usage:
            lines.append("")
            lines.append(f"Kullanım: {self.usage}")
        
        if self.aliases:
            lines.append("")
            lines.append(f"Takma adlar: {', '.join(self.aliases)}")
        
        return "\n".join(lines)


class CommandRegistry:
    """
    Registry for all available commands.
    
    Usage:
        registry = CommandRegistry()
        registry.register(PwdCommand)
        registry.register(LsCommand)
        
        cmd_class = registry.get("ls")
        if cmd_class:
            cmd = cmd_class(fs, shell)
            result = cmd.execute(["--all"])
    """
    
    def __init__(self):
        self._commands: dict[str, type[BaseCommand]] = {}
        self._aliases: dict[str, str] = {}  # alias -> real name
    
    def register(self, cmd_class: type[BaseCommand]):
        """Register a command class."""
        name = cmd_class.name
        if not name:
            raise ValueError(f"Command class {cmd_class} has no name")
        
        self._commands[name] = cmd_class
        
        # Register aliases
        for alias in getattr(cmd_class, 'aliases', []):
            self._aliases[alias] = name
    
    def get(self, name: str) -> type[BaseCommand] | None:
        """Get command class by name or alias."""
        # Check aliases first
        if name in self._aliases:
            name = self._aliases[name]
        
        return self._commands.get(name)
    
    def all_commands(self) -> list[type[BaseCommand]]:
        """Get all registered command classes."""
        return list(self._commands.values())
    
    def all_names(self) -> list[str]:
        """Get all command names and aliases."""
        names = list(self._commands.keys())
        names.extend(self._aliases.keys())
        return sorted(set(names))
    
    def get_help_table(self) -> list[tuple[str, str]]:
        """Get (name, description) pairs for all commands."""
        result = []
        for cmd_class in self._commands.values():
            result.append((cmd_class.name, cmd_class.help_short))
        return sorted(result, key=lambda x: x[0])


# Global registry instance
_registry = CommandRegistry()


def register_command(cmd_class: type[BaseCommand]) -> type[BaseCommand]:
    """Decorator to register a command class."""
    _registry.register(cmd_class)
    return cmd_class


def get_registry() -> CommandRegistry:
    """Get the global command registry."""
    return _registry
