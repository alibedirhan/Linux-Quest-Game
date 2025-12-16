"""Core systems: terminal, colors, game loop, audio, achievements."""

from .colors import ColorManager, ColorPair, Theme, THEMES
from .terminal import Terminal, Key, KeyEvent, InputLine
from .game import Game, GameConfig, GameState
from .audio import AudioManager, AudioConfig, SoundEffect, get_audio, play_sound
from .achievements import (
    Achievement, AchievementManager, AchievementCategory, AchievementRarity,
    GameStatistics, UnlockedAchievement, ACHIEVEMENTS
)

__all__ = [
    "ColorManager", "ColorPair", "Theme", "THEMES",
    "Terminal", "Key", "KeyEvent", "InputLine", 
    "Game", "GameConfig", "GameState",
    "AudioManager", "AudioConfig", "SoundEffect", "get_audio", "play_sound",
    "Achievement", "AchievementManager", "AchievementCategory", "AchievementRarity",
    "GameStatistics", "UnlockedAchievement", "ACHIEVEMENTS",
]
