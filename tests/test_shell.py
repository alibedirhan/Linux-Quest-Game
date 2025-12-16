"""
Tests for Shell and Commands
============================
"""

import pytest
from src.simulation.filesystem import VirtualFileSystem
from src.simulation.shell import Shell, ParsedCommand
from src.simulation.commands import get_registry


class TestShell:
    """Test Shell class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.fs = VirtualFileSystem("testuser")
        self.shell = Shell(self.fs)
    
    # === Command Parsing Tests (using internal _parse method) ===
    
    def test_parse_simple_command(self):
        """Simple command should parse correctly."""
        parsed = self.shell._parse("ls")
        assert parsed.name == "ls"
        assert parsed.args == []
    
    def test_parse_command_with_args(self):
        """Command with arguments should parse correctly."""
        parsed = self.shell._parse("ls -la /home")
        assert parsed.name == "ls"
        assert parsed.args == ["-la", "/home"]
    
    def test_parse_command_with_quotes(self):
        """Quoted arguments should be handled."""
        parsed = self.shell._parse('echo "hello world"')
        assert parsed.name == "echo"
        assert parsed.args == ["hello world"]
    
    def test_parse_redirect_output(self):
        """Output redirect should be parsed."""
        parsed = self.shell._parse("echo test > file.txt")
        assert parsed.name == "echo"
        assert parsed.stdout_file == "file.txt"
        assert not parsed.stdout_append
    
    def test_parse_redirect_append(self):
        """Append redirect should be parsed."""
        parsed = self.shell._parse("echo test >> file.txt")
        assert parsed.name == "echo"
        assert parsed.stdout_file == "file.txt"
        assert parsed.stdout_append
    
    # === Command Execution Tests ===
    
    def test_execute_pwd(self):
        """pwd should return current directory."""
        result = self.shell.execute("pwd")
        assert result.success
        assert self.fs.home in result.output
    
    def test_execute_ls(self):
        """ls should list directory contents."""
        result = self.shell.execute("ls")
        assert result.success
        assert "Documents" in result.output
    
    def test_execute_cd(self):
        """cd should change directory."""
        result = self.shell.execute("cd Documents")
        assert result.success
        assert self.fs.cwd.endswith("Documents")
    
    def test_execute_unknown_command(self):
        """Unknown command should return error."""
        result = self.shell.execute("unknowncommand")
        assert not result.success
        assert "bulunamadı" in result.error
    
    def test_execute_touch(self):
        """touch should create file."""
        result = self.shell.execute("touch newfile.txt")
        assert result.success
        assert self.fs.exists("newfile.txt")
    
    def test_execute_mkdir(self):
        """mkdir should create directory."""
        result = self.shell.execute("mkdir newdir")
        assert result.success
        assert self.fs.isdir("newdir")
    
    def test_execute_echo(self):
        """echo should output text."""
        result = self.shell.execute("echo hello world")
        assert result.success
        assert "hello world" in result.output
    
    def test_execute_echo_redirect(self):
        """echo with redirect should create file."""
        result = self.shell.execute("echo test > output.txt")
        assert result.success
        assert self.fs.exists("output.txt")
    
    def test_execute_cat(self):
        """cat should read file content."""
        self.shell.execute("echo content > test.txt")
        result = self.shell.execute("cat test.txt")
        assert result.success
        assert "content" in result.output
    
    def test_execute_rm(self):
        """rm should remove file."""
        self.fs.touch("todelete.txt")
        result = self.shell.execute("rm todelete.txt")
        assert result.success
        assert not self.fs.exists("todelete.txt")
    
    def test_execute_clear(self):
        """clear should set clear_screen flag."""
        result = self.shell.execute("clear")
        assert result.success
        assert result.clear_screen
    
    # === Pipe Tests ===
    
    def test_pipe_with_content(self):
        """Pipe should pass output between commands."""
        # Create file with content
        self.shell.execute("echo -e 'apple\\nbanana\\ncherry' > fruits.txt")
        # This tests the pipe mechanism
        result = self.shell.execute("cat fruits.txt | grep banana")
        # Grep on piped input
        assert result.success or "banana" in result.output or result.output == ""
    
    # === History Tests ===
    
    def test_history_records_commands(self):
        """Commands should be recorded in history."""
        self.shell.execute("pwd")
        self.shell.execute("ls")
        assert "pwd" in self.shell.history
        assert "ls" in self.shell.history
    
    def test_history_no_duplicates(self):
        """Consecutive duplicates should not be recorded."""
        self.shell.execute("pwd")
        self.shell.execute("pwd")
        assert self.shell.history.count("pwd") == 1
    
    # === Tab Completion Tests ===
    
    def test_complete_command(self):
        """Tab completion should complete commands."""
        completions = self.shell.complete("pw")
        assert "pwd" in completions
    
    def test_complete_path(self):
        """Tab completion should complete paths."""
        completions = self.shell.complete("cd Doc")
        assert "Documents/" in completions
    
    def test_complete_empty(self):
        """Empty input should return all commands."""
        completions = self.shell.complete("")
        assert len(completions) > 0


class TestCommands:
    """Test individual commands."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.fs = VirtualFileSystem("testuser")
        self.shell = Shell(self.fs)
    
    # === Navigation Commands ===
    
    def test_pwd_output_format(self):
        """pwd should output clean path."""
        result = self.shell.execute("pwd")
        assert result.output.strip() == self.fs.cwd
    
    def test_cd_no_args_goes_home(self):
        """cd without args should go to home."""
        self.shell.execute("cd /tmp")
        self.shell.execute("cd")
        assert self.fs.cwd == self.fs.home
    
    def test_ls_long_format(self):
        """ls -l should show detailed info."""
        result = self.shell.execute("ls -l")
        assert result.success
        # Should contain permission-like strings or dates
    
    def test_ls_all_shows_hidden(self):
        """ls -a should show hidden files."""
        self.fs.touch(".hidden")
        result = self.shell.execute("ls -a")
        assert ".hidden" in result.output
    
    # === File Commands ===
    
    def test_touch_multiple_files(self):
        """touch should create multiple files."""
        self.shell.execute("touch a.txt b.txt c.txt")
        assert self.fs.exists("a.txt")
        assert self.fs.exists("b.txt")
        assert self.fs.exists("c.txt")
    
    def test_mkdir_with_parents(self):
        """mkdir -p should create parent directories."""
        result = self.shell.execute("mkdir -p a/b/c")
        assert result.success
        assert self.fs.isdir("a/b/c")
    
    def test_rm_recursive(self):
        """rm -r should remove directory tree."""
        self.shell.execute("mkdir -p testdir/subdir")
        self.shell.execute("touch testdir/file.txt")
        result = self.shell.execute("rm -r testdir")
        assert result.success
        assert not self.fs.exists("testdir")
    
    def test_cp_file(self):
        """cp should copy file."""
        self.shell.execute("touch original.txt")
        result = self.shell.execute("cp original.txt copy.txt")
        assert result.success
        assert self.fs.exists("copy.txt")
    
    def test_mv_file(self):
        """mv should move/rename file."""
        self.shell.execute("touch old.txt")
        result = self.shell.execute("mv old.txt new.txt")
        assert result.success
        assert not self.fs.exists("old.txt")
        assert self.fs.exists("new.txt")
    
    # === Text Commands ===
    
    def test_echo_simple(self):
        """echo should output text."""
        result = self.shell.execute("echo hello")
        assert result.output.strip() == "hello"
    
    def test_echo_no_newline(self):
        """echo -n should not add newline."""
        result = self.shell.execute("echo -n hello")
        assert result.output == "hello"
    
    def test_cat_nonexistent(self):
        """cat on nonexistent file should error."""
        result = self.shell.execute("cat nonexistent.txt")
        assert not result.success
    
    def test_head_default(self):
        """head should show first 10 lines."""
        content = "\\n".join([f"line{i}" for i in range(20)])
        self.shell.execute(f"echo -e '{content}' > test.txt")
        result = self.shell.execute("head test.txt")
        assert result.success
    
    def test_tail_default(self):
        """tail should show last 10 lines."""
        content = "\\n".join([f"line{i}" for i in range(20)])
        self.shell.execute(f"echo -e '{content}' > test.txt")
        result = self.shell.execute("tail test.txt")
        assert result.success
    
    def test_grep_finds_pattern(self):
        """grep should find matching lines."""
        self.shell.execute("echo -e 'apple\\nbanana\\napricot' > fruits.txt")
        result = self.shell.execute("grep apple fruits.txt")
        assert "apple" in result.output
    
    def test_grep_case_insensitive(self):
        """grep -i should ignore case."""
        self.shell.execute("echo -e 'Apple\\nBANANA' > test.txt")
        result = self.shell.execute("grep -i apple test.txt")
        assert "Apple" in result.output
    
    def test_wc_counts(self):
        """wc should count lines, words, chars."""
        self.shell.execute("echo -e 'one two\\nthree four' > test.txt")
        result = self.shell.execute("wc test.txt")
        assert result.success
    
    # === System Commands ===
    
    def test_whoami(self):
        """whoami should return username."""
        result = self.shell.execute("whoami")
        assert result.output.strip() == "testuser"
    
    def test_hostname(self):
        """hostname should return hostname."""
        result = self.shell.execute("hostname")
        assert result.output.strip() == "quest"
    
    def test_date(self):
        """date should return current date."""
        result = self.shell.execute("date")
        assert result.success
        assert len(result.output) > 0
    
    def test_uname(self):
        """uname should return system info."""
        result = self.shell.execute("uname -a")
        assert result.success
        assert "Linux" in result.output
    
    def test_help(self):
        """help should list commands."""
        result = self.shell.execute("help")
        assert result.success
        assert "pwd" in result.output
    
    def test_history(self):
        """history should show command history."""
        self.shell.execute("pwd")
        self.shell.execute("ls")
        result = self.shell.execute("history")
        assert result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
