"""
Linux Command Quest - Terminal Management
==========================================

Curses-based terminal handling with input management,
screen buffering, and event system.
"""

from __future__ import annotations

import curses
import locale
import signal
import sys
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from typing import Any


class Key(IntEnum):
    """Special key constants."""
    
    NONE = 0
    UP = curses.KEY_UP
    DOWN = curses.KEY_DOWN
    LEFT = curses.KEY_LEFT
    RIGHT = curses.KEY_RIGHT
    ENTER = 10
    TAB = 9
    BACKSPACE = 127
    DELETE = curses.KEY_DC
    HOME = curses.KEY_HOME
    END = curses.KEY_END
    PAGE_UP = curses.KEY_PPAGE
    PAGE_DOWN = curses.KEY_NPAGE
    ESCAPE = 27
    RESIZE = curses.KEY_RESIZE
    
    # Ctrl combinations
    CTRL_A = 1
    CTRL_B = 2
    CTRL_C = 3
    CTRL_D = 4
    CTRL_E = 5
    CTRL_F = 6
    CTRL_G = 7
    CTRL_H = 8      # Hint
    CTRL_I = 9      # Tab
    CTRL_J = 10     # Enter
    CTRL_K = 11
    CTRL_L = 12     # Clear/Redraw
    CTRL_M = 13     # Enter
    CTRL_N = 14
    CTRL_O = 15
    CTRL_P = 16
    CTRL_Q = 17     # Quit
    CTRL_R = 18     # Reset
    CTRL_S = 19
    CTRL_T = 20
    CTRL_U = 21     # Clear line
    CTRL_V = 22
    CTRL_W = 23     # Delete word
    CTRL_X = 24
    CTRL_Y = 25
    CTRL_Z = 26


@dataclass
class KeyEvent:
    """Represents a keyboard event."""
    
    key: int
    char: str = ""
    ctrl: bool = False
    alt: bool = False
    
    @property
    def is_printable(self) -> bool:
        """Check if key is a printable character."""
        return len(self.char) == 1 and self.char.isprintable()
    
    @property
    def is_enter(self) -> bool:
        return self.key in (Key.ENTER, Key.CTRL_J, Key.CTRL_M, curses.KEY_ENTER)
    
    @property
    def is_backspace(self) -> bool:
        return self.key in (Key.BACKSPACE, curses.KEY_BACKSPACE, Key.CTRL_H, 8)
    
    @property
    def is_tab(self) -> bool:
        return self.key == Key.TAB
    
    @property
    def is_escape(self) -> bool:
        return self.key == Key.ESCAPE
    
    @property
    def is_arrow(self) -> bool:
        return self.key in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT)


@dataclass
class ScreenSize:
    """Terminal screen dimensions."""
    
    rows: int
    cols: int
    
    @property
    def min_supported(self) -> bool:
        """Check if screen meets minimum requirements."""
        return self.rows >= 24 and self.cols >= 80
    
    @property
    def recommended(self) -> bool:
        """Check if screen meets recommended size."""
        return self.rows >= 35 and self.cols >= 120


class Terminal:
    """
    Curses-based terminal manager.
    
    Handles:
    - Screen initialization and cleanup
    - Input reading with timeout
    - Screen size tracking
    - Signal handling (resize, interrupt)
    
    Usage:
        with Terminal() as term:
            while True:
                event = term.get_key(timeout=100)
                if event.is_escape:
                    break
                term.stdscr.addstr(0, 0, f"Key: {event.key}")
                term.stdscr.refresh()
    """
    
    MIN_ROWS = 24
    MIN_COLS = 80
    
    def __init__(self):
        self.stdscr = None
        self._old_signal_handlers: dict[int, Any] = {}
        self._resize_callback: Callable[[ScreenSize], None] | None = None
        self._running = True
    
    def __enter__(self) -> Terminal:
        """Initialize terminal."""
        self._setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup terminal."""
        self._cleanup()
        return False
    
    def _setup(self):
        """Initialize curses and terminal settings."""
        # Set locale for Unicode support
        locale.setlocale(locale.LC_ALL, '')
        
        # Initialize curses
        self.stdscr = curses.initscr()
        
        # Terminal settings
        curses.noecho()          # Don't echo keypresses
        curses.cbreak()          # React to keys instantly
        curses.curs_set(1)       # Show cursor
        self.stdscr.keypad(True) # Enable special keys
        
        # Mouse support (optional)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
        except curses.error:
            pass  # Mouse not supported
        
        # Setup signal handlers
        self._setup_signals()
        
        # Initial size check
        size = self.get_size()
        if not size.min_supported:
            self._cleanup()
            print(f"Terminal çok küçük: {size.cols}x{size.rows}")
            print(f"Minimum gereksinim: {self.MIN_COLS}x{self.MIN_ROWS}")
            sys.exit(1)
    
    def _cleanup(self):
        """Restore terminal to normal state."""
        if self.stdscr:
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
        
        # Restore signal handlers
        for sig, handler in self._old_signal_handlers.items():
            signal.signal(sig, handler)
    
    def _setup_signals(self):
        """Setup signal handlers."""
        # SIGWINCH - Terminal resize
        if hasattr(signal, 'SIGWINCH'):
            self._old_signal_handlers[signal.SIGWINCH] = signal.signal(
                signal.SIGWINCH, 
                self._handle_resize
            )
        
        # SIGINT - Ctrl+C (let it through for normal handling)
        # We don't override SIGINT to allow clean exit
    
    def _handle_resize(self, signum, frame):
        """Handle terminal resize signal."""
        curses.endwin()
        self.stdscr.refresh()
        
        size = self.get_size()
        if self._resize_callback:
            self._resize_callback(size)
    
    def on_resize(self, callback: Callable[[ScreenSize], None]):
        """Register resize callback."""
        self._resize_callback = callback
    
    def get_size(self) -> ScreenSize:
        """Get current terminal size."""
        rows, cols = self.stdscr.getmaxyx()
        return ScreenSize(rows=rows, cols=cols)
    
    def get_key(self, timeout: int = -1) -> KeyEvent:
        """
        Read a key with optional timeout.
        
        Args:
            timeout: Milliseconds to wait (-1 for blocking, 0 for non-blocking)
            
        Returns:
            KeyEvent with key information
        """
        self.stdscr.timeout(timeout)
        
        try:
            key = self.stdscr.getch()
        except KeyboardInterrupt:
            return KeyEvent(key=Key.CTRL_C, ctrl=True)
        
        if key == -1:
            return KeyEvent(key=Key.NONE)
        
        # Check for Ctrl combinations (0-31)
        ctrl = False
        if 0 < key < 32:
            ctrl = True
        
        # Get character representation
        char = ""
        if 32 <= key < 127:
            char = chr(key)
        
        return KeyEvent(key=key, char=char, ctrl=ctrl)
    
    def clear(self):
        """Clear the screen."""
        self.stdscr.clear()
    
    def refresh(self):
        """Refresh the screen."""
        self.stdscr.refresh()
    
    def set_cursor(self, visible: bool):
        """Show or hide cursor."""
        try:
            curses.curs_set(1 if visible else 0)
        except curses.error:
            pass  # Some terminals don't support cursor visibility
    
    def move(self, row: int, col: int):
        """Move cursor to position."""
        try:
            self.stdscr.move(row, col)
        except curses.error:
            pass
    
    def write(self, row: int, col: int, text: str, attr: int = 0):
        """
        Write text at position with optional attributes.
        
        Args:
            row: Row position (0-indexed)
            col: Column position (0-indexed)
            text: Text to write
            attr: Curses attributes (color pair, bold, etc.)
        """
        try:
            self.stdscr.addstr(row, col, text, attr)
        except curses.error:
            pass  # Ignore write errors (usually at screen edge)
    
    def write_centered(self, row: int, text: str, attr: int = 0):
        """Write text centered on row."""
        size = self.get_size()
        col = max(0, (size.cols - len(text)) // 2)
        self.write(row, col, text, attr)
    
    def fill_line(self, row: int, char: str = " ", attr: int = 0):
        """Fill entire line with character."""
        size = self.get_size()
        self.write(row, 0, char * size.cols, attr)
    
    def draw_box(self, y: int, x: int, height: int, width: int, 
                 attr: int = 0, title: str = ""):
        """
        Draw a box with optional title.
        
        Args:
            y, x: Top-left corner position
            height, width: Box dimensions
            attr: Curses attributes
            title: Optional title for top border
        """
        from .colors import get_box_chars
        box = get_box_chars()
        
        # Top border
        self.write(y, x, box.TL, attr)
        if title:
            title_str = f" {title} "
            border_left = (width - 2 - len(title_str)) // 2
            border_right = width - 2 - len(title_str) - border_left
            self.write(y, x + 1, box.H * border_left, attr)
            self.write(y, x + 1 + border_left, title_str, attr | curses.A_BOLD)
            self.write(y, x + 1 + border_left + len(title_str), box.H * border_right, attr)
        else:
            self.write(y, x + 1, box.H * (width - 2), attr)
        self.write(y, x + width - 1, box.TR, attr)
        
        # Sides
        for row in range(y + 1, y + height - 1):
            self.write(row, x, box.V, attr)
            self.write(row, x + width - 1, box.V, attr)
        
        # Bottom border
        self.write(y + height - 1, x, box.BL, attr)
        self.write(y + height - 1, x + 1, box.H * (width - 2), attr)
        self.write(y + height - 1, x + width - 1, box.BR, attr)
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def quit(self):
        """Signal to quit the application."""
        self._running = False


class InputLine:
    """
    Handles single-line text input with history.
    
    Features:
    - Character input/deletion
    - Cursor movement
    - Command history (up/down arrows)
    - Word deletion (Ctrl+W)
    - Line clear (Ctrl+U)
    """
    
    def __init__(self, history_size: int = 100):
        self.buffer: list[str] = []
        self.cursor: int = 0
        self.history: list[str] = []
        self.history_idx: int = 0
        self.history_size = history_size
        self._saved_buffer: list[str] = []
    
    @property
    def text(self) -> str:
        """Get current input text."""
        return "".join(self.buffer)
    
    @text.setter
    def text(self, value: str):
        """Set input text."""
        self.buffer = list(value)
        self.cursor = len(self.buffer)
    
    def clear(self):
        """Clear input buffer."""
        self.buffer = []
        self.cursor = 0
        self.history_idx = len(self.history)
    
    def handle_key(self, event: KeyEvent) -> str | None:
        """
        Process a key event.
        
        Returns:
            The completed input string if Enter was pressed, None otherwise.
        """
        if event.is_enter:
            result = self.text
            if result.strip():  # Don't add empty commands to history
                self._add_to_history(result)
            self.clear()
            return result
        
        elif event.is_backspace:
            if self.cursor > 0:
                self.buffer.pop(self.cursor - 1)
                self.cursor -= 1
        
        elif event.key == Key.DELETE:
            if self.cursor < len(self.buffer):
                self.buffer.pop(self.cursor)
        
        elif event.key == Key.LEFT:
            if self.cursor > 0:
                self.cursor -= 1
        
        elif event.key == Key.RIGHT:
            if self.cursor < len(self.buffer):
                self.cursor += 1
        
        elif event.key == Key.HOME or event.key == Key.CTRL_A:
            self.cursor = 0
        
        elif event.key == Key.END or event.key == Key.CTRL_E:
            self.cursor = len(self.buffer)
        
        elif event.key == Key.UP:
            self._history_prev()
        
        elif event.key == Key.DOWN:
            self._history_next()
        
        elif event.key == Key.CTRL_U:
            # Clear line
            self.buffer = self.buffer[self.cursor:]
            self.cursor = 0
        
        elif event.key == Key.CTRL_W:
            # Delete word backward
            self._delete_word_backward()
        
        elif event.is_printable:
            self.buffer.insert(self.cursor, event.char)
            self.cursor += 1
        
        return None
    
    def _add_to_history(self, cmd: str):
        """Add command to history."""
        # Don't add duplicates of last command
        if self.history and self.history[-1] == cmd:
            return
        
        self.history.append(cmd)
        
        # Limit history size
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        self.history_idx = len(self.history)
    
    def _history_prev(self):
        """Navigate to previous history item."""
        if not self.history:
            return
        
        # Save current input when starting to browse
        if self.history_idx == len(self.history):
            self._saved_buffer = self.buffer.copy()
        
        if self.history_idx > 0:
            self.history_idx -= 1
            self.buffer = list(self.history[self.history_idx])
            self.cursor = len(self.buffer)
    
    def _history_next(self):
        """Navigate to next history item."""
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self.buffer = list(self.history[self.history_idx])
            self.cursor = len(self.buffer)
        elif self.history_idx == len(self.history) - 1:
            # Restore saved input
            self.history_idx = len(self.history)
            self.buffer = self._saved_buffer.copy()
            self.cursor = len(self.buffer)
    
    def _delete_word_backward(self):
        """Delete word before cursor."""
        if self.cursor == 0:
            return
        
        # Find start of word
        pos = self.cursor - 1
        
        # Skip trailing spaces
        while pos > 0 and self.buffer[pos] == ' ':
            pos -= 1
        
        # Find word start
        while pos > 0 and self.buffer[pos - 1] != ' ':
            pos -= 1
        
        # Delete from pos to cursor
        del self.buffer[pos:self.cursor]
        self.cursor = pos
