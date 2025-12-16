"""
Linux Command Quest - Virtual Filesystem
=========================================

In-memory filesystem simulation that mimics real Linux filesystem behavior.
Safe sandbox environment where even `rm -rf /` can be executed safely.
"""

from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Flag, auto
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from typing import Any


class Permission(Flag):
    """Unix-style file permissions."""
    
    NONE = 0
    X_OTHER = auto()  # 1
    W_OTHER = auto()  # 2
    R_OTHER = auto()  # 4
    X_GROUP = auto()  # 8
    W_GROUP = auto()  # 16
    R_GROUP = auto()  # 32
    X_USER = auto()   # 64
    W_USER = auto()   # 128
    R_USER = auto()   # 256
    
    # Common combinations
    @classmethod
    def from_octal(cls, octal: int) -> Permission:
        """Create permission from octal (e.g., 755)."""
        result = cls.NONE
        
        # User (hundreds)
        u = (octal // 100) % 10
        if u & 4: result |= cls.R_USER
        if u & 2: result |= cls.W_USER
        if u & 1: result |= cls.X_USER
        
        # Group (tens)
        g = (octal // 10) % 10
        if g & 4: result |= cls.R_GROUP
        if g & 2: result |= cls.W_GROUP
        if g & 1: result |= cls.X_GROUP
        
        # Other (ones)
        o = octal % 10
        if o & 4: result |= cls.R_OTHER
        if o & 2: result |= cls.W_OTHER
        if o & 1: result |= cls.X_OTHER
        
        return result
    
    def to_octal(self) -> int:
        """Convert to octal representation."""
        result = 0
        
        if Permission.R_USER in self: result += 400
        if Permission.W_USER in self: result += 200
        if Permission.X_USER in self: result += 100
        if Permission.R_GROUP in self: result += 40
        if Permission.W_GROUP in self: result += 20
        if Permission.X_GROUP in self: result += 10
        if Permission.R_OTHER in self: result += 4
        if Permission.W_OTHER in self: result += 2
        if Permission.X_OTHER in self: result += 1
        
        return result
    
    def to_string(self) -> str:
        """Convert to ls -l style string (e.g., rwxr-xr-x)."""
        s = ""
        s += "r" if Permission.R_USER in self else "-"
        s += "w" if Permission.W_USER in self else "-"
        s += "x" if Permission.X_USER in self else "-"
        s += "r" if Permission.R_GROUP in self else "-"
        s += "w" if Permission.W_GROUP in self else "-"
        s += "x" if Permission.X_GROUP in self else "-"
        s += "r" if Permission.R_OTHER in self else "-"
        s += "w" if Permission.W_OTHER in self else "-"
        s += "x" if Permission.X_OTHER in self else "-"
        return s


# Common permission presets
PERM_FILE = Permission.from_octal(644)      # rw-r--r--
PERM_DIR = Permission.from_octal(755)       # rwxr-xr-x
PERM_EXEC = Permission.from_octal(755)      # rwxr-xr-x
PERM_PRIVATE = Permission.from_octal(600)   # rw-------


@dataclass
class FileNode:
    """Represents a file or directory in the virtual filesystem."""
    
    name: str
    is_dir: bool = False
    content: str = ""
    children: dict[str, FileNode] = field(default_factory=dict)
    permissions: Permission = field(default_factory=lambda: PERM_FILE)
    owner: str = "user"
    group: str = "user"
    size: int = 0
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.is_dir and self.permissions == PERM_FILE:
            self.permissions = PERM_DIR
        if not self.is_dir:
            self.size = len(self.content.encode('utf-8'))
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "is_dir": self.is_dir,
            "content": self.content if not self.is_dir else "",
            "children": {k: v.to_dict() for k, v in self.children.items()},
            "permissions": self.permissions.to_octal(),
            "owner": self.owner,
            "group": self.group,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> FileNode:
        """Deserialize from dictionary."""
        node = cls(
            name=data["name"],
            is_dir=data["is_dir"],
            content=data.get("content", ""),
            permissions=Permission.from_octal(data.get("permissions", 644)),
            owner=data.get("owner", "user"),
            group=data.get("group", "user"),
        )
        for name, child_data in data.get("children", {}).items():
            node.children[name] = cls.from_dict(child_data)
        return node


class FileSystemError(Exception):
    """Base exception for filesystem errors."""
    pass


class PathNotFoundError(FileSystemError):
    """Path does not exist."""
    pass


class NotADirectoryError(FileSystemError):
    """Expected directory but found file."""
    pass


class IsADirectoryError(FileSystemError):
    """Expected file but found directory."""
    pass


class FileExistsError(FileSystemError):
    """File already exists."""
    pass


class PermissionError(FileSystemError):
    """Permission denied."""
    pass


class VirtualFileSystem:
    """
    In-memory virtual filesystem.
    
    Features:
    - Full path resolution (., .., ~, absolute, relative)
    - Directory operations (mkdir, rmdir)
    - File operations (touch, rm, cat, write)
    - Permission system
    - Checkpoint/restore for mission reset
    
    Usage:
        fs = VirtualFileSystem("user")
        fs.mkdir("/home/user/test")
        fs.touch("/home/user/test/file.txt")
        fs.write("/home/user/test/file.txt", "Hello World")
        print(fs.cat("/home/user/test/file.txt"))
    """
    
    def __init__(self, username: str = "user"):
        self.username = username
        self.hostname = "quest"
        self.home = f"/home/{username}"
        self.cwd = self.home
        self._prev_cwd = self.home  # For cd - support
        
        # Root of filesystem
        self.root = FileNode(name="/", is_dir=True)
        
        # Build default structure
        self._init_default_structure()
        
        # Checkpoint for restore
        self._checkpoint: FileNode | None = None
    
    def _init_default_structure(self):
        """Create default Linux-like directory structure."""
        
        # System directories
        system_dirs = [
            "/bin", "/boot", "/dev", "/etc", "/lib", "/lib64",
            "/media", "/mnt", "/opt", "/proc", "/root", "/run",
            "/sbin", "/srv", "/sys", "/tmp", "/usr", "/var",
            "/usr/bin", "/usr/lib", "/usr/local", "/usr/share",
            "/var/log", "/var/tmp", "/var/cache",
        ]
        
        for path in system_dirs:
            self._ensure_path(path, is_dir=True)
        
        # User home
        home = self.home
        user_dirs = [
            f"{home}/Documents",
            f"{home}/Downloads", 
            f"{home}/Music",
            f"{home}/Pictures",
            f"{home}/Videos",
            f"{home}/Desktop",
            f"{home}/.config",
            f"{home}/.local/share",
        ]
        
        for path in user_dirs:
            self._ensure_path(path, is_dir=True)
        
        # Default files with content
        default_files = {
            f"{home}/.bashrc": self._get_bashrc_content(),
            f"{home}/.profile": self._get_profile_content(),
            f"{home}/Documents/notes.txt": "# Notlarım\n\nBu dosya örnek bir metin dosyasıdır.\nLinux öğrenmeye hoş geldin!\n",
            f"{home}/Documents/code.py": '#!/usr/bin/env python3\n\nprint("Merhaba Linux!")\n',
            "/etc/passwd": self._get_passwd_content(),
            "/etc/shadow": self._get_shadow_content(),
            "/etc/hosts": self._get_hosts_content(),
            "/etc/hostname": f"{self.hostname}\n",
            "/etc/os-release": self._get_os_release_content(),
            "/var/log/syslog": self._get_syslog_content(),
            "/var/log/auth.log": self._get_authlog_content(),
            "/tmp/test.txt": "Bu geçici bir dosyadır.\n",
        }
        
        for path, content in default_files.items():
            self._ensure_path(path, is_dir=False, content=content)
    
    def _get_bashrc_content(self) -> str:
        return f"""# ~/.bashrc: executed by bash for non-login shells.

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# History settings
HISTCONTROL=ignoreboth
HISTSIZE=1000
HISTFILESIZE=2000

# Prompt
PS1='\\u@\\h:\\w\\$ '

# Aliases
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Enable color support
alias ls='ls --color=auto'
alias grep='grep --color=auto'

export PATH="$HOME/.local/bin:$PATH"
"""
    
    def _get_profile_content(self) -> str:
        return """# ~/.profile: executed by the command interpreter for login shells.

if [ -n "$BASH_VERSION" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi

export EDITOR=nano
export LANG=tr_TR.UTF-8
"""
    
    def _get_passwd_content(self) -> str:
        return f"""root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
{self.username}:x:1000:1000:{self.username}:/home/{self.username}:/bin/bash
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
"""
    
    def _get_hosts_content(self) -> str:
        return f"""127.0.0.1       localhost
127.0.1.1       {self.hostname}
::1             localhost ip6-localhost ip6-loopback
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters
"""
    
    def _get_os_release_content(self) -> str:
        return """PRETTY_NAME="Linux Command Quest OS"
NAME="LinuxQuest"
VERSION_ID="2.0"
VERSION="2.0 (Educational)"
ID=linuxquest
HOME_URL="https://youtube.com/@ali_bedirhan"
SUPPORT_URL="https://github.com/alibedirhan/linux-command-quest"
"""
    
    def _get_syslog_content(self) -> str:
        return """Dec 15 10:00:01 quest systemd[1]: Started Daily apt download activities.
Dec 15 10:00:02 quest systemd[1]: Starting Linux Command Quest...
Dec 15 10:00:03 quest kernel: [    0.000000] Linux version 6.1.0-quest
Dec 15 10:00:04 quest quest[1234]: Session started for user
Dec 15 10:00:05 quest quest[1234]: Virtual filesystem initialized
Dec 15 10:00:06 quest quest[1234]: Ready for commands
"""
    
    def _get_authlog_content(self) -> str:
        return """Dec 15 08:23:01 quest sshd[1001]: Accepted password for user from 192.168.1.100 port 52341
Dec 15 08:45:12 quest sshd[1002]: Failed password for root from 10.0.0.50 port 43210
Dec 15 08:45:14 quest sshd[1002]: Failed password for root from 10.0.0.50 port 43210
Dec 15 08:45:16 quest sshd[1002]: Failed password for root from 10.0.0.50 port 43210
Dec 15 08:45:18 quest sshd[1002]: Failed password for root from 10.0.0.50 port 43210
Dec 15 09:00:00 quest CRON[1100]: pam_unix(cron:session): session opened for user root
Dec 15 09:15:22 quest sudo[1150]: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/ls
Dec 15 09:30:45 quest sshd[1200]: Accepted publickey for admin from 192.168.1.50 port 22
Dec 15 10:00:01 quest sshd[1250]: Failed password for admin from 203.0.113.100 port 55555
Dec 15 10:00:03 quest sshd[1250]: Failed password for admin from 203.0.113.100 port 55555
Dec 15 10:15:30 quest sshd[1300]: Invalid user hacker from 185.220.101.1 port 12345
Dec 15 10:15:32 quest sshd[1300]: Failed password for invalid user hacker from 185.220.101.1
Dec 15 10:30:00 quest systemd-logind[500]: New session 5 of user user.
Dec 15 11:00:00 quest sshd[1400]: Accepted password for user from 192.168.1.105 port 60000
"""
    
    def _get_shadow_content(self) -> str:
        # Shadow file - permission denied simulation
        return "cat: /etc/shadow: Permission denied\n"
    
    def _ensure_path(self, path: str, is_dir: bool, content: str = ""):
        """Ensure path exists, creating parent directories as needed."""
        parts = self._split_path(path)
        current = self.root
        
        for i, part in enumerate(parts):
            if part not in current.children:
                # Last part?
                if i == len(parts) - 1:
                    current.children[part] = FileNode(
                        name=part,
                        is_dir=is_dir,
                        content=content,
                        owner=self.username,
                        group=self.username,
                    )
                else:
                    # Intermediate directory
                    current.children[part] = FileNode(
                        name=part,
                        is_dir=True,
                        owner="root" if path.startswith("/etc") or path.startswith("/var") else self.username,
                        group="root" if path.startswith("/etc") or path.startswith("/var") else self.username,
                    )
            current = current.children[part]
    
    def _split_path(self, path: str) -> list[str]:
        """Split path into components."""
        path = path.strip()
        if not path or path == "/":
            return []
        
        # Remove leading/trailing slashes and split
        parts = [p for p in path.strip("/").split("/") if p]
        return parts
    
    def resolve(self, path: str) -> str:
        """
        Resolve a path to absolute form.
        
        Handles: ~, ., .., relative paths, absolute paths, $HOME, $USER
        """
        if not path:
            return self.cwd
        
        # Environment variable expansion
        path = path.replace("$HOME", self.home)
        path = path.replace("$USER", self.username)
        path = path.replace("${HOME}", self.home)
        path = path.replace("${USER}", self.username)
        
        # Home directory
        if path == "~":
            return self.home
        if path.startswith("~/"):
            path = self.home + path[1:]
        
        # Absolute vs relative
        if not path.startswith("/"):
            path = self.cwd + "/" + path
        
        # Manually resolve . and ..
        parts = path.split("/")
        resolved = []
        
        for part in parts:
            if part == "" or part == ".":
                continue
            elif part == "..":
                if resolved:
                    resolved.pop()
            else:
                resolved.append(part)
        
        normalized = "/" + "/".join(resolved)
        
        return normalized if normalized != "/" else "/"
    
    def _get_node(self, path: str) -> FileNode | None:
        """Get node at path, or None if not found."""
        path = self.resolve(path)
        
        if path == "/":
            return self.root
        
        parts = self._split_path(path)
        current = self.root
        
        for part in parts:
            if not current.is_dir:
                return None
            if part not in current.children:
                return None
            current = current.children[part]
        
        return current
    
    def _get_parent(self, path: str) -> tuple[FileNode, str] | None:
        """Get parent node and child name for a path."""
        path = self.resolve(path)
        
        if path == "/":
            return None  # Root has no parent
        
        parts = self._split_path(path)
        child_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1])
        
        parent = self._get_node(parent_path)
        if parent is None or not parent.is_dir:
            return None
        
        return (parent, child_name)
    
    # Public API
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return self._get_node(path) is not None
    
    def isdir(self, path: str) -> bool:
        """Check if path is a directory."""
        node = self._get_node(path)
        return node is not None and node.is_dir
    
    def isfile(self, path: str) -> bool:
        """Check if path is a file."""
        node = self._get_node(path)
        return node is not None and not node.is_dir
    
    def cd(self, path: str) -> bool:
        """
        Change current directory.
        
        Returns True on success, False if path doesn't exist or isn't a directory.
        """
        if path == "-":
            # Switch to previous directory
            target = self._prev_cwd
        else:
            target = self.resolve(path)
        
        if not self.isdir(target):
            return False
        
        # Save current as previous before changing
        self._prev_cwd = self.cwd
        self.cwd = target
        return True
    
    def ls(self, path: str = "", show_hidden: bool = False) -> list[tuple[str, bool]]:
        """
        List directory contents.
        
        Args:
            path: Directory to list (default: cwd)
            show_hidden: Include hidden files (starting with .)
            
        Returns:
            List of (name, is_dir) tuples, sorted alphabetically.
        """
        target = self.resolve(path) if path else self.cwd
        node = self._get_node(target)
        
        if node is None:
            raise PathNotFoundError(f"ls: cannot access '{path}': No such file or directory")
        
        if not node.is_dir:
            # Single file
            return [(node.name, False)]
        
        result = []
        for name, child in node.children.items():
            if not show_hidden and name.startswith("."):
                continue
            result.append((name, child.is_dir))
        
        return sorted(result, key=lambda x: (not x[1], x[0].lower()))
    
    def ls_detailed(self, path: str = "", show_hidden: bool = False) -> list[dict]:
        """
        List directory with details (like ls -l).
        
        Returns list of dicts with: name, is_dir, permissions, owner, group, size, modified
        """
        target = self.resolve(path) if path else self.cwd
        node = self._get_node(target)
        
        if node is None:
            raise PathNotFoundError(f"ls: cannot access '{path}': No such file or directory")
        
        if not node.is_dir:
            return [{
                "name": node.name,
                "is_dir": False,
                "permissions": node.permissions.to_string(),
                "owner": node.owner,
                "group": node.group,
                "size": node.size,
                "modified": node.modified,
            }]
        
        result = []
        for name, child in sorted(node.children.items()):
            if not show_hidden and name.startswith("."):
                continue
            result.append({
                "name": name,
                "is_dir": child.is_dir,
                "permissions": child.permissions.to_string(),
                "owner": child.owner,
                "group": child.group,
                "size": child.size if not child.is_dir else 4096,
                "modified": child.modified,
            })
        
        return sorted(result, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    def mkdir(self, path: str, parents: bool = False) -> bool:
        """
        Create directory.
        
        Args:
            path: Directory path to create
            parents: Create parent directories if needed (like mkdir -p)
            
        Returns:
            True on success
        """
        target = self.resolve(path)
        
        if self.exists(target):
            raise FileExistsError(f"mkdir: cannot create directory '{path}': File exists")
        
        result = self._get_parent(target)
        if result is None:
            if parents:
                # Create parent directories
                parts = self._split_path(target)
                current = self.root
                for part in parts:
                    if part not in current.children:
                        current.children[part] = FileNode(
                            name=part,
                            is_dir=True,
                            owner=self.username,
                            group=self.username,
                        )
                    current = current.children[part]
                return True
            raise PathNotFoundError(f"mkdir: cannot create directory '{path}': No such file or directory")
        
        parent, name = result
        parent.children[name] = FileNode(
            name=name,
            is_dir=True,
            owner=self.username,
            group=self.username,
        )
        return True
    
    def touch(self, path: str) -> bool:
        """
        Create empty file or update timestamp.
        
        Returns True on success.
        """
        target = self.resolve(path)
        
        # If exists, update timestamp
        node = self._get_node(target)
        if node is not None:
            node.modified = datetime.now()
            return True
        
        # Create new file
        result = self._get_parent(target)
        if result is None:
            raise PathNotFoundError(f"touch: cannot touch '{path}': No such file or directory")
        
        parent, name = result
        parent.children[name] = FileNode(
            name=name,
            is_dir=False,
            owner=self.username,
            group=self.username,
        )
        return True
    
    def rm(self, path: str, recursive: bool = False, force: bool = False) -> bool:
        """
        Remove file or directory.
        
        Args:
            path: Path to remove
            recursive: Remove directories recursively (-r)
            force: Ignore nonexistent files (-f)
            
        Returns:
            True on success
        """
        target = self.resolve(path)
        
        # Special case: rm -rf / simulation
        if target == "/" and recursive:
            # Simulate catastrophic deletion
            self.root.children = {}
            return True
        
        node = self._get_node(target)
        
        if node is None:
            if force:
                return True
            raise PathNotFoundError(f"rm: cannot remove '{path}': No such file or directory")
        
        if node.is_dir and not recursive:
            raise IsADirectoryError(f"rm: cannot remove '{path}': Is a directory")
        
        result = self._get_parent(target)
        if result is None:
            raise PermissionError(f"rm: cannot remove '{path}': Permission denied")
        
        parent, name = result
        del parent.children[name]
        return True
    
    def cat(self, path: str) -> str:
        """
        Read file contents.
        
        Returns file content as string.
        """
        target = self.resolve(path)
        node = self._get_node(target)
        
        if node is None:
            raise PathNotFoundError(f"cat: {path}: No such file or directory")
        
        if node.is_dir:
            raise IsADirectoryError(f"cat: {path}: Is a directory")
        
        return node.content
    
    def write(self, path: str, content: str, append: bool = False) -> bool:
        """
        Write content to file.
        
        Args:
            path: File path
            content: Content to write
            append: Append instead of overwrite
        """
        target = self.resolve(path)
        node = self._get_node(target)
        
        if node is None:
            # Create file
            self.touch(path)
            node = self._get_node(target)
        
        if node.is_dir:
            raise IsADirectoryError(f"cannot write to '{path}': Is a directory")
        
        if append:
            node.content += content
        else:
            node.content = content
        
        node.size = len(node.content.encode('utf-8'))
        node.modified = datetime.now()
        return True
    
    def cp(self, src: str, dst: str, recursive: bool = False) -> bool:
        """Copy file or directory."""
        src_node = self._get_node(src)
        
        if src_node is None:
            raise PathNotFoundError(f"cp: cannot stat '{src}': No such file or directory")
        
        if src_node.is_dir and not recursive:
            raise IsADirectoryError(f"cp: -r not specified; omitting directory '{src}'")
        
        # Deep copy
        new_node = copy.deepcopy(src_node)
        
        # Determine destination
        dst_resolved = self.resolve(dst)
        dst_node = self._get_node(dst_resolved)
        
        if dst_node is not None and dst_node.is_dir:
            # Copy into directory
            dst_resolved = dst_resolved + "/" + src_node.name
        
        result = self._get_parent(dst_resolved)
        if result is None:
            raise PathNotFoundError(f"cp: cannot create '{dst}': No such file or directory")
        
        parent, name = result
        new_node.name = name
        parent.children[name] = new_node
        return True
    
    def mv(self, src: str, dst: str) -> bool:
        """Move/rename file or directory."""
        src_node = self._get_node(src)
        
        if src_node is None:
            raise PathNotFoundError(f"mv: cannot stat '{src}': No such file or directory")
        
        # Copy then delete
        self.cp(src, dst, recursive=True)
        
        src_result = self._get_parent(src)
        if src_result:
            parent, name = src_result
            del parent.children[name]
        
        return True
    
    def get_prompt_path(self) -> str:
        """Get path for prompt display (~ substitution)."""
        if self.cwd == self.home:
            return "~"
        if self.cwd.startswith(self.home + "/"):
            return "~" + self.cwd[len(self.home):]
        return self.cwd
    
    # Checkpoint system
    
    def save_checkpoint(self):
        """Save current state for later restore."""
        self._checkpoint = copy.deepcopy(self.root)
        self._checkpoint_cwd = self.cwd
    
    def restore_checkpoint(self) -> bool:
        """Restore to last checkpoint."""
        if self._checkpoint is None:
            return False
        
        self.root = copy.deepcopy(self._checkpoint)
        self.cwd = self._checkpoint_cwd
        return True
    
    def reset(self):
        """Reset to initial state."""
        self.root = FileNode(name="/", is_dir=True)
        self._init_default_structure()
        self.cwd = self.home
        self._prev_cwd = self.home
    
    # Serialization
    
    def to_json(self) -> str:
        """Serialize filesystem to JSON."""
        data = {
            "username": self.username,
            "hostname": self.hostname,
            "cwd": self.cwd,
            "root": self.root.to_dict(),
        }
        return json.dumps(data, indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> VirtualFileSystem:
        """Deserialize filesystem from JSON."""
        data = json.loads(json_str)
        fs = cls(username=data["username"])
        fs.hostname = data.get("hostname", "quest")
        fs.cwd = data["cwd"]
        fs.root = FileNode.from_dict(data["root"])
        return fs
