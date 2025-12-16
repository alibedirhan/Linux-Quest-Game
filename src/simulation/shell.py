"""
Linux Command Quest - Shell
============================

Command interpreter with support for pipes, redirects, and command parsing.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .commands.base import CommandResult, get_registry

if TYPE_CHECKING:
    from .filesystem import VirtualFileSystem


@dataclass
class ParsedCommand:
    """Represents a parsed command with arguments."""
    
    name: str
    args: list[str]
    stdin: str | None = None
    stdout_file: str | None = None
    stdout_append: bool = False
    stderr_file: str | None = None
    pipe_to: "ParsedCommand | None" = None


class Shell:
    """
    Command interpreter with history, pipes, and redirects.
    
    Features:
    - Command parsing with shlex
    - Command history
    - Pipe support (|)
    - Redirect support (>, >>)
    - Tab completion
    
    Usage:
        shell = Shell(filesystem)
        result = shell.execute("ls -la | grep txt")
        print(result.output)
    """
    
    def __init__(self, fs: VirtualFileSystem):
        self.fs = fs
        self.history: list[str] = []
        self.history_max = 100
        self._registry = get_registry()
    
    def execute(self, command_line: str) -> CommandResult:
        """
        Execute a command line.
        
        Args:
            command_line: Raw command string from user
            
        Returns:
            CommandResult with output or error
        """
        command_line = command_line.strip()
        
        if not command_line:
            return CommandResult.ok()
        
        # Add to history
        self._add_history(command_line)
        
        # Parse command line
        try:
            parsed = self._parse(command_line)
        except ValueError as e:
            return CommandResult.fail(f"bash: sözdizimi hatası: {e}")
        
        # Execute
        return self._execute_parsed(parsed)
    
    def _add_history(self, cmd: str):
        """Add command to history."""
        # Don't add duplicates of last command
        if self.history and self.history[-1] == cmd:
            return
        
        self.history.append(cmd)
        
        # Limit size
        if len(self.history) > self.history_max:
            self.history.pop(0)
    
    def get_history(self) -> list[str]:
        """Get command history."""
        return self.history.copy()
    
    def _parse(self, command_line: str) -> ParsedCommand:
        """
        Parse a command line into structured form.
        
        Handles:
        - Simple commands: ls -la
        - Pipes: ls | grep txt
        - Redirects: echo hello > file.txt
        - Append redirects: echo world >> file.txt
        """
        # Handle pipes first
        if "|" in command_line:
            parts = command_line.split("|", 1)
            left = self._parse(parts[0].strip())
            right = self._parse(parts[1].strip())
            left.pipe_to = right
            return left
        
        # Handle redirects
        stdout_file = None
        stdout_append = False
        
        if ">>" in command_line:
            parts = command_line.split(">>", 1)
            command_line = parts[0].strip()
            stdout_file = parts[1].strip()
            stdout_append = True
        elif ">" in command_line:
            parts = command_line.split(">", 1)
            command_line = parts[0].strip()
            stdout_file = parts[1].strip()
        
        # Parse command and arguments
        try:
            tokens = shlex.split(command_line)
        except ValueError as e:
            raise ValueError(str(e))
        
        if not tokens:
            return ParsedCommand(name="", args=[])
        
        return ParsedCommand(
            name=tokens[0],
            args=tokens[1:],
            stdout_file=stdout_file,
            stdout_append=stdout_append,
        )
    
    def _execute_parsed(self, parsed: ParsedCommand, stdin: str = "") -> CommandResult:
        """Execute a parsed command."""
        
        if not parsed.name:
            return CommandResult.ok()
        
        # Get command class
        cmd_class = self._registry.get(parsed.name)
        
        if cmd_class is None:
            return CommandResult.fail(f"bash: {parsed.name}: komut bulunamadı")
        
        # Create command instance
        cmd = cmd_class(self.fs, self)
        
        # Validate arguments
        error = cmd.validate_args(parsed.args)
        if error:
            return CommandResult.fail(error)
        
        # Execute command
        try:
            result = cmd.execute(parsed.args)
        except Exception as e:
            return CommandResult.fail(f"{parsed.name}: {e}")
        
        # Handle pipe
        if parsed.pipe_to and result.success:
            # Pass output to next command
            # For simplicity, we just filter output through next command
            # Real pipes would be more complex
            pipe_result = self._execute_parsed(parsed.pipe_to, result.output)
            return pipe_result
        
        # Handle redirect
        if parsed.stdout_file and result.success:
            try:
                self.fs.write(
                    parsed.stdout_file,
                    result.output + "\n",
                    append=parsed.stdout_append
                )
                return CommandResult.ok()  # Output goes to file, not screen
            except Exception as e:
                return CommandResult.fail(f"bash: {parsed.stdout_file}: {e}")
        
        return result
    
    def complete(self, partial_line: str) -> list[str]:
        """
        Provide tab completion suggestions.
        
        Args:
            partial_line: Partial command line
            
        Returns:
            List of completion suggestions
        """
        if not partial_line:
            # Return all commands
            return self._registry.all_names()
        
        parts = partial_line.split()
        
        if len(parts) == 1 and not partial_line.endswith(" "):
            # Completing command name
            prefix = parts[0]
            return [name for name in self._registry.all_names() 
                    if name.startswith(prefix)]
        
        # Completing arguments
        cmd_name = parts[0]
        cmd_class = self._registry.get(cmd_name)
        
        if cmd_class is None:
            return []
        
        # Get partial argument
        if partial_line.endswith(" "):
            partial_arg = ""
            args = parts[1:]
        else:
            partial_arg = parts[-1]
            args = parts[1:-1]
        
        # Create command instance for completion
        cmd = cmd_class(self.fs, self)
        return cmd.autocomplete(partial_arg, args)
    
    def get_prompt(self) -> str:
        """Get shell prompt string."""
        path = self.fs.get_prompt_path()
        return f"\033[32m{self.fs.username}\033[0m@\033[36m{self.fs.hostname}\033[0m:\033[34m{path}\033[0m$ "
    
    def get_prompt_plain(self) -> str:
        """Get prompt without colors (for width calculation)."""
        path = self.fs.get_prompt_path()
        return f"{self.fs.username}@{self.fs.hostname}:{path}$ "
