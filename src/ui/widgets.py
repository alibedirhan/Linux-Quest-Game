"""
Linux Command Quest - UI System
================================

Panel-based UI with widgets for game interface.
"""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..core.terminal import Terminal
    from ..core.colors import ColorManager


@dataclass
class Rect:
    """Rectangle for UI positioning."""
    
    y: int
    x: int
    height: int
    width: int
    
    @property
    def y2(self) -> int:
        return self.y + self.height
    
    @property
    def x2(self) -> int:
        return self.x + self.width
    
    @property
    def inner(self) -> "Rect":
        """Get inner rect (1 char padding)."""
        return Rect(
            y=self.y + 1,
            x=self.x + 1,
            height=max(0, self.height - 2),
            width=max(0, self.width - 2),
        )


class Widget(ABC):
    """Base class for UI widgets."""
    
    def __init__(self, rect: Rect):
        self.rect = rect
        self.visible = True
        self.focused = False
    
    @abstractmethod
    def render(self, term: Terminal, colors: ColorManager):
        """Render the widget."""
        pass
    
    def handle_key(self, key: int) -> bool:
        """Handle key input. Returns True if handled."""
        return False


class Panel(Widget):
    """Bordered panel with optional title."""
    
    def __init__(self, rect: Rect, title: str = "", border_color: int = 0):
        super().__init__(rect)
        self.title = title
        self.border_color = border_color
        self.content_lines: list[tuple[str, int]] = []  # (text, attr)
    
    def render(self, term: Terminal, colors: ColorManager):
        if not self.visible:
            return
        
        from ..core.colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        r = self.rect
        
        # Border color
        if self.focused:
            border_attr = colors.attr(ColorPair.BORDER_ACTIVE)
        else:
            border_attr = colors.attr(ColorPair.BORDER)
        
        # Top border
        term.write(r.y, r.x, box.TL, border_attr)
        
        if self.title:
            title_str = f" {self.title} "
            border_left = (r.width - 2 - len(title_str)) // 2
            border_right = r.width - 2 - len(title_str) - border_left
            term.write(r.y, r.x + 1, box.H * border_left, border_attr)
            term.write(r.y, r.x + 1 + border_left, title_str, 
                      colors.attr(ColorPair.TITLE, bold=True))
            term.write(r.y, r.x + 1 + border_left + len(title_str), 
                      box.H * border_right, border_attr)
        else:
            term.write(r.y, r.x + 1, box.H * (r.width - 2), border_attr)
        
        term.write(r.y, r.x + r.width - 1, box.TR, border_attr)
        
        # Sides and content
        inner = r.inner
        for i in range(r.height - 2):
            row = r.y + 1 + i
            term.write(row, r.x, box.V, border_attr)
            
            # Clear inner area
            term.write(row, r.x + 1, " " * (r.width - 2), 0)
            
            # Content
            if i < len(self.content_lines):
                text, attr = self.content_lines[i]
                # Truncate if needed
                if len(text) > inner.width:
                    text = text[:inner.width - 1] + "…"
                term.write(row, inner.x, text, attr)
            
            term.write(row, r.x + r.width - 1, box.V, border_attr)
        
        # Bottom border
        term.write(r.y + r.height - 1, r.x, box.BL, border_attr)
        term.write(r.y + r.height - 1, r.x + 1, box.H * (r.width - 2), border_attr)
        term.write(r.y + r.height - 1, r.x + r.width - 1, box.BR, border_attr)
    
    def set_content(self, lines: list[tuple[str, int]]):
        """Set panel content."""
        self.content_lines = lines
    
    def add_line(self, text: str, attr: int = 0):
        """Add a line to content."""
        self.content_lines.append((text, attr))
    
    def clear_content(self):
        """Clear panel content."""
        self.content_lines = []


class ScrollablePanel(Panel):
    """Panel with scrollable content."""
    
    def __init__(self, rect: Rect, title: str = ""):
        super().__init__(rect, title)
        self.scroll_offset = 0
        self.all_lines: list[tuple[str, int]] = []
    
    @property
    def visible_lines(self) -> int:
        return self.rect.height - 2
    
    @property
    def max_scroll(self) -> int:
        return max(0, len(self.all_lines) - self.visible_lines)
    
    def scroll_up(self, amount: int = 1):
        self.scroll_offset = max(0, self.scroll_offset - amount)
        self._update_visible()
    
    def scroll_down(self, amount: int = 1):
        self.scroll_offset = min(self.max_scroll, self.scroll_offset + amount)
        self._update_visible()
    
    def scroll_to_bottom(self):
        self.scroll_offset = self.max_scroll
        self._update_visible()
    
    def set_all_lines(self, lines: list[tuple[str, int]]):
        self.all_lines = lines
        self._update_visible()
    
    def add_line(self, text: str, attr: int = 0):
        self.all_lines.append((text, attr))
        self.scroll_to_bottom()
    
    def _update_visible(self):
        start = self.scroll_offset
        end = start + self.visible_lines
        self.content_lines = self.all_lines[start:end]
    
    def clear_content(self):
        self.all_lines = []
        self.scroll_offset = 0
        super().clear_content()


class Header(Widget):
    """Top header bar."""
    
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self.title = "LINUX COMMAND QUEST"
        self.subtitle = ""
        self.right_text = ""
    
    def render(self, term: Terminal, colors: ColorManager):
        if not self.visible:
            return
        
        from ..core.colors import ColorPair
        
        r = self.rect
        
        # Background
        attr = colors.attr(ColorPair.HEADER)
        term.write(r.y, r.x, " " * r.width, attr)
        
        # Title
        term.write(r.y, r.x + 2, self.title, 
                  colors.attr(ColorPair.HEADER_ACCENT, bold=True))
        
        # Subtitle
        if self.subtitle:
            term.write(r.y, r.x + 2 + len(self.title) + 3, f"│ {self.subtitle}", attr)
        
        # Right side
        if self.right_text:
            term.write(r.y, r.x + r.width - len(self.right_text) - 2, 
                      self.right_text, attr)


class StatusBar(Widget):
    """Bottom status bar."""
    
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self.left_text = ""
        self.center_text = ""
        self.right_text = ""
    
    def render(self, term: Terminal, colors: ColorManager):
        if not self.visible:
            return
        
        from ..core.colors import ColorPair
        
        r = self.rect
        attr = colors.attr(ColorPair.HEADER)
        
        # Background
        term.write(r.y, r.x, " " * r.width, attr)
        
        # Left
        if self.left_text:
            term.write(r.y, r.x + 2, self.left_text, attr)
        
        # Center
        if self.center_text:
            cx = (r.width - len(self.center_text)) // 2
            term.write(r.y, r.x + cx, self.center_text, attr)
        
        # Right
        if self.right_text:
            term.write(r.y, r.x + r.width - len(self.right_text) - 2, 
                      self.right_text, attr)


class TaskList(Widget):
    """Widget showing mission tasks."""
    
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self.tasks: list[dict] = []  # {description, status: done/active/pending}
        self.active_index = 0
    
    def render(self, term: Terminal, colors: ColorManager):
        if not self.visible:
            return
        
        from ..core.colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        r = self.rect
        
        # Border
        border_attr = colors.attr(ColorPair.BORDER_ACTIVE if self.focused else ColorPair.BORDER)
        
        # Top
        term.write(r.y, r.x, box.TL + box.H * (r.width - 2) + box.TR, border_attr)
        
        # Title
        title = " GÖREVLER "
        term.write(r.y, r.x + (r.width - len(title)) // 2, title,
                  colors.attr(ColorPair.TITLE, bold=True))
        
        # Content
        inner = r.inner
        for i in range(r.height - 2):
            row = r.y + 1 + i
            term.write(row, r.x, box.V, border_attr)
            term.write(row, r.x + 1, " " * (r.width - 2), 0)
            term.write(row, r.x + r.width - 1, box.V, border_attr)
            
            if i < len(self.tasks):
                task = self.tasks[i]
                status = task.get("status", "pending")
                desc = task.get("description", "")
                
                # Status indicator
                if status == "done":
                    indicator = "\033[32m[✓]\033[0m"
                    attr = colors.attr(ColorPair.TASK_DONE)
                elif status == "active":
                    indicator = "\033[33m[>]\033[0m"
                    attr = colors.attr(ColorPair.TASK_ACTIVE, bold=True)
                else:
                    indicator = "\033[90m[ ]\033[0m"
                    attr = colors.attr(ColorPair.TASK_PENDING, dim=True)
                
                # Truncate description
                max_desc = inner.width - 6
                if len(desc) > max_desc:
                    desc = desc[:max_desc - 1] + "…"
                
                line = f" {indicator} {desc}"
                term.write(row, inner.x, line[:inner.width], 0)
        
        # Bottom
        term.write(r.y + r.height - 1, r.x, 
                  box.BL + box.H * (r.width - 2) + box.BR, border_attr)
    
    def set_tasks(self, tasks: list[dict]):
        self.tasks = tasks


class InputLine(Widget):
    """Command input line widget."""
    
    def __init__(self, rect: Rect):
        super().__init__(rect)
        self.prompt = "$ "
        self.text = ""
        self.cursor_pos = 0
    
    def render(self, term: Terminal, colors: ColorManager):
        if not self.visible:
            return
        
        from ..core.colors import ColorPair
        
        r = self.rect
        
        # Clear line
        term.write(r.y, r.x, " " * r.width, 0)
        
        # Prompt
        term.write(r.y, r.x, self.prompt, 0)
        
        # Text
        prompt_len = len(self.prompt.replace("\033[0m", "").replace("\033[32m", "")
                        .replace("\033[36m", "").replace("\033[34m", ""))
        
        # Calculate visible text
        max_text = r.width - prompt_len - 1
        
        if len(self.text) <= max_text:
            visible_text = self.text
            cursor_x = r.x + prompt_len + self.cursor_pos
        else:
            # Scroll to show cursor
            start = max(0, self.cursor_pos - max_text + 1)
            visible_text = self.text[start:start + max_text]
            cursor_x = r.x + prompt_len + (self.cursor_pos - start)
        
        term.write(r.y, r.x + prompt_len, visible_text, 0)
        
        # Position cursor
        term.move(r.y, cursor_x)


@dataclass
class Layout:
    """Screen layout configuration."""
    
    header: Rect
    left_panel: Rect
    right_panel: Rect
    log_panel: Rect
    status_bar: Rect
    input_line: Rect
    
    @classmethod
    def create(cls, rows: int, cols: int) -> "Layout":
        """Create layout for given screen size."""
        
        # Header: 1 row at top
        header = Rect(0, 0, 1, cols)
        
        # Main area
        main_top = 1
        main_height = rows - 3  # Leave room for status and input
        
        # Left panel: ~30% width
        left_width = min(40, cols // 3)
        left_panel = Rect(main_top, 0, main_height, left_width)
        
        # Right panel: remaining width, upper portion
        right_width = cols - left_width
        terminal_height = main_height * 2 // 3
        right_panel = Rect(main_top, left_width, terminal_height, right_width)
        
        # Log panel: below terminal
        log_height = main_height - terminal_height
        log_panel = Rect(main_top + terminal_height, left_width, log_height, right_width)
        
        # Status bar: second to last row
        status_bar = Rect(rows - 2, 0, 1, cols)
        
        # Input line: last row
        input_line = Rect(rows - 1, 0, 1, cols)
        
        return cls(
            header=header,
            left_panel=left_panel,
            right_panel=right_panel,
            log_panel=log_panel,
            status_bar=status_bar,
            input_line=input_line,
        )


class GameUI:
    """Main game UI manager."""
    
    def __init__(self, term: Terminal, colors: ColorManager):
        self.term = term
        self.colors = colors
        
        size = term.get_size()
        self.layout = Layout.create(size.rows, size.cols)
        
        # Create widgets
        self.header = Header(self.layout.header)
        self.task_panel = Panel(self.layout.left_panel, "GÖREVLER")
        self.terminal_panel = ScrollablePanel(self.layout.right_panel, "TERMİNAL")
        self.log_panel = ScrollablePanel(self.layout.log_panel, "SİSTEM LOG")
        self.status_bar = StatusBar(self.layout.status_bar)
        self.input_widget = InputLine(self.layout.input_line)
        
        self.terminal_panel.focused = True
    
    def render(self):
        """Render all widgets."""
        self.term.clear()
        
        self.header.render(self.term, self.colors)
        self.task_panel.render(self.term, self.colors)
        self.terminal_panel.render(self.term, self.colors)
        self.log_panel.render(self.term, self.colors)
        self.status_bar.render(self.term, self.colors)
        self.input_widget.render(self.term, self.colors)
        
        self.term.refresh()
    
    def resize(self):
        """Handle terminal resize."""
        size = self.term.get_size()
        self.layout = Layout.create(size.rows, size.cols)
        
        # Update widget rects
        self.header.rect = self.layout.header
        self.task_panel.rect = self.layout.left_panel
        self.terminal_panel.rect = self.layout.right_panel
        self.log_panel.rect = self.layout.log_panel
        self.status_bar.rect = self.layout.status_bar
        self.input_widget.rect = self.layout.input_line
