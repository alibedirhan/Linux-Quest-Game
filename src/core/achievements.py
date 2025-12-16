"""
Linux Command Quest - Achievement System
=========================================

Comprehensive achievement and statistics tracking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING


class AchievementCategory(Enum):
    """Achievement categories."""
    EXPLORATION = auto()    # Navigasyon ve keşif
    FILE_MASTER = auto()    # Dosya işlemleri
    TEXT_WIZARD = auto()    # Metin işleme
    SPEED_DEMON = auto()    # Hız başarıları
    PERFECTIONIST = auto()  # Hatasız tamamlama
    DEDICATION = auto()     # Süreklilik
    SPECIAL = auto()        # Özel başarılar
    
    def to_turkish(self) -> str:
        names = {
            AchievementCategory.EXPLORATION: "Keşif",
            AchievementCategory.FILE_MASTER: "Dosya Ustası",
            AchievementCategory.TEXT_WIZARD: "Metin Büyücüsü",
            AchievementCategory.SPEED_DEMON: "Hız Şeytanı",
            AchievementCategory.PERFECTIONIST: "Mükemmeliyetçi",
            AchievementCategory.DEDICATION: "Azim",
            AchievementCategory.SPECIAL: "Özel",
        }
        return names.get(self, "?")


class AchievementRarity(Enum):
    """Achievement rarity levels."""
    COMMON = 1       # Yaygın - Bronz
    UNCOMMON = 2     # Nadir - Gümüş
    RARE = 3         # Çok Nadir - Altın
    EPIC = 4         # Efsanevi - Platin
    LEGENDARY = 5    # Efsane - Elmas
    
    def to_turkish(self) -> str:
        names = {
            AchievementRarity.COMMON: "Yaygın",
            AchievementRarity.UNCOMMON: "Nadir",
            AchievementRarity.RARE: "Çok Nadir",
            AchievementRarity.EPIC: "Efsanevi",
            AchievementRarity.LEGENDARY: "Efsane",
        }
        return names.get(self, "?")
    
    def to_icon(self) -> str:
        """Return icon for this rarity."""
        icons = {
            AchievementRarity.COMMON: "🥉",
            AchievementRarity.UNCOMMON: "🥈",
            AchievementRarity.RARE: "🥇",
            AchievementRarity.EPIC: "💎",
            AchievementRarity.LEGENDARY: "🏆",
        }
        return icons.get(self, "⭐")


@dataclass
class Achievement:
    """An achievement definition."""
    
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str = "🏅"
    hidden: bool = False  # Hidden until unlocked
    points: int = 10
    
    # Unlock conditions
    condition_type: str = ""
    condition_value: int = 0
    condition_extra: str = ""


@dataclass
class UnlockedAchievement:
    """A player's unlocked achievement."""
    
    achievement_id: str
    unlocked_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "achievement_id": self.achievement_id,
            "unlocked_at": self.unlocked_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UnlockedAchievement":
        return cls(
            achievement_id=data["achievement_id"],
            unlocked_at=datetime.fromisoformat(data["unlocked_at"]),
        )


@dataclass 
class GameStatistics:
    """Player statistics tracking."""
    
    # Command statistics
    total_commands: int = 0
    commands_by_type: dict = field(default_factory=dict)
    unique_commands_used: set = field(default_factory=set)
    
    # Directory tracking
    visited_directories: set = field(default_factory=set)
    
    # Error tracking
    total_errors: int = 0
    errors_this_mission: int = 0
    
    # Time tracking
    total_play_time: float = 0.0
    session_start: datetime | None = None
    mission_start: datetime | None = None
    
    # Mission statistics
    missions_completed: int = 0
    missions_perfect: int = 0
    hints_used_total: int = 0
    hints_used_this_mission: int = 0
    current_streak: int = 0
    best_streak: int = 0
    
    # Typing statistics
    total_keystrokes: int = 0
    
    # Session statistics
    total_sessions: int = 0
    
    # Speed records
    fastest_mission: dict = field(default_factory=dict)
    
    # Combo tracking
    correct_commands_streak: int = 0
    best_combo: int = 0
    
    def increment_command(self, command: str):
        """Record a command execution."""
        self.total_commands += 1
        self.correct_commands_streak += 1
        self.best_combo = max(self.best_combo, self.correct_commands_streak)
        
        base_cmd = command.split()[0] if command else ""
        if base_cmd:
            self.commands_by_type[base_cmd] = self.commands_by_type.get(base_cmd, 0) + 1
            self.unique_commands_used.add(base_cmd)
    
    def increment_error(self):
        """Record an error."""
        self.total_errors += 1
        self.errors_this_mission += 1
        self.correct_commands_streak = 0
    
    def visit_directory(self, path: str):
        """Record a directory visit."""
        self.visited_directories.add(path)
    
    def use_hint(self):
        """Record hint usage."""
        self.hints_used_total += 1
        self.hints_used_this_mission += 1
    
    def start_session(self):
        """Start a new session."""
        self.session_start = datetime.now()
        self.total_sessions += 1
    
    def end_session(self):
        """End current session."""
        if self.session_start:
            elapsed = (datetime.now() - self.session_start).total_seconds()
            self.total_play_time += elapsed
            self.session_start = None
    
    def start_mission(self):
        """Start a mission."""
        self.mission_start = datetime.now()
        self.errors_this_mission = 0
        self.hints_used_this_mission = 0
    
    def complete_mission(self, mission_id: str) -> tuple[float, bool]:
        """
        Record mission completion.
        Returns (time_seconds, was_perfect).
        """
        time_seconds = 0.0
        if self.mission_start:
            time_seconds = (datetime.now() - self.mission_start).total_seconds()
        
        self.missions_completed += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        
        was_perfect = self.errors_this_mission == 0 and self.hints_used_this_mission == 0
        if was_perfect:
            self.missions_perfect += 1
        
        # Record speed
        if mission_id not in self.fastest_mission or time_seconds < self.fastest_mission[mission_id]:
            self.fastest_mission[mission_id] = time_seconds
        
        self.mission_start = None
        return time_seconds, was_perfect
    
    def reset_streak(self):
        """Reset streak on mission failure/quit."""
        self.current_streak = 0
    
    def to_dict(self) -> dict:
        return {
            "total_commands": self.total_commands,
            "commands_by_type": self.commands_by_type,
            "unique_commands_used": list(self.unique_commands_used),
            "visited_directories": list(self.visited_directories),
            "total_errors": self.total_errors,
            "total_play_time": self.total_play_time,
            "missions_completed": self.missions_completed,
            "missions_perfect": self.missions_perfect,
            "hints_used_total": self.hints_used_total,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "total_keystrokes": self.total_keystrokes,
            "total_sessions": self.total_sessions,
            "fastest_mission": self.fastest_mission,
            "best_combo": self.best_combo,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameStatistics":
        stats = cls()
        stats.total_commands = data.get("total_commands", 0)
        stats.commands_by_type = data.get("commands_by_type", {})
        stats.unique_commands_used = set(data.get("unique_commands_used", []))
        stats.visited_directories = set(data.get("visited_directories", []))
        stats.total_errors = data.get("total_errors", 0)
        stats.total_play_time = data.get("total_play_time", 0.0)
        stats.missions_completed = data.get("missions_completed", 0)
        stats.missions_perfect = data.get("missions_perfect", 0)
        stats.hints_used_total = data.get("hints_used_total", 0)
        stats.current_streak = data.get("current_streak", 0)
        stats.best_streak = data.get("best_streak", 0)
        stats.total_keystrokes = data.get("total_keystrokes", 0)
        stats.total_sessions = data.get("total_sessions", 0)
        stats.fastest_mission = data.get("fastest_mission", {})
        stats.best_combo = data.get("best_combo", 0)
        return stats


# All achievements definitions
ACHIEVEMENTS: list[Achievement] = [
    # === EXPLORATION ===
    Achievement(
        id="first_steps",
        name="İlk Adımlar",
        description="İlk komutunu çalıştır",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.COMMON,
        icon="👣",
        condition_type="total_commands",
        condition_value=1,
    ),
    Achievement(
        id="getting_started",
        name="Başlangıç",
        description="10 komut çalıştır",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.COMMON,
        icon="🚀",
        condition_type="total_commands",
        condition_value=10,
    ),
    Achievement(
        id="command_apprentice",
        name="Komut Çırağı",
        description="50 komut çalıştır",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="📚",
        condition_type="total_commands",
        condition_value=50,
        points=15,
    ),
    Achievement(
        id="command_master",
        name="Komut Ustası",
        description="200 komut çalıştır",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.RARE,
        icon="🎓",
        condition_type="total_commands",
        condition_value=200,
        points=25,
    ),
    Achievement(
        id="command_legend",
        name="Komut Efsanesi",
        description="500 komut çalıştır",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.EPIC,
        icon="👑",
        condition_type="total_commands",
        condition_value=500,
        points=50,
    ),
    Achievement(
        id="explorer",
        name="Kaşif",
        description="10 farklı dizini ziyaret et",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="🧭",
        condition_type="unique_dirs",
        condition_value=10,
        points=15,
    ),
    Achievement(
        id="world_traveler",
        name="Dünya Gezgini",
        description="25 farklı dizini ziyaret et",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.RARE,
        icon="🌍",
        condition_type="unique_dirs",
        condition_value=25,
        points=25,
    ),
    Achievement(
        id="root_explorer",
        name="Kök Gezgini",
        description="Kök dizinine git",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.COMMON,
        icon="🌳",
        condition_type="visited_dir",
        condition_extra="/",
    ),
    Achievement(
        id="etc_visitor",
        name="Sistem Meraklısı",
        description="/etc dizinini ziyaret et",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.COMMON,
        icon="⚙️",
        condition_type="visited_dir",
        condition_extra="/etc",
    ),
    Achievement(
        id="var_visitor",
        name="Log Avcısı",
        description="/var/log dizinini ziyaret et",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="📋",
        condition_type="visited_dir",
        condition_extra="/var/log",
    ),
    Achievement(
        id="polyglot",
        name="Çok Dilli",
        description="15 farklı komut kullan",
        category=AchievementCategory.EXPLORATION,
        rarity=AchievementRarity.RARE,
        icon="🗣️",
        condition_type="unique_commands",
        condition_value=15,
        points=25,
    ),
    
    # === FILE MASTER ===
    Achievement(
        id="first_file",
        name="İlk Dosya",
        description="İlk dosyanı oluştur",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.COMMON,
        icon="📄",
        condition_type="command_used",
        condition_extra="touch",
    ),
    Achievement(
        id="mkdir_beginner",
        name="Klasör Çırağı",
        description="5 klasör oluştur",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.COMMON,
        icon="📁",
        condition_type="command_count",
        condition_value=5,
        condition_extra="mkdir",
    ),
    Achievement(
        id="mkdir_master",
        name="Klasör Ustası",
        description="20 klasör oluştur",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.UNCOMMON,
        icon="🗂️",
        condition_type="command_count",
        condition_value=20,
        condition_extra="mkdir",
        points=15,
    ),
    Achievement(
        id="clean_freak",
        name="Temizlik Hastası",
        description="30 dosya veya klasör sil",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.RARE,
        icon="🧹",
        condition_type="command_count",
        condition_value=30,
        condition_extra="rm",
        points=25,
    ),
    Achievement(
        id="copy_ninja",
        name="Kopyalama Ninjası",
        description="20 dosya kopyala",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.UNCOMMON,
        icon="📋",
        condition_type="command_count",
        condition_value=20,
        condition_extra="cp",
        points=15,
    ),
    Achievement(
        id="mover",
        name="Taşıyıcı",
        description="15 dosya taşı",
        category=AchievementCategory.FILE_MASTER,
        rarity=AchievementRarity.UNCOMMON,
        icon="📦",
        condition_type="command_count",
        condition_value=15,
        condition_extra="mv",
        points=15,
    ),
    
    # === TEXT WIZARD ===
    Achievement(
        id="reader",
        name="Okuyucu",
        description="İlk dosyanı oku",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.COMMON,
        icon="📖",
        condition_type="command_used",
        condition_extra="cat",
    ),
    Achievement(
        id="bookworm",
        name="Kitap Kurdu",
        description="30 dosya oku",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.UNCOMMON,
        icon="📚",
        condition_type="command_count",
        condition_value=30,
        condition_extra="cat",
        points=15,
    ),
    Achievement(
        id="grep_beginner",
        name="Arama Çırağı",
        description="5 kez grep kullan",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.COMMON,
        icon="🔍",
        condition_type="command_count",
        condition_value=5,
        condition_extra="grep",
    ),
    Achievement(
        id="grep_master",
        name="Grep Ustası",
        description="25 kez grep kullan",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.RARE,
        icon="🔎",
        condition_type="command_count",
        condition_value=25,
        condition_extra="grep",
        points=25,
    ),
    Achievement(
        id="pipe_user",
        name="Boru Hattı",
        description="Pipe (|) kullan",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.UNCOMMON,
        icon="🔗",
        condition_type="special",
        condition_extra="pipe_used",
        points=15,
    ),
    Achievement(
        id="redirect_user",
        name="Yönlendirici",
        description="Çıktı yönlendirme (>) kullan",
        category=AchievementCategory.TEXT_WIZARD,
        rarity=AchievementRarity.COMMON,
        icon="➡️",
        condition_type="special",
        condition_extra="redirect_used",
    ),
    
    # === SPEED DEMON ===
    Achievement(
        id="quick_learner",
        name="Hızlı Öğrenci",
        description="Bir görevi 60 saniyede tamamla",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.UNCOMMON,
        icon="⚡",
        condition_type="mission_time",
        condition_value=60,
        points=15,
    ),
    Achievement(
        id="speed_runner",
        name="Hız Koşucusu",
        description="Bir görevi 30 saniyede tamamla",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.RARE,
        icon="🏃",
        condition_type="mission_time",
        condition_value=30,
        points=25,
    ),
    Achievement(
        id="flash",
        name="Şimşek",
        description="Bir görevi 15 saniyede tamamla",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.EPIC,
        icon="⚡",
        condition_type="mission_time",
        condition_value=15,
        points=50,
        hidden=True,
    ),
    Achievement(
        id="combo_starter",
        name="Kombo Başlangıcı",
        description="5 komut art arda doğru yap",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.COMMON,
        icon="🔥",
        condition_type="combo",
        condition_value=5,
    ),
    Achievement(
        id="combo_master",
        name="Kombo Ustası",
        description="15 komut art arda doğru yap",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.RARE,
        icon="💥",
        condition_type="combo",
        condition_value=15,
        points=25,
    ),
    Achievement(
        id="unstoppable",
        name="Durdurulamaz",
        description="30 komut art arda doğru yap",
        category=AchievementCategory.SPEED_DEMON,
        rarity=AchievementRarity.EPIC,
        icon="🌟",
        condition_type="combo",
        condition_value=30,
        points=50,
        hidden=True,
    ),
    
    # === PERFECTIONIST ===
    Achievement(
        id="no_hints",
        name="Yardımsız",
        description="Bir görevi ipucu kullanmadan tamamla",
        category=AchievementCategory.PERFECTIONIST,
        rarity=AchievementRarity.COMMON,
        icon="💪",
        condition_type="mission_no_hints",
        condition_value=1,
    ),
    Achievement(
        id="flawless",
        name="Kusursuz",
        description="Bir görevi hatasız tamamla",
        category=AchievementCategory.PERFECTIONIST,
        rarity=AchievementRarity.UNCOMMON,
        icon="✨",
        condition_type="mission_perfect",
        condition_value=1,
        points=15,
    ),
    Achievement(
        id="perfectionist",
        name="Mükemmeliyetçi",
        description="5 görevi hatasız tamamla",
        category=AchievementCategory.PERFECTIONIST,
        rarity=AchievementRarity.RARE,
        icon="💎",
        condition_type="missions_perfect",
        condition_value=5,
        points=30,
    ),
    Achievement(
        id="master_perfectionist",
        name="Usta Mükemmeliyetçi",
        description="Tüm görevleri hatasız tamamla",
        category=AchievementCategory.PERFECTIONIST,
        rarity=AchievementRarity.LEGENDARY,
        icon="🏆",
        condition_type="all_missions_perfect",
        condition_value=1,
        points=100,
        hidden=True,
    ),
    
    # === DEDICATION ===
    Achievement(
        id="first_mission",
        name="İlk Görev",
        description="İlk görevini tamamla",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.COMMON,
        icon="🎯",
        condition_type="missions_completed",
        condition_value=1,
    ),
    Achievement(
        id="dedicated",
        name="Azimli",
        description="3 görev tamamla",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="💼",
        condition_type="missions_completed",
        condition_value=3,
        points=15,
    ),
    Achievement(
        id="committed",
        name="Kararlı",
        description="Tüm görevleri tamamla",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.EPIC,
        icon="🌟",
        condition_type="missions_completed",
        condition_value=5,
        points=50,
    ),
    Achievement(
        id="streak_starter",
        name="Seri Başlangıcı",
        description="3 görev art arda tamamla",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.COMMON,
        icon="🔗",
        condition_type="streak",
        condition_value=3,
    ),
    Achievement(
        id="on_fire",
        name="Ateştesin!",
        description="5 görev art arda tamamla",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.RARE,
        icon="🔥",
        condition_type="streak",
        condition_value=5,
        points=30,
    ),
    Achievement(
        id="play_time_1h",
        name="Bir Saat",
        description="Toplam 1 saat oyna",
        category=AchievementCategory.DEDICATION,
        rarity=AchievementRarity.UNCOMMON,
        icon="⏰",
        condition_type="play_time",
        condition_value=3600,
        points=15,
    ),
    
    # === SPECIAL ===
    Achievement(
        id="curious",
        name="Meraklı",
        description="help komutunu kullan",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.COMMON,
        icon="❓",
        condition_type="command_used",
        condition_extra="help",
    ),
    Achievement(
        id="historian",
        name="Tarihçi",
        description="history komutunu kullan",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.COMMON,
        icon="📜",
        condition_type="command_used",
        condition_extra="history",
    ),
    Achievement(
        id="identity_crisis",
        name="Kimlik Krizi",
        description="whoami komutunu kullan",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.COMMON,
        icon="🤔",
        condition_type="command_used",
        condition_extra="whoami",
    ),
    Achievement(
        id="time_keeper",
        name="Zaman Tutucusu",
        description="date komutunu kullan",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.COMMON,
        icon="📅",
        condition_type="command_used",
        condition_extra="date",
    ),
    Achievement(
        id="system_info",
        name="Sistem Bilgisi",
        description="uname -a komutunu kullan",
        category=AchievementCategory.SPECIAL,
        rarity=AchievementRarity.UNCOMMON,
        icon="💻",
        condition_type="command_used",
        condition_extra="uname",
    ),
]


class AchievementManager:
    """Manages achievements and checks unlock conditions."""
    
    def __init__(self):
        self._achievements: dict[str, Achievement] = {a.id: a for a in ACHIEVEMENTS}
        self._unlocked: dict[str, UnlockedAchievement] = {}
        self._pending_notifications: list[Achievement] = []
        
        # Special trackers
        self._pipe_used = False
        self._redirect_used = False
    
    def get_achievement(self, achievement_id: str) -> Achievement | None:
        """Get achievement by ID."""
        return self._achievements.get(achievement_id)
    
    def get_all_achievements(self) -> list[Achievement]:
        """Get all achievement definitions."""
        return list(self._achievements.values())
    
    def get_unlocked(self) -> list[Achievement]:
        """Get list of unlocked achievements."""
        return [self._achievements[uid.achievement_id] 
                for uid in self._unlocked.values()
                if uid.achievement_id in self._achievements]
    
    def get_locked(self) -> list[Achievement]:
        """Get list of locked achievements (excluding hidden)."""
        return [a for a in self._achievements.values()
                if a.id not in self._unlocked and not a.hidden]
    
    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if achievement is unlocked."""
        return achievement_id in self._unlocked
    
    def get_pending_notifications(self) -> list[Achievement]:
        """Get and clear pending achievement notifications."""
        pending = self._pending_notifications.copy()
        self._pending_notifications.clear()
        return pending
    
    def unlock(self, achievement_id: str) -> bool:
        """Manually unlock an achievement."""
        if achievement_id in self._unlocked:
            return False
        
        if achievement_id not in self._achievements:
            return False
        
        self._unlocked[achievement_id] = UnlockedAchievement(achievement_id=achievement_id)
        self._pending_notifications.append(self._achievements[achievement_id])
        return True
    
    def check_command(self, command: str, stats: GameStatistics):
        """Check achievements after a command."""
        base_cmd = command.split()[0] if command else ""
        
        # Check for pipe/redirect usage
        if "|" in command:
            self._pipe_used = True
        if ">" in command:
            self._redirect_used = True
        
        # Check all achievements
        for achievement in self._achievements.values():
            if achievement.id in self._unlocked:
                continue
            
            if self._check_condition(achievement, stats, base_cmd):
                self.unlock(achievement.id)
    
    def check_mission_complete(self, mission_time: float, was_perfect: bool, stats: GameStatistics):
        """Check achievements after mission completion."""
        for achievement in self._achievements.values():
            if achievement.id in self._unlocked:
                continue
            
            ctype = achievement.condition_type
            cval = achievement.condition_value
            
            # Mission time achievements
            if ctype == "mission_time" and mission_time <= cval:
                self.unlock(achievement.id)
            
            # Perfect mission achievements
            elif ctype == "mission_perfect" and was_perfect:
                self.unlock(achievement.id)
            
            elif ctype == "mission_no_hints" and stats.hints_used_this_mission == 0:
                self.unlock(achievement.id)
            
            # Check other conditions
            elif self._check_condition(achievement, stats, ""):
                self.unlock(achievement.id)
    
    def _check_condition(self, achievement: Achievement, stats: GameStatistics, current_cmd: str) -> bool:
        """Check if achievement condition is met."""
        ctype = achievement.condition_type
        cval = achievement.condition_value
        cextra = achievement.condition_extra
        
        if ctype == "total_commands":
            return stats.total_commands >= cval
        
        elif ctype == "unique_dirs":
            return len(stats.visited_directories) >= cval
        
        elif ctype == "unique_commands":
            return len(stats.unique_commands_used) >= cval
        
        elif ctype == "visited_dir":
            return cextra in stats.visited_directories
        
        elif ctype == "command_used":
            return cextra in stats.unique_commands_used or current_cmd == cextra
        
        elif ctype == "command_count":
            return stats.commands_by_type.get(cextra, 0) >= cval
        
        elif ctype == "missions_completed":
            return stats.missions_completed >= cval
        
        elif ctype == "missions_perfect":
            return stats.missions_perfect >= cval
        
        elif ctype == "streak":
            return stats.current_streak >= cval
        
        elif ctype == "combo":
            return stats.best_combo >= cval
        
        elif ctype == "play_time":
            return stats.total_play_time >= cval
        
        elif ctype == "special":
            if cextra == "pipe_used":
                return self._pipe_used
            elif cextra == "redirect_used":
                return self._redirect_used
        
        return False
    
    def get_progress(self, achievement_id: str, stats: GameStatistics) -> tuple[int, int]:
        """Get progress towards an achievement (current, target)."""
        achievement = self._achievements.get(achievement_id)
        if not achievement:
            return 0, 1
        
        ctype = achievement.condition_type
        cval = achievement.condition_value
        cextra = achievement.condition_extra
        
        if ctype == "total_commands":
            return min(stats.total_commands, cval), cval
        elif ctype == "unique_dirs":
            return min(len(stats.visited_directories), cval), cval
        elif ctype == "unique_commands":
            return min(len(stats.unique_commands_used), cval), cval
        elif ctype == "command_count":
            return min(stats.commands_by_type.get(cextra, 0), cval), cval
        elif ctype == "missions_completed":
            return min(stats.missions_completed, cval), cval
        elif ctype == "missions_perfect":
            return min(stats.missions_perfect, cval), cval
        elif ctype == "streak":
            return min(stats.best_streak, cval), cval
        elif ctype == "combo":
            return min(stats.best_combo, cval), cval
        elif ctype == "play_time":
            return min(int(stats.total_play_time), cval), cval
        
        return 0, 1
    
    def calculate_total_points(self) -> int:
        """Calculate total achievement points earned."""
        total = 0
        for uid in self._unlocked.values():
            achievement = self._achievements.get(uid.achievement_id)
            if achievement:
                total += achievement.points
        return total
    
    def to_dict(self) -> dict:
        """Serialize unlocked achievements."""
        return {
            "unlocked": [ua.to_dict() for ua in self._unlocked.values()],
            "pipe_used": self._pipe_used,
            "redirect_used": self._redirect_used,
        }
    
    def from_dict(self, data: dict):
        """Load unlocked achievements."""
        self._unlocked.clear()
        for ua_data in data.get("unlocked", []):
            ua = UnlockedAchievement.from_dict(ua_data)
            self._unlocked[ua.achievement_id] = ua
        self._pipe_used = data.get("pipe_used", False)
        self._redirect_used = data.get("redirect_used", False)
