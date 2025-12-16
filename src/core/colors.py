"""
Linux Command Quest - Color & Theme System
==========================================

Curses-based color management with theme support.
Supports 256-color terminals with fallback to 8 colors.
"""

from __future__ import annotations

import curses
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar


class ColorPair(IntEnum):
    """Predefined color pairs for consistent UI styling."""
    
    DEFAULT = 1
    PROMPT_USER = 2
    PROMPT_HOST = 3
    PROMPT_PATH = 4
    SUCCESS = 5
    ERROR = 6
    WARNING = 7
    INFO = 8
    DIRECTORY = 9
    FILE = 10
    EXECUTABLE = 11
    SYMLINK = 12
    HIDDEN = 13
    HEADER = 14
    HEADER_ACCENT = 15
    BORDER = 16
    BORDER_ACTIVE = 17
    TASK_DONE = 18
    TASK_ACTIVE = 19
    TASK_PENDING = 20
    LOG_TIME = 21
    LOG_SUCCESS = 22
    LOG_ERROR = 23
    HINT = 24
    SCORE = 25
    TITLE = 26
    SUBTITLE = 27
    MENU_NORMAL = 28
    MENU_SELECTED = 29
    MENU_DISABLED = 30
    SYSTEM_CPU = 31
    SYSTEM_RAM = 32


@dataclass
class Theme:
    """Color theme definition."""
    
    name: str
    description: str
    
    # Base colors (curses color constants or 256-color codes)
    bg: int = curses.COLOR_BLACK
    fg: int = curses.COLOR_WHITE
    
    # Accent colors
    primary: int = curses.COLOR_CYAN
    secondary: int = curses.COLOR_BLUE
    accent: int = curses.COLOR_MAGENTA
    
    # Semantic colors
    success: int = curses.COLOR_GREEN
    error: int = curses.COLOR_RED
    warning: int = curses.COLOR_YELLOW
    info: int = curses.COLOR_CYAN
    
    # UI specific
    border: int = curses.COLOR_WHITE
    border_active: int = curses.COLOR_CYAN
    header_bg: int = curses.COLOR_BLUE
    
    # Terminal colors
    dir_color: int = curses.COLOR_BLUE
    exec_color: int = curses.COLOR_GREEN
    link_color: int = curses.COLOR_CYAN
    
    # 256-color mode flag
    use_256: bool = False
    
    def __post_init__(self):
        """Convert to 256-color if supported."""
        if self.use_256 and curses.COLORS >= 256:
            self._apply_256_colors()
    
    def _apply_256_colors(self):
        """Override with 256-color palette."""
        pass  # Subclasses can override


@dataclass
class MatrixTheme(Theme):
    """Classic green-on-black hacker aesthetic."""
    
    name: str = "matrix"
    description: str = "Klasik yeşil hacker teması"
    
    primary: int = curses.COLOR_GREEN
    secondary: int = curses.COLOR_GREEN
    accent: int = curses.COLOR_WHITE
    border: int = curses.COLOR_GREEN
    border_active: int = curses.COLOR_WHITE
    
    def _apply_256_colors(self):
        self.primary = 46      # Bright green
        self.secondary = 34    # Dark green
        self.border = 22       # Forest green


@dataclass  
class CyberpunkTheme(Theme):
    """Neon blue/pink cyberpunk style."""
    
    name: str = "cyberpunk"
    description: str = "Neon mavi/pembe cyberpunk"
    
    primary: int = curses.COLOR_CYAN
    secondary: int = curses.COLOR_BLUE
    accent: int = curses.COLOR_MAGENTA
    border: int = curses.COLOR_CYAN
    border_active: int = curses.COLOR_MAGENTA
    header_bg: int = curses.COLOR_BLUE
    
    def _apply_256_colors(self):
        self.primary = 51      # Cyan
        self.secondary = 27    # Blue
        self.accent = 201      # Pink
        self.border = 39       # Light blue


@dataclass
class RetroTheme(Theme):
    """Amber monochrome retro terminal."""
    
    name: str = "retro"
    description: str = "Amber retro terminal"
    
    primary: int = curses.COLOR_YELLOW
    secondary: int = curses.COLOR_YELLOW
    accent: int = curses.COLOR_WHITE
    success: int = curses.COLOR_YELLOW
    info: int = curses.COLOR_YELLOW
    border: int = curses.COLOR_YELLOW
    border_active: int = curses.COLOR_WHITE
    dir_color: int = curses.COLOR_YELLOW
    
    def _apply_256_colors(self):
        self.primary = 214     # Orange/Amber
        self.secondary = 208   # Dark amber
        self.border = 172      # Brown-amber


# Default themes registry
THEMES: dict[str, type[Theme]] = {
    "default": Theme,
    "matrix": MatrixTheme,
    "cyberpunk": CyberpunkTheme,
    "retro": RetroTheme,
}


class ColorManager:
    """
    Manages curses color initialization and theme application.
    
    Usage:
        colors = ColorManager(stdscr)
        colors.set_theme("matrix")
        
        stdscr.addstr("Success!", colors.attr(ColorPair.SUCCESS))
    """
    
    _instance: ClassVar[ColorManager | None] = None
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.theme: Theme = Theme(name="default", description="Default theme")
        self._initialized = False
        
        ColorManager._instance = self
    
    @classmethod
    def get(cls) -> ColorManager:
        """Get singleton instance."""
        if cls._instance is None:
            raise RuntimeError("ColorManager not initialized. Call ColorManager(stdscr) first.")
        return cls._instance
    
    def init_colors(self) -> bool:
        """
        Initialize curses colors.
        
        Returns:
            True if colors are supported, False otherwise.
        """
        if not curses.has_colors():
            return False
        
        curses.start_color()
        curses.use_default_colors()
        
        self._initialized = True
        self._setup_color_pairs()
        
        return True
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Apply a theme by name.
        
        Args:
            theme_name: Name of theme from THEMES registry.
            
        Returns:
            True if theme was applied, False if not found.
        """
        if theme_name not in THEMES:
            return False
        
        use_256 = curses.COLORS >= 256
        self.theme = THEMES[theme_name](
            name=theme_name,
            description=THEMES[theme_name].__doc__ or "",
            use_256=use_256,
        )
        
        if self._initialized:
            self._setup_color_pairs()
        
        return True
    
    def _setup_color_pairs(self):
        """Setup all color pairs based on current theme."""
        t = self.theme
        bg = -1  # Use terminal default background
        
        # Basic pairs
        curses.init_pair(ColorPair.DEFAULT, t.fg, bg)
        curses.init_pair(ColorPair.PROMPT_USER, t.success, bg)
        curses.init_pair(ColorPair.PROMPT_HOST, t.primary, bg)
        curses.init_pair(ColorPair.PROMPT_PATH, t.info, bg)
        
        # Status colors
        curses.init_pair(ColorPair.SUCCESS, t.success, bg)
        curses.init_pair(ColorPair.ERROR, t.error, bg)
        curses.init_pair(ColorPair.WARNING, t.warning, bg)
        curses.init_pair(ColorPair.INFO, t.info, bg)
        
        # File types
        curses.init_pair(ColorPair.DIRECTORY, t.dir_color, bg)
        curses.init_pair(ColorPair.FILE, t.fg, bg)
        curses.init_pair(ColorPair.EXECUTABLE, t.exec_color, bg)
        curses.init_pair(ColorPair.SYMLINK, t.link_color, bg)
        curses.init_pair(ColorPair.HIDDEN, curses.COLOR_WHITE, bg)
        
        # UI elements - Header with better contrast
        # Use black background with bright foreground for readability
        if curses.COLORS >= 256:
            # 256 color mode - use dark gray background
            curses.init_pair(ColorPair.HEADER, 15, 235)  # Bright white on dark gray
            curses.init_pair(ColorPair.HEADER_ACCENT, t.warning, 235)  # Yellow accent
        else:
            # 8 color fallback - white on black with bold
            curses.init_pair(ColorPair.HEADER, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(ColorPair.HEADER_ACCENT, t.warning, curses.COLOR_BLACK)
        
        curses.init_pair(ColorPair.BORDER, t.border, bg)
        curses.init_pair(ColorPair.BORDER_ACTIVE, t.border_active, bg)
        
        # Tasks
        curses.init_pair(ColorPair.TASK_DONE, t.success, bg)
        curses.init_pair(ColorPair.TASK_ACTIVE, t.warning, bg)
        curses.init_pair(ColorPair.TASK_PENDING, curses.COLOR_WHITE, bg)
        
        # Log
        curses.init_pair(ColorPair.LOG_TIME, curses.COLOR_WHITE, bg)
        curses.init_pair(ColorPair.LOG_SUCCESS, t.success, bg)
        curses.init_pair(ColorPair.LOG_ERROR, t.error, bg)
        
        # Misc
        curses.init_pair(ColorPair.HINT, t.info, bg)
        curses.init_pair(ColorPair.SCORE, t.warning, bg)
        curses.init_pair(ColorPair.TITLE, t.primary, bg)
        curses.init_pair(ColorPair.SUBTITLE, t.secondary, bg)
        
        # Menu
        curses.init_pair(ColorPair.MENU_NORMAL, t.fg, bg)
        curses.init_pair(ColorPair.MENU_SELECTED, t.bg, t.primary)
        curses.init_pair(ColorPair.MENU_DISABLED, curses.COLOR_WHITE, bg)
        
        # System stats
        curses.init_pair(ColorPair.SYSTEM_CPU, t.success, bg)
        curses.init_pair(ColorPair.SYSTEM_RAM, t.info, bg)
    
    def attr(self, pair: ColorPair, bold: bool = False, dim: bool = False) -> int:
        """
        Get curses attribute for a color pair.
        
        Args:
            pair: ColorPair to use
            bold: Add bold attribute
            dim: Add dim attribute
            
        Returns:
            Curses attribute integer
        """
        attr = curses.color_pair(pair)
        if bold:
            attr |= curses.A_BOLD
        if dim:
            attr |= curses.A_DIM
        return attr
    
    def success(self, bold: bool = True) -> int:
        """Shortcut for success color."""
        return self.attr(ColorPair.SUCCESS, bold=bold)
    
    def error(self, bold: bool = True) -> int:
        """Shortcut for error color."""
        return self.attr(ColorPair.ERROR, bold=bold)
    
    def warning(self, bold: bool = False) -> int:
        """Shortcut for warning color."""
        return self.attr(ColorPair.WARNING, bold=bold)
    
    def info(self, bold: bool = False) -> int:
        """Shortcut for info color."""
        return self.attr(ColorPair.INFO, bold=bold)


# Box drawing characters (ASCII fallback available)
@dataclass
class BoxChars:
    """Box drawing character sets."""
    
    # Unicode (default)
    TL: str = "┌"  # Top-left
    TR: str = "┐"  # Top-right
    BL: str = "└"  # Bottom-left
    BR: str = "┘"  # Bottom-right
    H: str = "─"   # Horizontal
    V: str = "│"   # Vertical
    LT: str = "├"  # Left-T
    RT: str = "┤"  # Right-T
    TT: str = "┬"  # Top-T
    BT: str = "┴"  # Bottom-T
    X: str = "┼"   # Cross
    
    # Double line variants
    DTL: str = "╔"
    DTR: str = "╗"
    DBL: str = "╚"
    DBR: str = "╝"
    DH: str = "═"
    DV: str = "║"


# ASCII fallback
ASCII_BOX = BoxChars(
    TL="+", TR="+", BL="+", BR="+",
    H="-", V="|",
    LT="+", RT="+", TT="+", BT="+", X="+",
    DTL="+", DTR="+", DBL="+", DBR="+",
    DH="=", DV="|",
)

# Unicode box (default)
UNICODE_BOX = BoxChars()


def get_box_chars(use_unicode: bool = True) -> BoxChars:
    """Get appropriate box drawing characters."""
    return UNICODE_BOX if use_unicode else ASCII_BOX
