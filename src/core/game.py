"""
Linux Command Quest - Main Game
================================

Main game loop and state management.
"""

from __future__ import annotations

import curses
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class GameState(Enum):
    """Game states."""
    BOOT = auto()
    MENU = auto()
    MISSION_SELECT = auto()
    PLAYING = auto()
    PAUSED = auto()          # ESC ile pause menü
    MISSION_COMPLETE = auto()
    GAME_OVER = auto()
    STATS_VIEW = auto()      # F2 - İstatistik görüntüleme
    ACHIEVEMENTS_VIEW = auto()  # F3 - Başarı galerisi
    SETTINGS = auto()        # Ayarlar menüsü
    PROFILE_EDIT = auto()    # F4 - Profil düzenleme
    HELP_VIEW = auto()       # F1 - Akıllı yardım sistemi
    SHORTCUTS_VIEW = auto()  # Kısayollar görüntüleme


@dataclass
class GameConfig:
    """Game configuration."""
    
    username: str = "user"
    hostname: str = "quest"   # Makine adı
    theme: str = "matrix"
    sound_enabled: bool = True
    hints_per_mission: int = 3
    show_boot_animation: bool = True
    profile_name: str = "default"  # Profil adı


class Game:
    """
    Main game controller.
    
    Manages game state, UI, and coordinates between components.
    """
    
    VERSION = "3.7.0"
    
    def __init__(self, stdscr, config: GameConfig | None = None):
        self.stdscr = stdscr
        self.config = config or GameConfig()
        
        # Initialize core systems
        from .colors import ColorManager
        from .audio import AudioManager, AudioConfig
        from .achievements import AchievementManager, GameStatistics
        from ..simulation.filesystem import VirtualFileSystem
        from ..simulation.shell import Shell
        from ..missions.missions import MissionLoader, TaskValidator, PlayerProgress
        
        # Terminal and colors
        self.colors = ColorManager(stdscr)
        self.colors.init_colors()
        self.colors.set_theme(self.config.theme)
        
        # Audio system (optional - fails silently if not available)
        audio_config = AudioConfig(enabled=self.config.sound_enabled)
        self.audio = AudioManager(audio_config)
        
        # Game systems
        self.fs = VirtualFileSystem(self.config.username)
        self.shell = Shell(self.fs)
        self.mission_loader = MissionLoader()
        self.progress = PlayerProgress()
        self.validator = TaskValidator(self.fs)
        
        # Achievement and statistics system
        self.achievements = AchievementManager()
        self.stats = GameStatistics()
        
        # Input buffer
        self.input_buffer = []
        self.input_cursor = 0
        self.history_idx = 0
        
        # State
        self.state = GameState.BOOT
        self._previous_state = GameState.MENU  # Overlay'lerden dönüş için
        self.running = True
        self.current_mission = None
        self.current_task_idx = 0
        self.hints_remaining = self.config.hints_per_mission
        self.score = 0
        
        # UI state
        self.terminal_lines: list[tuple[str, int]] = []
        self.log_lines: list[tuple[str, int]] = []
        self.menu_selection = 0
        self.mission_selection = 0
        self.pause_selection = 0  # Pause menü seçimi
        
        # Achievement notification queue
        self._achievement_display_time = 0
        self._current_achievement_notification = None
        
        # Save system
        self._save_dir = Path.home() / ".linux-quest" / "saves"
        self._save_dir.mkdir(parents=True, exist_ok=True)
        
        # Load progress if exists
        self._load_progress()
        
        # Start session tracking
        self.stats.start_session()
        
        # Screen setup
        curses.curs_set(1)
        self.stdscr.nodelay(False)
        self.stdscr.timeout(100)  # 100ms for less CPU usage
        
        # CRITICAL: Reduce ESC delay (default is 1000ms!)
        try:
            curses.set_escdelay(25)  # 25ms delay for ESC key
        except AttributeError:
            pass  # Not available on all systems (e.g., Windows)
        
        # CRITICAL: Disable automatic refresh for double buffering
        self.stdscr.scrollok(False)
        self.stdscr.idlok(False)
        self.stdscr.leaveok(False)
        
        # Get screen size
        self.rows, self.cols = self.stdscr.getmaxyx()
        
        # Track if redraw is needed
        self._needs_redraw = True
        self._last_input_len = 0
    
    def run(self):
        """Main game loop."""
        try:
            if self.config.show_boot_animation:
                self._boot_sequence()
            
            self.state = GameState.MENU
            
            while self.running:
                self._handle_input()
                self._update()
                self._render()
                
        except KeyboardInterrupt:
            pass
        finally:
            # Cleanup - save stats and progress
            self._cleanup()
    
    def _cleanup(self):
        """Clean up before exit - save progress and stats."""
        try:
            self.stats.end_session()
            self._save_progress()
        except Exception:
            pass  # Don't crash on cleanup
    
    def _boot_sequence(self):
        """Show boot animation."""
        from .colors import ColorPair
        from .audio import SoundEffect
        
        # Play boot sound
        self.audio.play(SoundEffect.BOOT)
        
        boot_lines = [
            "",
            "  ██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗",
            "  ██║     ██║████╗  ██║██║   ██║╚██╗██╔╝",
            "  ██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝ ",
            "  ██║     ██║██║╚██╗██║██║   ██║ ██╔██╗ ",
            "  ███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗",
            "  ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝",
            "",
            "     ██████╗ ██╗   ██╗███████╗███████╗████████╗",
            "    ██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝",
            "    ██║   ██║██║   ██║█████╗  ███████╗   ██║   ",
            "    ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   ",
            "    ╚██████╔╝╚██████╔╝███████╗███████║   ██║   ",
            "     ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   ",
            "",
            f"          COMMAND QUEST v{self.VERSION}",
            "",
        ]
        
        self.stdscr.clear()
        start_row = max(0, (self.rows - len(boot_lines) - 8) // 2)
        
        # Draw logo with animation
        for i, line in enumerate(boot_lines):
            if start_row + i >= self.rows - 1:
                break
            
            col = max(0, (self.cols - len(line)) // 2)
            color = self.colors.attr(ColorPair.SUCCESS) if i < 7 else self.colors.attr(ColorPair.INFO)
            if "COMMAND QUEST" in line:
                color = self.colors.attr(ColorPair.WARNING, bold=True)
            
            try:
                self.stdscr.addstr(start_row + i, col, line, color)
            except curses.error:
                pass
            
            self.stdscr.refresh()
            time.sleep(0.02)
        
        # Boot messages
        boot_msgs = [
            ("[BOOT] Sistem başlatılıyor...", ColorPair.DEFAULT),
            ("[OK] Sanal dosya sistemi yüklendi", ColorPair.SUCCESS),
            ("[OK] Komut yorumlayıcı hazır", ColorPair.SUCCESS),
            ("[OK] Görev sistemi aktif", ColorPair.SUCCESS),
            ("[OK] Terminal başlatıldı", ColorPair.SUCCESS),
            ("", None),
            ("Devam etmek için bir tuşa basın...", ColorPair.WARNING),
        ]
        
        msg_row = start_row + len(boot_lines) + 1
        for msg, color in boot_msgs:
            if msg_row >= self.rows - 1:
                break
            try:
                col = max(0, (self.cols - len(msg)) // 2)
                attr = self.colors.attr(color) if color else 0
                self.stdscr.addstr(msg_row, col, msg, attr)
            except curses.error:
                pass
            msg_row += 1
            self.stdscr.refresh()
            time.sleep(0.15)
        
        # Wait for keypress
        self.stdscr.timeout(-1)
        self.stdscr.getch()
        self.stdscr.timeout(50)
    
    def _handle_input(self):
        """Handle keyboard input based on current state."""
        try:
            key = self.stdscr.getch()
        except curses.error:
            return
        
        if key == -1:
            return
        
        # Global shortcuts
        if key == 3:  # Ctrl+C
            self.running = False
            return
        
        if key == 17:  # Ctrl+Q
            if self.state == GameState.PLAYING:
                self.state = GameState.MENU
                return
            else:
                self.running = False
                return
        
        # State-specific handling
        if self.state == GameState.MENU:
            self._handle_menu_input(key)
        elif self.state == GameState.MISSION_SELECT:
            self._handle_mission_select_input(key)
        elif self.state == GameState.PLAYING:
            self._handle_game_input(key)
        elif self.state == GameState.PAUSED:
            self._handle_pause_input(key)
        elif self.state == GameState.MISSION_COMPLETE:
            self._handle_complete_input(key)
        elif self.state == GameState.STATS_VIEW:
            self._handle_stats_input(key)
        elif self.state == GameState.ACHIEVEMENTS_VIEW:
            self._handle_achievements_input(key)
        elif self.state == GameState.SETTINGS:
            self._handle_settings_input(key)
        elif self.state == GameState.PROFILE_EDIT:
            self._handle_profile_input(key)
        elif self.state == GameState.HELP_VIEW:
            self._handle_help_input(key)
        elif self.state == GameState.SHORTCUTS_VIEW:
            self._handle_shortcuts_input(key)
    
    def _handle_menu_input(self, key):
        """Handle main menu input."""
        from .audio import SoundEffect
        
        # F-key shortcuts (work from menu too)
        if key == curses.KEY_F2:
            self._previous_state = self.state
            self.state = GameState.STATS_VIEW
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        elif key == curses.KEY_F3:
            self._previous_state = self.state
            self.state = GameState.ACHIEVEMENTS_VIEW
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        elif key == curses.KEY_F4:
            self._previous_state = self.state
            self.state = GameState.PROFILE_EDIT
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # Dynamic menu based on save state
        if self._has_save():
            menu_items = ["Devam Et", "Yeni Oyun", "Görev Seç", "Ayarlar", "Çıkış"]
        else:
            menu_items = ["Yeni Oyun", "Görev Seç", "Ayarlar", "Çıkış"]
        
        if key == curses.KEY_UP:
            self.menu_selection = (self.menu_selection - 1) % len(menu_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key == curses.KEY_DOWN:
            self.menu_selection = (self.menu_selection + 1) % len(menu_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key in (10, curses.KEY_ENTER):  # Enter
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            
            selected = menu_items[self.menu_selection]
            
            if selected == "Devam Et":
                self._continue_game()
            elif selected == "Yeni Oyun":
                # Start first mission
                self.current_mission = self.mission_loader.get_mission("basics")
                if self.current_mission:
                    self._start_mission()
            elif selected == "Görev Seç":
                self.state = GameState.MISSION_SELECT
                self.mission_selection = 0
            elif selected == "Ayarlar":
                self._previous_state = self.state
                self.state = GameState.SETTINGS
                self.settings_selection = 0
            elif selected == "Çıkış":
                self._save_progress()
                self.running = False
        elif key == ord('q'):
            self._save_progress()
            self.running = False
    
    def _handle_mission_select_input(self, key):
        """Handle mission selection input."""
        from .audio import SoundEffect
        
        missions = self.mission_loader.get_all_missions()
        
        if key == curses.KEY_UP:
            self.mission_selection = (self.mission_selection - 1) % len(missions)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key == curses.KEY_DOWN:
            self.mission_selection = (self.mission_selection + 1) % len(missions)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key in (10, curses.KEY_ENTER):
            self.current_mission = missions[self.mission_selection]
            self._start_mission()
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
        elif key == ord('q') or key == 27:  # q or ESC
            self.state = GameState.MENU
            self._needs_redraw = True
    
    def _handle_game_input(self, key):
        """Handle in-game input."""
        from .audio import SoundEffect
        
        # ESC - Pause menu
        if key == 27:
            self.state = GameState.PAUSED
            self.pause_selection = 0
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # F1 - Smart Help
        if key == curses.KEY_F1:
            self._previous_state = self.state
            self.help_hint_level = 0  # Start with first hint
            self.state = GameState.HELP_VIEW
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # F1 - Smart Help
        if key == curses.KEY_F1:
            self._previous_state = self.state
            self.state = GameState.HELP_VIEW
            self.help_hint_level = 0  # İpucu seviyesi (0, 1, 2)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # F2 - Statistics view
        if key == curses.KEY_F2:
            self._previous_state = self.state
            self.state = GameState.STATS_VIEW
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # F3 - Achievements view
        if key == curses.KEY_F3:
            self._previous_state = self.state
            self.state = GameState.ACHIEVEMENTS_VIEW
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # Ctrl+H - Hint (quick hint in terminal)
        if key == 8:
            self._show_hint()
            return
        
        # Ctrl+R - Reset mission
        if key == 18:
            self._reset_mission()
            return
        
        # Arrow keys for history
        if key == curses.KEY_UP:
            self._history_prev()
            return
        elif key == curses.KEY_DOWN:
            self._history_next()
            return
        
        # Left/Right for cursor - only update input line
        if key == curses.KEY_LEFT:
            if self.input_cursor > 0:
                self.input_cursor -= 1
            return
        elif key == curses.KEY_RIGHT:
            if self.input_cursor < len(self.input_buffer):
                self.input_cursor += 1
            return
        
        # Home/End
        if key == curses.KEY_HOME:
            self.input_cursor = 0
            return
        elif key == curses.KEY_END:
            self.input_cursor = len(self.input_buffer)
            return
        
        # Backspace
        if key in (127, curses.KEY_BACKSPACE):
            if self.input_cursor > 0:
                self.input_buffer.pop(self.input_cursor - 1)
                self.input_cursor -= 1
                self._needs_redraw = True
            return
        
        # Delete
        if key == curses.KEY_DC:
            if self.input_cursor < len(self.input_buffer):
                self.input_buffer.pop(self.input_cursor)
                self._needs_redraw = True
            return
        
        # Enter - execute command
        if key in (10, curses.KEY_ENTER):
            self._execute_command()
            return
        
        # Tab - autocomplete
        if key == 9:
            self._autocomplete()
            return
        
        # Printable character
        if 32 <= key < 127:
            self.input_buffer.insert(self.input_cursor, chr(key))
            self.input_cursor += 1
            self._needs_redraw = True
    
    def _handle_complete_input(self, key):
        """Handle mission complete screen input."""
        from .audio import SoundEffect
        
        # Initialize complete menu selection if not exists
        if not hasattr(self, 'complete_selection'):
            self.complete_selection = 0
        
        # Get available options
        next_mission = self._get_next_mission()
        
        if next_mission:
            complete_items = ["Sonraki Görev", "Görev Seçimine Dön", "Ana Menü"]
        else:
            complete_items = ["Görev Seçimine Dön", "Ana Menü"]
        
        if key == curses.KEY_UP:
            self.complete_selection = (self.complete_selection - 1) % len(complete_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key == curses.KEY_DOWN:
            self.complete_selection = (self.complete_selection + 1) % len(complete_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key in (10, curses.KEY_ENTER, ord(' ')):
            self.audio.play(SoundEffect.MENU_SELECT)
            
            selected = complete_items[self.complete_selection]
            
            if selected == "Sonraki Görev" and next_mission:
                self.current_mission = next_mission
                self.complete_selection = 0
                self._start_mission()
            elif selected == "Görev Seçimine Dön":
                self.complete_selection = 0
                self.state = GameState.MISSION_SELECT
                self._needs_redraw = True
            elif selected == "Ana Menü":
                self.complete_selection = 0
                self.state = GameState.MENU
                self._needs_redraw = True
    
    def _get_next_mission(self):
        """Get the next available mission after current one."""
        if not self.current_mission:
            return None
        
        # Get missions that this one unlocks
        unlocks = self.current_mission.unlocks
        
        for mission_id in unlocks:
            mission = self.mission_loader.get_mission(mission_id)
            if mission and mission.id not in self.progress.completed_missions:
                return mission
        
        # If no unlocks, try to find any available mission
        available = self.mission_loader.get_available_missions(self.progress.completed_missions)
        
        for mission in available:
            if mission.id != self.current_mission.id:
                return mission
        
        return None
    
    def _handle_pause_input(self, key):
        """Handle pause menu input."""
        from .audio import SoundEffect
        
        pause_items = ["Devam Et", "Görevi Yeniden Başlat", "Ana Menüye Dön", "Oyundan Çık"]
        
        if key == 27:  # ESC again - resume
            self.state = GameState.PLAYING
            self._needs_redraw = True
            return
        
        if key == curses.KEY_UP:
            self.pause_selection = (self.pause_selection - 1) % len(pause_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key == curses.KEY_DOWN:
            self.pause_selection = (self.pause_selection + 1) % len(pause_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key in (10, curses.KEY_ENTER):
            self.audio.play(SoundEffect.MENU_SELECT)
            
            if self.pause_selection == 0:  # Devam Et
                self.state = GameState.PLAYING
                self._needs_redraw = True
            elif self.pause_selection == 1:  # Yeniden Başlat
                self._reset_mission()
                self.state = GameState.PLAYING
                self._needs_redraw = True
            elif self.pause_selection == 2:  # Ana Menüye Dön
                self._save_progress()  # Kaydet
                self.state = GameState.MENU
                self._needs_redraw = True
            elif self.pause_selection == 3:  # Oyundan Çık
                self._save_progress()  # Kaydet
                self.running = False
    
    def _start_mission(self):
        """Start a mission."""
        from .audio import SoundEffect
        
        if not self.current_mission:
            return
        
        self.state = GameState.PLAYING
        self.current_task_idx = 0
        self.hints_remaining = self.config.hints_per_mission
        self.score = 0  # Reset score for this mission
        
        # Reset filesystem
        self.fs.reset()
        self.fs.save_checkpoint()
        
        # Clear terminal
        self.terminal_lines = []
        self.log_lines = []
        self.input_buffer = []
        self.input_cursor = 0
        
        # Start mission tracking
        self.stats.start_mission()
        
        # Play mission start sound
        self.audio.play(SoundEffect.MISSION_START)
        
        # Add mission start message
        self._add_terminal_line(f"╔{'═' * 50}╗", "info")
        self._add_terminal_line(f"║ MİSYON: {self.current_mission.name:^40} ║", "title")
        self._add_terminal_line(f"╠{'═' * 50}╣", "info")
        self._add_terminal_line(f"║ {self.current_mission.description[:48]:^48} ║", "default")
        self._add_terminal_line(f"╚{'═' * 50}╝", "info")
        self._add_terminal_line("", "default")
        
        self._add_log(f"Misyon başlatıldı: {self.current_mission.name}")
        self._needs_redraw = True
        
        # Auto-save when starting mission
        self._save_progress()
    
    def _reset_mission(self):
        """Reset current mission."""
        from .audio import SoundEffect
        
        if self.current_mission:
            self.fs.restore_checkpoint()
            self.current_task_idx = 0
            self.terminal_lines = []
            self._add_terminal_line("⟳ Görev sıfırlandı", "warning")
            self._add_terminal_line("", "default")
            self._add_log("Görev sıfırlandı")
            self._needs_redraw = True
            self.audio.play(SoundEffect.NOTIFICATION)
    
    def _execute_command(self):
        """Execute the current command."""
        from .audio import SoundEffect
        
        cmd = "".join(self.input_buffer).strip()
        self.input_buffer = []
        self.input_cursor = 0
        
        if not cmd:
            return
        
        # Play enter sound
        self.audio.play(SoundEffect.ENTER)
        
        # Show command in terminal
        prompt = self.shell.get_prompt()
        self._add_terminal_line(f"{prompt}{cmd}", "default")
        
        # Execute
        result = self.shell.execute(cmd)
        
        # Track statistics
        self.stats.increment_command(cmd)
        self.stats.visit_directory(self.fs.cwd)
        
        # Show output
        if result.output:
            for line in result.output.split("\n"):
                self._add_terminal_line(line, "default")
        
        if result.error:
            for line in result.error.split("\n"):
                self._add_terminal_line(line, "error")
            self.audio.play(SoundEffect.ERROR)
            self.stats.increment_error()
        
        if result.clear_screen:
            self.terminal_lines = []
        
        # Check achievements after command
        self.achievements.check_command(cmd, self.stats)
        self._check_achievement_notifications()
        
        # Check task completion
        if self.current_mission and self.current_task_idx < len(self.current_mission.tasks):
            task = self.current_mission.tasks[self.current_task_idx]
            success, message = self.validator.validate(task, cmd)
            
            if success:
                self.score += task.points
                self._add_terminal_line("", "default")
                self._add_terminal_line(f"  ✓ DOĞRU! +{task.points} puan", "success")
                if message:
                    self._add_terminal_line(f"  {message}", "info")
                self._add_terminal_line("", "default")
                
                self._add_log(f"Görev tamamlandı: {task.description[:30]}")
                
                # Play success sound
                self.audio.play(SoundEffect.SUCCESS)
                
                self.current_task_idx += 1
                
                # Check mission complete
                if self.current_task_idx >= len(self.current_mission.tasks):
                    self._mission_complete()
        
        # Reset history index
        self.history_idx = len(self.shell.history)
        self._needs_redraw = True
    
    def _check_achievement_notifications(self):
        """Check and display any pending achievement notifications."""
        from .audio import SoundEffect
        
        pending = self.achievements.get_pending_notifications()
        for achievement in pending:
            self._add_terminal_line("", "default")
            self._add_terminal_line(f"  🏆 BAŞARI AÇILDI: {achievement.icon} {achievement.name}", "success")
            self._add_terminal_line(f"     {achievement.description}", "info")
            self._add_terminal_line(f"     +{achievement.points} başarı puanı", "warning")
            self._add_terminal_line("", "default")
            self.audio.play(SoundEffect.MISSION_COMPLETE)
        
        # Reset history index
        self.history_idx = len(self.shell.history)
        self._needs_redraw = True
    
    def _mission_complete(self):
        """Handle mission completion."""
        from .audio import SoundEffect
        
        # Complete mission in stats and get results
        mission_time, was_perfect = self.stats.complete_mission(self.current_mission.id)
        
        self._add_terminal_line("", "default")
        self._add_terminal_line("🎉 " + "═" * 40 + " 🎉", "success")
        self._add_terminal_line("       MİSYON TAMAMLANDI!", "success")
        self._add_terminal_line("🎉 " + "═" * 40 + " 🎉", "success")
        
        # Show stats
        time_str = f"{int(mission_time)}s" if mission_time < 60 else f"{int(mission_time//60)}m {int(mission_time%60)}s"
        self._add_terminal_line(f"  ⏱️ Süre: {time_str}", "info")
        if was_perfect:
            self._add_terminal_line("  ✨ KUSURSUZ! Hatasız ve ipucusuz tamamladın!", "success")
        
        if self.current_mission.completion_message:
            for line in self.current_mission.completion_message.split("\n"):
                self._add_terminal_line(f"  {line}", "info")
        
        self._add_log(f"MİSYON TAMAMLANDI: {self.current_mission.name}")
        
        # Play mission complete sound
        self.audio.play(SoundEffect.MISSION_COMPLETE)
        
        # Check mission-related achievements
        self.achievements.check_mission_complete(mission_time, was_perfect, self.stats)
        self._check_achievement_notifications()
        
        # Mark as completed
        if self.current_mission.id not in self.progress.completed_missions:
            self.progress.completed_missions.append(self.current_mission.id)
        
        self.progress.total_score += self.score
        self.state = GameState.MISSION_COMPLETE
        self._needs_redraw = True
        
        # Auto-save progress
        self._save_progress()
    
    def _show_hint(self):
        """Show hint for current task."""
        from .audio import SoundEffect
        
        if self.hints_remaining <= 0:
            self._add_terminal_line("  ⚠ İpucu hakkın kalmadı!", "warning")
            self._needs_redraw = True
            self.audio.play(SoundEffect.WARNING)
            return
        
        if not self.current_mission or self.current_task_idx >= len(self.current_mission.tasks):
            return
        
        task = self.current_mission.tasks[self.current_task_idx]
        if task.hint:
            self.hints_remaining -= 1
            self.stats.use_hint()  # Track hint usage
            self._add_terminal_line("", "default")
            self._add_terminal_line(f"  💡 İPUCU: {task.hint}", "hint")
            self._add_terminal_line(f"     (Kalan ipucu: {self.hints_remaining})", "info")
            self._add_terminal_line("", "default")
            self._add_log(f"İpucu kullanıldı ({self.hints_remaining} kaldı)")
            self._needs_redraw = True
            self.audio.play(SoundEffect.HINT)
    
    def _autocomplete(self):
        """Handle tab completion."""
        partial = "".join(self.input_buffer)
        
        if not partial:
            return
        
        # Split into command and arguments
        parts = partial.split()
        
        if not parts:
            return
        
        # Get completions
        completions = self.shell.complete(partial)
        
        if not completions:
            return
        
        if len(completions) == 1:
            # Single completion - apply it
            completion = completions[0]
            
            # If completing first word (command), replace whole thing
            if len(parts) == 1 and not partial.endswith(" "):
                self.input_buffer = list(completion + " ")
            else:
                # Completing an argument - keep command part
                # Find where the last word starts
                last_space = partial.rfind(" ")
                if last_space >= 0:
                    prefix = partial[:last_space + 1]
                    # Get just the completed filename/path
                    if "/" in completion:
                        # It's a path completion from shell
                        self.input_buffer = list(prefix + completion + " ")
                    else:
                        self.input_buffer = list(prefix + completion + " ")
                else:
                    self.input_buffer = list(completion + " ")
            
            self.input_cursor = len(self.input_buffer)
        else:
            # Multiple completions - show them and find common prefix
            self._add_terminal_line("", "default")
            self._add_terminal_line("  " + "  ".join(completions[:10]), "info")
            if len(completions) > 10:
                self._add_terminal_line(f"  ... ve {len(completions) - 10} daha", "info")
            
            # Auto-complete common prefix
            common = completions[0]
            for c in completions[1:]:
                while not c.startswith(common):
                    common = common[:-1]
                    if not common:
                        break
            
            if common and len(common) > len(parts[-1] if parts else ""):
                last_space = partial.rfind(" ")
                if last_space >= 0:
                    self.input_buffer = list(partial[:last_space + 1] + common)
                else:
                    self.input_buffer = list(common)
                self.input_cursor = len(self.input_buffer)
        
        self._needs_redraw = True
    
    def _history_prev(self):
        """Navigate to previous command in history."""
        history = self.shell.history
        if not history:
            return
        
        if self.history_idx > 0:
            self.history_idx -= 1
            self.input_buffer = list(history[self.history_idx])
            self.input_cursor = len(self.input_buffer)
            self._needs_redraw = True
    
    def _history_next(self):
        """Navigate to next command in history."""
        history = self.shell.history
        
        if self.history_idx < len(history) - 1:
            self.history_idx += 1
            self.input_buffer = list(history[self.history_idx])
            self.input_cursor = len(self.input_buffer)
            self._needs_redraw = True
        elif self.history_idx == len(history) - 1:
            self.history_idx = len(history)
            self.input_buffer = []
            self.input_cursor = 0
            self._needs_redraw = True
    
    def _add_terminal_line(self, text: str, style: str = "default"):
        """Add line to terminal output."""
        from .colors import ColorPair
        
        style_map = {
            "default": 0,
            "success": self.colors.attr(ColorPair.SUCCESS, bold=True),
            "error": self.colors.attr(ColorPair.ERROR),
            "warning": self.colors.attr(ColorPair.WARNING),
            "info": self.colors.attr(ColorPair.INFO),
            "hint": self.colors.attr(ColorPair.HINT),
            "title": self.colors.attr(ColorPair.TITLE, bold=True),
        }
        
        attr = style_map.get(style, 0)
        self.terminal_lines.append((text, attr))
        
        # Limit lines
        max_lines = 500
        if len(self.terminal_lines) > max_lines:
            self.terminal_lines = self.terminal_lines[-max_lines:]
    
    def _add_log(self, message: str):
        """Add entry to system log."""
        from .colors import ColorPair
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_lines.append((f"[{timestamp}] {message}", 
                               self.colors.attr(ColorPair.LOG_TIME)))
        
        # Limit log
        if len(self.log_lines) > 100:
            self.log_lines = self.log_lines[-100:]
    
    def _get_save_path(self) -> Path:
        """Get save file path for current profile."""
        return self._save_dir / f"{self.config.profile_name}.json"
    
    def _save_progress(self):
        """Save game progress to file."""
        # End session to update play time
        self.stats.end_session()
        self.stats.start_session()  # Restart for continued play
        
        save_data = {
            "profile_name": self.config.profile_name,
            "username": self.config.username,
            "hostname": self.config.hostname,
            "progress": self.progress.to_dict(),
            "current_mission_id": self.current_mission.id if self.current_mission else None,
            "current_task_idx": self.current_task_idx,
            "score": self.score,
            "theme": self.config.theme,
            "last_played": datetime.now().isoformat(),
            "statistics": self.stats.to_dict(),
            "achievements": self.achievements.to_dict(),
        }
        
        try:
            with open(self._get_save_path(), 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Fail silently
    
    def _load_progress(self):
        """Load game progress from file."""
        from .achievements import GameStatistics
        
        save_path = self._get_save_path()
        
        if not save_path.exists():
            return
        
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Restore progress
            from ..missions.missions import PlayerProgress
            self.progress = PlayerProgress.from_dict(save_data.get("progress", {}))
            
            # Store last mission for "continue" feature
            self._last_mission_id = save_data.get("current_mission_id")
            self._last_task_idx = save_data.get("current_task_idx", 0)
            self._last_score = save_data.get("score", 0)
            
            # Load statistics
            if "statistics" in save_data:
                self.stats = GameStatistics.from_dict(save_data["statistics"])
            
            # Load achievements
            if "achievements" in save_data:
                self.achievements.from_dict(save_data["achievements"])
            
            # Load profile settings
            if "username" in save_data:
                self.config.username = save_data["username"]
                self.fs.username = save_data["username"]
                self.fs.home = f"/home/{save_data['username']}"
            if "hostname" in save_data:
                self.config.hostname = save_data["hostname"]
                self.fs.hostname = save_data["hostname"]
            
        except Exception:
            pass  # Start fresh if load fails
    
    def _has_save(self) -> bool:
        """Check if there's a save to continue from."""
        return hasattr(self, '_last_mission_id') and self._last_mission_id is not None
    
    def _continue_game(self):
        """Continue from last saved position."""
        if not self._has_save():
            return
        
        self.current_mission = self.mission_loader.get_mission(self._last_mission_id)
        if self.current_mission:
            self.current_task_idx = self._last_task_idx
            self.score = self._last_score
            self.state = GameState.PLAYING
            self.hints_remaining = self.config.hints_per_mission
            
            # Reset filesystem
            self.fs.reset()
            self.fs.save_checkpoint()
            
            # Clear terminal
            self.terminal_lines = []
            self.log_lines = []
            self.input_buffer = []
            self.input_cursor = 0
            
            # Show continue message
            self._add_terminal_line(f"╔{'═' * 50}╗", "info")
            self._add_terminal_line(f"║ {'DEVAM EDİLİYOR':^48} ║", "title")
            self._add_terminal_line(f"║ MİSYON: {self.current_mission.name:^39} ║", "info")
            self._add_terminal_line(f"╚{'═' * 50}╝", "info")
            self._add_terminal_line("", "default")
            
            self._add_log(f"Oyun devam ediyor: {self.current_mission.name}")
            self._needs_redraw = True
            
            from .audio import SoundEffect
            self.audio.play(SoundEffect.MISSION_START)
    
    def _update(self):
        """Update game state."""
        # Check for screen resize
        new_rows, new_cols = self.stdscr.getmaxyx()
        if new_rows != self.rows or new_cols != self.cols:
            self.rows, self.cols = new_rows, new_cols
            self._needs_redraw = True
        
        # Check if input changed (for cursor update)
        current_input_len = len(self.input_buffer)
        if current_input_len != self._last_input_len:
            self._last_input_len = current_input_len
    
    def _render(self):
        """Render current state with double buffering."""
        if not self._needs_redraw:
            # Only update cursor position for input
            if self.state == GameState.PLAYING:
                self._render_input_line(self.rows - 2)
                self.stdscr.refresh()
            return
        
        # Use erase instead of clear (no flicker)
        self.stdscr.erase()
        
        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.MISSION_SELECT:
            self._render_mission_select()
        elif self.state == GameState.PLAYING:
            self._render_game()
        elif self.state == GameState.PAUSED:
            self._render_game()  # Show game in background
            self._render_pause_overlay()  # Overlay pause menu
        elif self.state == GameState.MISSION_COMPLETE:
            self._render_game()  # Keep showing game screen
            self._render_complete_overlay()  # Show completion menu
        elif self.state == GameState.STATS_VIEW:
            self._render_stats_view()
        elif self.state == GameState.ACHIEVEMENTS_VIEW:
            self._render_achievements_view()
        elif self.state == GameState.SETTINGS:
            self._render_settings()
        elif self.state == GameState.PROFILE_EDIT:
            self._render_profile_edit()
        elif self.state == GameState.HELP_VIEW:
            self._render_game()  # Show game in background
            self._render_help_overlay()  # Overlay help
        elif self.state == GameState.SHORTCUTS_VIEW:
            self._render_shortcuts_view()
        
        # Single refresh at the end (double buffering)
        self.stdscr.refresh()
        self._needs_redraw = False
    
    def _render_menu(self):
        """Render main menu."""
        from .colors import ColorPair
        
        # Title
        title = "LINUX COMMAND QUEST"
        subtitle = f"v{self.VERSION}"
        
        center_col = self.cols // 2
        
        try:
            self.stdscr.addstr(3, center_col - len(title) // 2, title, 
                              self.colors.attr(ColorPair.TITLE, bold=True))
            self.stdscr.addstr(4, center_col - len(subtitle) // 2, subtitle,
                              self.colors.attr(ColorPair.INFO))
        except curses.error:
            pass
        
        # Dynamic menu items based on save
        if self._has_save():
            menu_items = ["Devam Et", "Yeni Oyun", "Görev Seç", "Ayarlar", "Çıkış"]
        else:
            menu_items = ["Yeni Oyun", "Görev Seç", "Ayarlar", "Çıkış"]
        
        menu_start = 8
        
        for i, item in enumerate(menu_items):
            row = menu_start + i * 2
            
            if i == self.menu_selection:
                text = f"  ▶ {item} ◀  "
                attr = self.colors.attr(ColorPair.MENU_SELECTED, bold=True)
            else:
                text = f"    {item}    "
                attr = self.colors.attr(ColorPair.MENU_NORMAL)
            
            try:
                self.stdscr.addstr(row, center_col - len(text) // 2, text, attr)
            except curses.error:
                pass
        
        # Show save info if exists
        if self._has_save():
            save_info = f"Kayıtlı: {self._last_mission_id} - Görev {self._last_task_idx + 1}"
            try:
                self.stdscr.addstr(menu_start + len(menu_items) * 2 + 1, 
                                  center_col - len(save_info) // 2, save_info,
                                  self.colors.attr(ColorPair.INFO, dim=True))
            except curses.error:
                pass
        
        # Controls hint
        hint = "↑↓: Seç  Enter: Onayla  Q: Çıkış"
        try:
            self.stdscr.addstr(self.rows - 2, center_col - len(hint) // 2, hint,
                              self.colors.attr(ColorPair.INFO, dim=True))
        except curses.error:
            pass
    
    def _render_mission_select(self):
        """Render mission selection screen."""
        from .colors import ColorPair
        
        # Title
        title = "GÖREV SEÇ"
        try:
            self.stdscr.addstr(2, (self.cols - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
        except curses.error:
            pass
        
        # Mission list - grouped by category
        missions = self.mission_loader.get_all_missions()
        start_row = 4
        
        # Group missions by category
        categories = {}
        for m in missions:
            cat = getattr(m, 'category', 'tutorial')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(m)
        
        # Category display names
        cat_names = {
            'tutorial': '📚 EĞİTİM',
            'hacker': '🔓 HACKER EĞİTİMİ',
            'sysadmin': '🖥️ SİSTEM YÖNETİMİ',
        }
        
        row = start_row
        mission_idx = 0
        
        for cat_id, cat_missions in categories.items():
            # Category header
            if row < self.rows - 5:
                cat_title = cat_names.get(cat_id, cat_id.upper())
                try:
                    self.stdscr.addstr(row, 4, cat_title, 
                                      self.colors.attr(ColorPair.TITLE, bold=True))
                    self.stdscr.addstr(row, 4 + len(cat_title) + 1, "─" * (self.cols - len(cat_title) - 10),
                                      self.colors.attr(ColorPair.BORDER))
                except curses.error:
                    pass
                row += 1
            
            # Missions in category
            for mission in cat_missions:
                if row >= self.rows - 5:
                    break
                
                # Check if unlocked
                unlocked = all(p in self.progress.completed_missions 
                              for p in mission.prerequisites)
                completed = mission.id in self.progress.completed_missions
                
                if mission_idx == self.mission_selection:
                    prefix = "▶ "
                    attr = self.colors.attr(ColorPair.MENU_SELECTED, bold=True)
                else:
                    prefix = "  "
                    if completed:
                        attr = self.colors.attr(ColorPair.SUCCESS)
                    elif unlocked:
                        attr = self.colors.attr(ColorPair.MENU_NORMAL)
                    else:
                        attr = self.colors.attr(ColorPair.MENU_DISABLED, dim=True)
                
                status = "✓" if completed else ("🔒" if not unlocked else " ")
                diff_text = mission.difficulty.to_turkish()
                
                # Shorter name for display
                name = mission.name[:25] if len(mission.name) > 25 else mission.name
                line = f"{prefix}{status} {name:25} [{diff_text:^6}] {mission.estimated_time}"
                
                try:
                    self.stdscr.addstr(row, 6, line, attr)
                except curses.error:
                    pass
                
                row += 1
                mission_idx += 1
            
            row += 1  # Space between categories
        
        # Selected mission description
        if 0 <= self.mission_selection < len(missions):
            mission = missions[self.mission_selection]
            desc_row = self.rows - 5
            
            try:
                self.stdscr.addstr(desc_row, 4, "─" * (self.cols - 8),
                                  self.colors.attr(ColorPair.BORDER))
                self.stdscr.addstr(desc_row + 1, 4, mission.description[:self.cols - 10],
                                  self.colors.attr(ColorPair.INFO))
            except curses.error:
                pass
        
        # Controls
        hint = "↑↓: Seç  Enter: Başlat  Q: Geri"
        try:
            self.stdscr.addstr(self.rows - 2, (self.cols - len(hint)) // 2, hint,
                              self.colors.attr(ColorPair.INFO, dim=True))
        except curses.error:
            pass
    
    def _render_game(self):
        """Render main game screen."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        # Layout calculations - dynamic left panel width
        # Minimum 30, max %40, ideal for task descriptions
        left_width = max(30, min(45, int(self.cols * 0.35)))
        right_width = self.cols - left_width
        terminal_height = self.rows - 4
        
        # === HEADER ===
        mission_name = self.current_mission.name if self.current_mission else 'Ana Menü'
        header_text = f" 🐧 LINUX QUEST │ {mission_name} "
        achievement_points = self.achievements.calculate_total_points()
        
        # Combo indicator
        combo_text = ""
        if self.stats.correct_commands_streak >= 3:
            combo_text = f"🔥x{self.stats.correct_commands_streak} "
        
        stats_text = f"{combo_text}Puan: {self.score} │ 🏆 {achievement_points} │ 💡 {self.hints_remaining}/{self.config.hints_per_mission} "
        
        try:
            # Header background
            self.stdscr.addstr(0, 0, " " * self.cols, self.colors.attr(ColorPair.HEADER))
            # Left side - game title and mission (bold)
            self.stdscr.addstr(0, 0, header_text, self.colors.attr(ColorPair.HEADER, bold=True))
            # Right side - stats
            stats_x = max(0, self.cols - len(stats_text) - 1)
            self.stdscr.addstr(0, stats_x, stats_text, self.colors.attr(ColorPair.HEADER, bold=True))
        except curses.error:
            pass
        
        # === LEFT PANEL (Tasks) ===
        self._render_task_panel(1, 0, terminal_height, left_width)
        
        # === RIGHT PANEL (Terminal) ===
        self._render_terminal_panel(1, left_width, terminal_height, right_width)
        
        # === INPUT LINE ===
        self._render_input_line(self.rows - 2)
        
        # === STATUS BAR with Progress ===
        # Calculate mission progress
        progress_text = ""
        if self.current_mission:
            total = len(self.current_mission.tasks)
            done = self.current_task_idx
            pct = int((done / total) * 100) if total > 0 else 0
            filled = int((done / total) * 10) if total > 0 else 0
            bar = "▓" * filled + "░" * (10 - filled)
            progress_text = f"[{bar}] {pct}% │ "
        
        status = f" {progress_text}F1: Yardım │ F2: Stats │ F3: Başarılar │ Tab: Tamamla │ ESC: Menü "
        try:
            self.stdscr.addstr(self.rows - 1, 0, " " * self.cols, 
                              self.colors.attr(ColorPair.HEADER))
            # Center or left-align based on width
            status_x = max(0, (self.cols - len(status)) // 2)
            self.stdscr.addstr(self.rows - 1, status_x, status[:self.cols-1],
                              self.colors.attr(ColorPair.HEADER, bold=True))
        except curses.error:
            pass
    
    def _render_task_panel(self, y: int, x: int, height: int, width: int):
        """Render task panel with shortcuts box."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        border_attr = self.colors.attr(ColorPair.BORDER)
        
        # Reserve space for shortcuts box at bottom (7 lines)
        shortcuts_height = 8
        task_height = height - shortcuts_height
        
        # === TASK PANEL ===
        try:
            # Top
            self.stdscr.addstr(y, x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " GÖREVLER "
            self.stdscr.addstr(y, x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            # Sides
            for i in range(1, task_height - 1):
                self.stdscr.addstr(y + i, x, box.V, border_attr)
                self.stdscr.addstr(y + i, x + width - 1, box.V, border_attr)
            
            # Bottom of task panel
            self.stdscr.addstr(y + task_height - 1, x, box.BL + box.H * (width - 2) + box.BR, border_attr)
        except curses.error:
            pass
        
        # Task list with multi-line support
        if self.current_mission:
            inner_y = y + 2
            inner_x = x + 2
            inner_width = width - 4
            current_row = inner_y
            
            for i, task in enumerate(self.current_mission.tasks):
                if current_row >= y + task_height - 2:
                    break
                
                if i < self.current_task_idx:
                    status = "✓"
                    attr = self.colors.attr(ColorPair.TASK_DONE)
                elif i == self.current_task_idx:
                    status = "▶"
                    attr = self.colors.attr(ColorPair.TASK_ACTIVE, bold=True)
                else:
                    status = "○"
                    attr = self.colors.attr(ColorPair.TASK_PENDING, dim=True)
                
                # Smart text wrapping for long descriptions
                desc = task.description
                prefix = f"{status} "
                max_text_width = inner_width - len(prefix)
                
                if len(desc) <= max_text_width:
                    # Single line
                    line = f"{prefix}{desc}"
                    try:
                        self.stdscr.addstr(current_row, inner_x, line[:inner_width], attr)
                    except curses.error:
                        pass
                    current_row += 1
                else:
                    # Multi-line: first line with status, rest indented
                    first_line = f"{prefix}{desc[:max_text_width]}"
                    try:
                        self.stdscr.addstr(current_row, inner_x, first_line, attr)
                    except curses.error:
                        pass
                    current_row += 1
                    
                    # Continue on next line(s) with indent
                    remaining = desc[max_text_width:]
                    indent = "  "  # 2 spaces indent for continuation
                    cont_width = inner_width - len(indent)
                    
                    while remaining and current_row < y + task_height - 2:
                        cont_line = f"{indent}{remaining[:cont_width]}"
                        try:
                            self.stdscr.addstr(current_row, inner_x, cont_line, attr)
                        except curses.error:
                            pass
                        remaining = remaining[cont_width:]
                        current_row += 1
        
        # === SHORTCUTS BOX ===
        shortcuts_y = y + task_height
        try:
            # Top of shortcuts
            self.stdscr.addstr(shortcuts_y, x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            shortcut_title = " ⌨ KISAYOLLAR "
            self.stdscr.addstr(shortcuts_y, x + (width - len(shortcut_title)) // 2, shortcut_title,
                              self.colors.attr(ColorPair.INFO, bold=True))
            
            # Sides and content
            shortcuts = [
                ("F1", "Yardım"),
                ("F2", "İstatistik"),
                ("F3", "Başarılar"),
                ("Tab", "Otomatik Tamamla"),
                ("Ctrl+R", "Görevi Sıfırla"),
                ("ESC", "Menü"),
            ]
            
            for i in range(1, shortcuts_height - 1):
                self.stdscr.addstr(shortcuts_y + i, x, box.V, border_attr)
                self.stdscr.addstr(shortcuts_y + i, x + width - 1, box.V, border_attr)
                
                # Shortcut content
                if i - 1 < len(shortcuts):
                    key, desc = shortcuts[i - 1]
                    shortcut_text = f" {key:8} {desc}"
                    self.stdscr.addstr(shortcuts_y + i, x + 1, shortcut_text[:width-3],
                                      self.colors.attr(ColorPair.DEFAULT))
            
            # Bottom
            self.stdscr.addstr(shortcuts_y + shortcuts_height - 1, x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
        except curses.error:
            pass
    
    def _render_terminal_panel(self, y: int, x: int, height: int, width: int):
        """Render terminal output panel."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        # Border
        try:
            # Top
            self.stdscr.addstr(y, x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " TERMİNAL "
            self.stdscr.addstr(y, x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            # Sides
            for i in range(1, height - 1):
                self.stdscr.addstr(y + i, x, box.V, border_attr)
                self.stdscr.addstr(y + i, x + width - 1, box.V, border_attr)
            
            # Bottom
            self.stdscr.addstr(y + height - 1, x, box.BL + box.H * (width - 2) + box.BR, border_attr)
        except curses.error:
            pass
        
        # Terminal content
        inner_height = height - 2
        inner_width = width - 4
        inner_y = y + 1
        inner_x = x + 2
        
        # Show last N lines that fit
        visible_lines = self.terminal_lines[-(inner_height):]
        
        for i, (line, attr) in enumerate(visible_lines):
            if i >= inner_height:
                break
            
            # Truncate and clean ANSI codes for display
            display_line = line[:inner_width]
            
            try:
                # Simple ANSI handling - strip codes and use attr
                clean_line = display_line
                for code in ["\033[0m", "\033[31m", "\033[32m", "\033[33m", 
                            "\033[34m", "\033[36m", "\033[90m", "\033[1m"]:
                    clean_line = clean_line.replace(code, "")
                
                self.stdscr.addstr(inner_y + i, inner_x, clean_line[:inner_width], attr)
            except curses.error:
                pass
    
    def _render_pause_overlay(self):
        """Render pause menu overlay on top of game."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        # Overlay dimensions
        overlay_width = 40
        overlay_height = 12
        start_y = (self.rows - overlay_height) // 2
        start_x = (self.cols - overlay_width) // 2
        
        # Draw overlay box with semi-transparent effect (darker background)
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        bg_attr = self.colors.attr(ColorPair.DEFAULT)
        
        try:
            # Top border
            self.stdscr.addstr(start_y, start_x, 
                              box.TL + box.H * (overlay_width - 2) + box.TR, border_attr)
            
            # Title
            title = " DURAKLAT "
            title_pos = start_x + (overlay_width - len(title)) // 2
            self.stdscr.addstr(start_y, title_pos, title, 
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            # Content area
            for i in range(1, overlay_height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (overlay_width - 2), bg_attr)
                self.stdscr.addstr(start_y + i, start_x + overlay_width - 1, box.V, border_attr)
            
            # Bottom border
            self.stdscr.addstr(start_y + overlay_height - 1, start_x,
                              box.BL + box.H * (overlay_width - 2) + box.BR, border_attr)
            
            # Menu items
            pause_items = ["Devam Et", "Görevi Yeniden Başlat", "Ana Menüye Dön", "Oyundan Çık"]
            menu_start_y = start_y + 3
            
            for i, item in enumerate(pause_items):
                row = menu_start_y + i
                
                if i == self.pause_selection:
                    text = f"▶ {item}"
                    attr = self.colors.attr(ColorPair.MENU_SELECTED, bold=True)
                else:
                    text = f"  {item}"
                    attr = self.colors.attr(ColorPair.MENU_NORMAL)
                
                # Center the item
                item_x = start_x + (overlay_width - len(text)) // 2
                self.stdscr.addstr(row, item_x, text, attr)
            
            # Hint
            hint = "ESC: Devam  ↑↓: Seç  Enter: Onayla"
            hint_y = start_y + overlay_height - 2
            hint_x = start_x + (overlay_width - len(hint)) // 2
            self.stdscr.addstr(hint_y, hint_x, hint, 
                              self.colors.attr(ColorPair.INFO, dim=True))
            
        except curses.error:
            pass
    
    def _render_complete_overlay(self):
        """Render mission complete overlay with next actions."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        # Initialize selection if needed
        if not hasattr(self, 'complete_selection'):
            self.complete_selection = 0
        
        # Get options
        next_mission = self._get_next_mission()
        
        if next_mission:
            complete_items = ["Sonraki Görev", "Görev Seçimine Dön", "Ana Menü"]
            next_info = f"Sonraki: {next_mission.name}"
        else:
            complete_items = ["Görev Seçimine Dön", "Ana Menü"]
            next_info = "Tüm görevler tamamlandı!"
        
        # Overlay dimensions
        overlay_width = 50
        overlay_height = 14
        start_y = (self.rows - overlay_height) // 2
        start_x = (self.cols - overlay_width) // 2
        
        border_attr = self.colors.attr(ColorPair.SUCCESS)
        bg_attr = self.colors.attr(ColorPair.DEFAULT)
        
        try:
            # Top border
            self.stdscr.addstr(start_y, start_x, 
                              box.TL + box.H * (overlay_width - 2) + box.TR, border_attr)
            
            # Title
            title = " 🎉 MİSYON TAMAMLANDI! 🎉 "
            title_pos = start_x + (overlay_width - len(title)) // 2
            self.stdscr.addstr(start_y, title_pos, title, 
                              self.colors.attr(ColorPair.SUCCESS, bold=True))
            
            # Content area
            for i in range(1, overlay_height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (overlay_width - 2), bg_attr)
                self.stdscr.addstr(start_y + i, start_x + overlay_width - 1, box.V, border_attr)
            
            # Bottom border
            self.stdscr.addstr(start_y + overlay_height - 1, start_x,
                              box.BL + box.H * (overlay_width - 2) + box.BR, border_attr)
            
            # Score info
            score_text = f"Puan: {self.score} | Toplam: {self.progress.total_score}"
            self.stdscr.addstr(start_y + 2, start_x + (overlay_width - len(score_text)) // 2,
                              score_text, self.colors.attr(ColorPair.WARNING, bold=True))
            
            # Next mission info
            self.stdscr.addstr(start_y + 4, start_x + (overlay_width - len(next_info)) // 2,
                              next_info, self.colors.attr(ColorPair.INFO))
            
            # Separator
            self.stdscr.addstr(start_y + 5, start_x + 2, "─" * (overlay_width - 4),
                              self.colors.attr(ColorPair.BORDER))
            
            # Menu items
            menu_start_y = start_y + 7
            
            for i, item in enumerate(complete_items):
                row = menu_start_y + i
                
                if i == self.complete_selection:
                    text = f"▶ {item}"
                    attr = self.colors.attr(ColorPair.MENU_SELECTED, bold=True)
                else:
                    text = f"  {item}"
                    attr = self.colors.attr(ColorPair.MENU_NORMAL)
                
                item_x = start_x + (overlay_width - len(text)) // 2
                self.stdscr.addstr(row, item_x, text, attr)
            
            # Hint
            hint = "↑↓: Seç  Enter: Onayla"
            hint_y = start_y + overlay_height - 2
            hint_x = start_x + (overlay_width - len(hint)) // 2
            self.stdscr.addstr(hint_y, hint_x, hint, 
                              self.colors.attr(ColorPair.INFO, dim=True))
            
        except curses.error:
            pass
    
    def _render_input_line(self, row: int):
        """Render command input line."""
        from .colors import ColorPair
        
        # Build prompt
        prompt = f"{self.fs.username}@{self.fs.hostname}:{self.fs.get_prompt_path()}$ "
        input_text = "".join(self.input_buffer)
        
        try:
            # Clear line
            self.stdscr.addstr(row, 0, " " * self.cols, 0)
            
            # Prompt parts with colors
            col = 1
            self.stdscr.addstr(row, col, self.fs.username, 
                              self.colors.attr(ColorPair.PROMPT_USER, bold=True))
            col += len(self.fs.username)
            
            self.stdscr.addstr(row, col, "@", 0)
            col += 1
            
            self.stdscr.addstr(row, col, self.fs.hostname,
                              self.colors.attr(ColorPair.PROMPT_HOST))
            col += len(self.fs.hostname)
            
            self.stdscr.addstr(row, col, ":", 0)
            col += 1
            
            path = self.fs.get_prompt_path()
            self.stdscr.addstr(row, col, path,
                              self.colors.attr(ColorPair.PROMPT_PATH))
            col += len(path)
            
            self.stdscr.addstr(row, col, "$ ", 0)
            col += 2
            
            # Input text
            max_input = self.cols - col - 2
            if len(input_text) <= max_input:
                self.stdscr.addstr(row, col, input_text, 0)
                cursor_col = col + self.input_cursor
            else:
                # Scroll input to show cursor
                start = max(0, self.input_cursor - max_input + 1)
                visible = input_text[start:start + max_input]
                self.stdscr.addstr(row, col, visible, 0)
                cursor_col = col + (self.input_cursor - start)
            
            # Position cursor
            self.stdscr.move(row, cursor_col)
            
        except curses.error:
            pass


    # === STATS VIEW ===
    
    def _handle_stats_input(self, key):
        """Handle stats view input."""
        # ESC or other keys return to previous state
        if key in (27, ord('q'), ord(' '), 10, curses.KEY_ENTER):
            self.state = self._previous_state
            self._needs_redraw = True
    
    def _render_stats_view(self):
        """Render statistics view."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        # Calculate dimensions
        width = min(60, self.cols - 4)
        height = min(22, self.rows - 4)
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        # Draw box
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Top border
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " 📊 İSTATİSTİKLER "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            # Sides and content
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            # Bottom border
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            # Content
            y = start_y + 2
            x = start_x + 3
            
            stats_data = [
                ("", ""),
                ("📈 GENEL İSTATİSTİKLER", ""),
                ("─" * 40, ""),
                ("Toplam Komut", str(self.stats.total_commands)),
                ("Toplam Hata", str(self.stats.total_errors)),
                ("Kullanılan Komut Çeşidi", str(len(self.stats.unique_commands_used))),
                ("Ziyaret Edilen Dizin", str(len(self.stats.visited_directories))),
                ("", ""),
                ("🎯 GÖREV İSTATİSTİKLERİ", ""),
                ("─" * 40, ""),
                ("Tamamlanan Görev", str(self.stats.missions_completed)),
                ("Kusursuz Görev", str(self.stats.missions_perfect)),
                ("En Yüksek Seri", str(self.stats.best_streak)),
                ("Kullanılan İpucu", str(self.stats.hints_used_total)),
                ("", ""),
                ("🔥 KOMBO", ""),
                ("─" * 40, ""),
                ("Mevcut Kombo", str(self.stats.correct_commands_streak)),
                ("En İyi Kombo", str(self.stats.best_combo)),
                ("", ""),
            ]
            
            for label, value in stats_data:
                if y >= start_y + height - 2:
                    break
                if label.startswith("─"):
                    self.stdscr.addstr(y, x, label[:width-6], self.colors.attr(ColorPair.BORDER))
                elif label.startswith("📈") or label.startswith("🎯") or label.startswith("🔥"):
                    self.stdscr.addstr(y, x, label, self.colors.attr(ColorPair.TITLE, bold=True))
                elif value:
                    self.stdscr.addstr(y, x, f"{label}:", self.colors.attr(ColorPair.DEFAULT))
                    self.stdscr.addstr(y, x + 25, value, self.colors.attr(ColorPair.SUCCESS, bold=True))
                y += 1
            
            # Footer
            hint = "Çıkmak için ESC veya ENTER"
            self.stdscr.addstr(start_y + height - 2, start_x + (width - len(hint)) // 2, hint,
                              self.colors.attr(ColorPair.INFO))
            
        except curses.error:
            pass
    
    # === ACHIEVEMENTS VIEW ===
    
    def _handle_achievements_input(self, key):
        """Handle achievements view input."""
        if not hasattr(self, 'achievement_scroll'):
            self.achievement_scroll = 0
        
        max_scroll = max(0, len(self.achievements.get_all_achievements()) - 10)
        
        if key == curses.KEY_UP:
            self.achievement_scroll = max(0, self.achievement_scroll - 1)
            self._needs_redraw = True
        elif key == curses.KEY_DOWN:
            self.achievement_scroll = min(max_scroll, self.achievement_scroll + 1)
            self._needs_redraw = True
        elif key in (27, ord('q'), ord(' '), 10, curses.KEY_ENTER):
            self.state = self._previous_state
            self._needs_redraw = True
    
    def _render_achievements_view(self):
        """Render achievements gallery."""
        from .colors import ColorPair, get_box_chars
        from .achievements import AchievementRarity
        
        box = get_box_chars()
        
        if not hasattr(self, 'achievement_scroll'):
            self.achievement_scroll = 0
        
        # Calculate dimensions
        width = min(70, self.cols - 4)
        height = min(20, self.rows - 4)
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        # Draw box
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Top border
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            
            unlocked_count = len(self.achievements.get_unlocked())
            total_count = len(self.achievements.get_all_achievements())
            total_points = self.achievements.calculate_total_points()
            title = f" 🏆 BAŞARILAR ({unlocked_count}/{total_count}) - {total_points} Puan "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            # Sides
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            # Bottom border
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            # Content - list achievements
            all_achievements = self.achievements.get_all_achievements()
            visible_count = height - 4
            
            y = start_y + 2
            x = start_x + 2
            
            for i, achievement in enumerate(all_achievements[self.achievement_scroll:self.achievement_scroll + visible_count]):
                if y >= start_y + height - 2:
                    break
                
                is_unlocked = self.achievements.is_unlocked(achievement.id)
                
                # Icon and name
                if is_unlocked:
                    icon = achievement.icon
                    name_attr = self.colors.attr(ColorPair.SUCCESS, bold=True)
                    desc_attr = self.colors.attr(ColorPair.DEFAULT)
                else:
                    if achievement.hidden:
                        icon = "❓"
                        name_attr = self.colors.attr(ColorPair.MENU_DISABLED)
                        desc_attr = self.colors.attr(ColorPair.MENU_DISABLED)
                    else:
                        icon = "🔒"
                        name_attr = self.colors.attr(ColorPair.MENU_DISABLED)
                        desc_attr = self.colors.attr(ColorPair.MENU_DISABLED)
                
                # Rarity indicator
                rarity_icon = achievement.rarity.to_icon()
                
                # Draw line
                line = f"{icon} {rarity_icon} {achievement.name[:20]:<20}"
                self.stdscr.addstr(y, x, line, name_attr)
                
                if is_unlocked or not achievement.hidden:
                    desc = achievement.description[:width - 35]
                    self.stdscr.addstr(y, x + 28, desc, desc_attr)
                else:
                    self.stdscr.addstr(y, x + 28, "???", desc_attr)
                
                y += 1
            
            # Scroll indicator
            if len(all_achievements) > visible_count:
                scroll_info = f"↑↓ Kaydır ({self.achievement_scroll + 1}-{min(self.achievement_scroll + visible_count, len(all_achievements))}/{len(all_achievements)})"
                self.stdscr.addstr(start_y + height - 2, start_x + 3, scroll_info,
                                  self.colors.attr(ColorPair.INFO))
            
            # Footer
            hint = "ESC: Kapat"
            self.stdscr.addstr(start_y + height - 2, start_x + width - len(hint) - 3, hint,
                              self.colors.attr(ColorPair.INFO))
            
        except curses.error:
            pass
    
    # === SETTINGS ===
    
    def _handle_settings_input(self, key):
        """Handle settings menu input."""
        from .audio import SoundEffect
        
        if not hasattr(self, 'settings_selection'):
            self.settings_selection = 0
        
        settings_items = ["Tema Değiştir", "Ses Aç/Kapat", "Kısayollar", "Geri"]
        
        if key == curses.KEY_UP:
            self.settings_selection = (self.settings_selection - 1) % len(settings_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key == curses.KEY_DOWN:
            self.settings_selection = (self.settings_selection + 1) % len(settings_items)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
        elif key in (10, curses.KEY_ENTER):
            self.audio.play(SoundEffect.MENU_SELECT)
            selected = settings_items[self.settings_selection]
            
            if selected == "Tema Değiştir":
                self._cycle_theme()
            elif selected == "Ses Aç/Kapat":
                self.config.sound_enabled = not self.config.sound_enabled
                self.audio.config.enabled = self.config.sound_enabled
            elif selected == "Kısayollar":
                # Kısayollar'dan Settings'e dönmek için özel state
                self._shortcuts_return_state = self.state
                self.state = GameState.SHORTCUTS_VIEW
            elif selected == "Geri":
                self.state = self._previous_state
            
            self._needs_redraw = True
        elif key == 27:
            self.state = self._previous_state
            self._needs_redraw = True
    
    def _cycle_theme(self):
        """Cycle through available themes."""
        from .colors import THEMES
        
        theme_names = list(THEMES.keys())
        current_idx = theme_names.index(self.config.theme) if self.config.theme in theme_names else 0
        next_idx = (current_idx + 1) % len(theme_names)
        self.config.theme = theme_names[next_idx]
        self.colors.set_theme(self.config.theme)
    
    def _render_settings(self):
        """Render settings menu."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        if not hasattr(self, 'settings_selection'):
            self.settings_selection = 0
        
        # Calculate dimensions
        width = 50
        height = 14
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Box
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " ⚙️ AYARLAR "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            # Settings items
            settings_items = [
                (f"Tema: {self.config.theme.upper()}", "Tema Değiştir"),
                (f"Ses: {'AÇIK' if self.config.sound_enabled else 'KAPALI'}", "Ses Aç/Kapat"),
                ("⌨️  Kısayollar", "Kısayollar"),
                ("← Geri", "Geri"),
            ]
            
            y = start_y + 3
            for i, (display, _) in enumerate(settings_items):
                if i == self.settings_selection:
                    indicator = "▶ "
                    attr = self.colors.attr(ColorPair.MENU_SELECTED, bold=True)
                else:
                    indicator = "  "
                    attr = self.colors.attr(ColorPair.MENU_NORMAL)
                
                text = f"{indicator}{display}"
                x = start_x + (width - len(text)) // 2
                self.stdscr.addstr(y, x, text, attr)
                y += 2
            
        except curses.error:
            pass

    # === PROFILE EDIT ===
    
    def _handle_profile_input(self, key):
        """Handle profile edit input."""
        from .audio import SoundEffect
        
        if not hasattr(self, 'profile_field'):
            self.profile_field = 0  # 0: username, 1: hostname
            self.profile_username = list(self.config.username)
            self.profile_hostname = list(self.config.hostname)
            self.profile_cursor = len(self.profile_username)
        
        # ESC - cancel and return to previous state
        if key == 27:
            # Reset profile edit state without saving
            if hasattr(self, 'profile_field'):
                del self.profile_field
            if hasattr(self, 'profile_username'):
                del self.profile_username
            if hasattr(self, 'profile_hostname'):
                del self.profile_hostname
            if hasattr(self, 'profile_cursor'):
                del self.profile_cursor
            
            self.state = self._previous_state
            self._needs_redraw = True
            return
        
        # Tab or Up/Down - switch field
        if key in (9, curses.KEY_UP, curses.KEY_DOWN):
            self.profile_field = 1 - self.profile_field
            if self.profile_field == 0:
                self.profile_cursor = len(self.profile_username)
            else:
                self.profile_cursor = len(self.profile_hostname)
            self._needs_redraw = True
            self.audio.play(SoundEffect.MENU_MOVE)
            return
        
        # Enter - save and return
        if key in (10, curses.KEY_ENTER):
            # Apply changes
            new_username = "".join(self.profile_username).strip() or "user"
            new_hostname = "".join(self.profile_hostname).strip() or "quest"
            
            self.config.username = new_username
            self.config.hostname = new_hostname
            self.fs.username = new_username
            self.fs.hostname = new_hostname
            self.fs.home = f"/home/{new_username}"
            
            # Reset profile edit state
            del self.profile_field
            del self.profile_username
            del self.profile_hostname
            del self.profile_cursor
            
            self.state = self._previous_state
            self._needs_redraw = True
            self._save_progress()
            self.audio.play(SoundEffect.MENU_SELECT)
            return
        
        # Get current buffer
        if self.profile_field == 0:
            buffer = self.profile_username
        else:
            buffer = self.profile_hostname
        
        # Left/Right cursor
        if key == curses.KEY_LEFT:
            if self.profile_cursor > 0:
                self.profile_cursor -= 1
                self._needs_redraw = True
            return
        elif key == curses.KEY_RIGHT:
            if self.profile_cursor < len(buffer):
                self.profile_cursor += 1
                self._needs_redraw = True
            return
        
        # Backspace
        if key in (127, curses.KEY_BACKSPACE):
            if self.profile_cursor > 0:
                buffer.pop(self.profile_cursor - 1)
                self.profile_cursor -= 1
                self._needs_redraw = True
            return
        
        # Printable character (limit to 16 chars, alphanumeric only)
        if 32 <= key < 127 and len(buffer) < 16:
            char = chr(key)
            if char.isalnum() or char in "-_":
                buffer.insert(self.profile_cursor, char)
                self.profile_cursor += 1
                self._needs_redraw = True
    
    def _render_profile_edit(self):
        """Render profile edit screen."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        if not hasattr(self, 'profile_field'):
            self.profile_field = 0
            self.profile_username = list(self.config.username)
            self.profile_hostname = list(self.config.hostname)
            self.profile_cursor = len(self.profile_username)
        
        # Calculate dimensions
        width = 50
        height = 14
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Box
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " 👤 PROFİL DÜZENLE "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            # Preview - use current editing values
            current_username = "".join(self.profile_username) or "user"
            current_hostname = "".join(self.profile_hostname) or "quest"
            preview = f"{current_username}@{current_hostname}:~$"
            self.stdscr.addstr(start_y + 2, start_x + (width - len(preview)) // 2 - 5,
                              "Önizleme: ", self.colors.attr(ColorPair.INFO))
            self.stdscr.addstr(start_y + 2, start_x + (width - len(preview)) // 2 + 5,
                              preview, self.colors.attr(ColorPair.SUCCESS, bold=True))
            
            # Separator
            self.stdscr.addstr(start_y + 4, start_x + 3, "─" * (width - 6), 
                              self.colors.attr(ColorPair.BORDER))
            
            # Username field
            y = start_y + 6
            label = "Kullanıcı Adı:"
            if self.profile_field == 0:
                self.stdscr.addstr(y, start_x + 5, "▶ " + label, 
                                  self.colors.attr(ColorPair.MENU_SELECTED, bold=True))
                field_attr = self.colors.attr(ColorPair.SUCCESS, bold=True)
            else:
                self.stdscr.addstr(y, start_x + 5, "  " + label, 
                                  self.colors.attr(ColorPair.DEFAULT))
                field_attr = self.colors.attr(ColorPair.DEFAULT)
            
            username_str = "".join(self.profile_username)
            field_x = start_x + 22
            self.stdscr.addstr(y, field_x, "[" + username_str.ljust(16) + "]", field_attr)
            
            # Hostname field
            y = start_y + 8
            label = "Makine Adı:"
            if self.profile_field == 1:
                self.stdscr.addstr(y, start_x + 5, "▶ " + label, 
                                  self.colors.attr(ColorPair.MENU_SELECTED, bold=True))
                field_attr = self.colors.attr(ColorPair.SUCCESS, bold=True)
            else:
                self.stdscr.addstr(y, start_x + 5, "  " + label, 
                                  self.colors.attr(ColorPair.DEFAULT))
                field_attr = self.colors.attr(ColorPair.DEFAULT)
            
            hostname_str = "".join(self.profile_hostname)
            self.stdscr.addstr(y, field_x, "[" + hostname_str.ljust(16) + "]", field_attr)
            
            # Show cursor
            if self.profile_field == 0:
                cursor_x = field_x + 1 + self.profile_cursor
                cursor_y = start_y + 6
            else:
                cursor_x = field_x + 1 + self.profile_cursor
                cursor_y = start_y + 8
            
            # Hint
            hint = "Tab: Alan Değiştir │ Enter: Kaydet │ ESC: İptal"
            self.stdscr.addstr(start_y + height - 2, start_x + (width - len(hint)) // 2, hint,
                              self.colors.attr(ColorPair.INFO))
            
            # Position cursor
            self.stdscr.move(cursor_y, cursor_x)
            
        except curses.error:
            pass

    # === HELP VIEW (F1) ===
    
    def _handle_help_input(self, key):
        """Handle help view input."""
        from .audio import SoundEffect
        
        if not hasattr(self, 'help_hint_level'):
            self.help_hint_level = 0
        
        # H key - show more hints
        if key in (ord('h'), ord('H')):
            if self.help_hint_level < 2:
                self.help_hint_level += 1
                self._needs_redraw = True
                self.audio.play(SoundEffect.MENU_MOVE)
            return
        
        # ESC or other keys - close
        if key in (27, ord('q'), ord(' '), 10, curses.KEY_ENTER):
            self.state = self._previous_state
            self._needs_redraw = True
            return
    
    def _render_help_overlay(self):
        """Render smart help overlay."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        if not hasattr(self, 'help_hint_level'):
            self.help_hint_level = 0
        
        # Get current task info
        current_task = None
        if self.current_mission and self.current_task_idx < len(self.current_mission.tasks):
            current_task = self.current_mission.tasks[self.current_task_idx]
        
        # Calculate dimensions
        width = min(55, self.cols - 4)
        height = min(18, self.rows - 4)
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Draw box
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " 💡 AKILLI YARDIM "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            y = start_y + 2
            x = start_x + 3
            
            if current_task:
                # Task description
                self.stdscr.addstr(y, x, "📋 Görev:", self.colors.attr(ColorPair.INFO, bold=True))
                y += 1
                desc = current_task.description[:width - 8]
                self.stdscr.addstr(y, x, desc, self.colors.attr(ColorPair.DEFAULT))
                y += 2
                
                # Separator
                self.stdscr.addstr(y, x, "─" * (width - 6), self.colors.attr(ColorPair.BORDER))
                y += 2
                
                # Smart hints based on level
                hints = self._get_smart_hints(current_task)
                
                self.stdscr.addstr(y, x, "💭 İpuçları:", self.colors.attr(ColorPair.WARNING, bold=True))
                y += 1
                
                for i, hint in enumerate(hints):
                    if i <= self.help_hint_level:
                        self.stdscr.addstr(y, x, f"  {i+1}. {hint[:width-10]}", 
                                          self.colors.attr(ColorPair.DEFAULT))
                    else:
                        self.stdscr.addstr(y, x, f"  {i+1}. [H tuşuna bas]", 
                                          self.colors.attr(ColorPair.MENU_DISABLED))
                    y += 1
                
                y += 1
                
                # Thinking prompt
                if self.help_hint_level < 2:
                    think = "🤔 Düşün: Komut nasıl yazılır?"
                    self.stdscr.addstr(y, x, think, self.colors.attr(ColorPair.INFO))
                else:
                    # Show command structure hint at max level
                    cmd_hint = self._get_command_structure_hint(current_task)
                    if cmd_hint:
                        self.stdscr.addstr(y, x, f"📝 Format: {cmd_hint}", 
                                          self.colors.attr(ColorPair.SUCCESS))
            else:
                self.stdscr.addstr(y, x, "Aktif görev yok.", self.colors.attr(ColorPair.INFO))
            
            # Footer
            hint_text = "H: Daha fazla ipucu │ ESC: Kapat"
            self.stdscr.addstr(start_y + height - 2, start_x + (width - len(hint_text)) // 2, 
                              hint_text, self.colors.attr(ColorPair.INFO))
            
        except curses.error:
            pass
    
    def _get_smart_hints(self, task) -> list[str]:
        """Generate smart hints for a task without giving the answer."""
        hints = []
        
        # Get the command from accepted_commands
        if task.accepted_commands:
            cmd = task.accepted_commands[0]
            parts = cmd.split()
            
            if parts:
                base_cmd = parts[0]
                
                # Hint 1: Command category
                cmd_hints = {
                    'ls': "Dosya listeleme komutu kullan",
                    'cd': "Dizin değiştirme komutu kullan", 
                    'pwd': "Mevcut dizini gösteren komut",
                    'cat': "Dosya içeriği okuma komutu",
                    'echo': "Metin yazdırma komutu",
                    'mkdir': "Dizin oluşturma komutu",
                    'touch': "Dosya oluşturma komutu",
                    'rm': "Silme komutu",
                    'cp': "Kopyalama komutu",
                    'mv': "Taşıma/yeniden adlandırma komutu",
                    'grep': "Metin arama komutu",
                    'head': "Dosya başını gösteren komut",
                    'tail': "Dosya sonunu gösteren komut",
                    'wc': "Satır/kelime sayma komutu",
                    'find': "Dosya arama komutu",
                    'whoami': "Kullanıcı bilgisi komutu",
                    'hostname': "Makine adı komutu",
                    'uname': "Sistem bilgisi komutu",
                }
                hints.append(cmd_hints.get(base_cmd, f"'{base_cmd}' komutunu düşün"))
                
                # Hint 2: Flags/options
                if len(parts) > 1:
                    flags = [p for p in parts[1:] if p.startswith('-')]
                    if flags:
                        flag_hints = {
                            '-a': "Gizli dosyaları da göster (-a = all)",
                            '-la': "Detaylı liste + gizli dosyalar",
                            '-l': "Detaylı (uzun) format",
                            '-r': "Recursive (alt dizinler dahil)",
                            '-rf': "Recursive + zorla (dikkatli!)",
                            '-n': "Satır sayısı belirt",
                            '-i': "Büyük/küçük harf duyarsız",
                            '-5': "5 satır göster",
                        }
                        for f in flags:
                            if f in flag_hints:
                                hints.append(flag_hints[f])
                                break
                        else:
                            hints.append("Komuta bayrak/seçenek ekle")
                    else:
                        hints.append("Komuta parametre/dosya adı ekle")
                else:
                    hints.append("Komutu tek başına kullanabilirsin")
                
                # Hint 3: More specific
                if task.hint:
                    # Use task's own hint but make it less obvious
                    if "'" in task.hint:
                        hints.append("Komut yapısını düşün")
                    else:
                        hints.append(task.hint[:40])
        
        # Ensure we have 3 hints
        while len(hints) < 3:
            hints.append("help komutu ile yardım alabilirsin")
        
        return hints[:3]
    
    def _get_command_structure_hint(self, task) -> str:
        """Get command structure hint without exact answer."""
        if task.accepted_commands:
            cmd = task.accepted_commands[0]
            parts = cmd.split()
            
            if len(parts) == 1:
                return parts[0]
            elif len(parts) == 2:
                if parts[1].startswith('-'):
                    return f"{parts[0]} {parts[1]}"
                else:
                    return f"{parts[0]} <dosya/dizin>"
            else:
                # Hide specific values
                structure = [parts[0]]
                for p in parts[1:]:
                    if p.startswith('-'):
                        structure.append(p)
                    elif p.startswith('/'):
                        structure.append("<yol>")
                    else:
                        structure.append("<...>")
                return " ".join(structure)
        return ""

    # === SHORTCUTS VIEW ===
    
    def _handle_shortcuts_input(self, key):
        """Handle shortcuts view input."""
        # Any key returns to settings
        if key in (27, ord('q'), ord(' '), 10, curses.KEY_ENTER):
            # Kısayollar Settings'ten açıldıysa Settings'e dön
            if hasattr(self, '_shortcuts_return_state'):
                self.state = self._shortcuts_return_state
                del self._shortcuts_return_state
            else:
                self.state = GameState.SETTINGS
            self._needs_redraw = True
    
    def _render_shortcuts_view(self):
        """Render shortcuts view."""
        from .colors import ColorPair, get_box_chars
        
        box = get_box_chars()
        
        # Calculate dimensions
        width = 55
        height = 20
        start_x = (self.cols - width) // 2
        start_y = (self.rows - height) // 2
        
        border_attr = self.colors.attr(ColorPair.BORDER_ACTIVE)
        
        try:
            # Box
            self.stdscr.addstr(start_y, start_x, box.TL + box.H * (width - 2) + box.TR, border_attr)
            title = " ⌨️ KISAYOLLAR "
            self.stdscr.addstr(start_y, start_x + (width - len(title)) // 2, title,
                              self.colors.attr(ColorPair.TITLE, bold=True))
            
            for i in range(1, height - 1):
                self.stdscr.addstr(start_y + i, start_x, box.V, border_attr)
                self.stdscr.addstr(start_y + i, start_x + 1, " " * (width - 2), 
                                  self.colors.attr(ColorPair.DEFAULT))
                self.stdscr.addstr(start_y + i, start_x + width - 1, box.V, border_attr)
            
            self.stdscr.addstr(start_y + height - 1, start_x, 
                              box.BL + box.H * (width - 2) + box.BR, border_attr)
            
            # Shortcuts - organized by category
            y = start_y + 2
            x = start_x + 3
            
            # Oyun İçi
            self.stdscr.addstr(y, x, "📺 OYUN İÇİ", self.colors.attr(ColorPair.INFO, bold=True))
            y += 1
            self.stdscr.addstr(y, x, "─" * (width - 6), self.colors.attr(ColorPair.BORDER))
            y += 1
            
            game_shortcuts = [
                ("F1", "Akıllı Yardım (ipuçları)"),
                ("F2", "İstatistikleri Görüntüle"),
                ("F3", "Başarı Galerisi"),
                ("Tab", "Komut Otomatik Tamamlama"),
                ("Ctrl+H", "Hızlı İpucu"),
                ("Ctrl+R", "Görevi Sıfırla"),
                ("↑/↓", "Komut Geçmişi"),
                ("ESC", "Duraklatma Menüsü"),
            ]
            
            for key, desc in game_shortcuts:
                self.stdscr.addstr(y, x, f"  {key:10}", self.colors.attr(ColorPair.SUCCESS))
                self.stdscr.addstr(y, x + 12, desc, self.colors.attr(ColorPair.DEFAULT))
                y += 1
            
            y += 1
            
            # Ana Menü
            self.stdscr.addstr(y, x, "🏠 ANA MENÜ", self.colors.attr(ColorPair.INFO, bold=True))
            y += 1
            self.stdscr.addstr(y, x, "─" * (width - 6), self.colors.attr(ColorPair.BORDER))
            y += 1
            
            menu_shortcuts = [
                ("F2", "İstatistikler"),
                ("F3", "Başarılar"),
                ("F4", "Profil Düzenle"),
                ("Q", "Çıkış"),
            ]
            
            for key, desc in menu_shortcuts:
                self.stdscr.addstr(y, x, f"  {key:10}", self.colors.attr(ColorPair.SUCCESS))
                self.stdscr.addstr(y, x + 12, desc, self.colors.attr(ColorPair.DEFAULT))
                y += 1
            
            # Footer
            hint = "ESC: Kapat"
            self.stdscr.addstr(start_y + height - 2, start_x + (width - len(hint)) // 2, 
                              hint, self.colors.attr(ColorPair.INFO))
            
        except curses.error:
            pass


def main():
    """Entry point."""
    def run_game(stdscr):
        config = GameConfig(
            username="user",
            theme="matrix",
            show_boot_animation=True,
        )
        game = Game(stdscr, config)
        game.run()
    
    curses.wrapper(run_game)


if __name__ == "__main__":
    main()
