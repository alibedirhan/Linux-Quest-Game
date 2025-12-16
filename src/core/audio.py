"""
Linux Command Quest - Audio System
===================================

Optional audio system for sound effects and ambient music.
Falls back silently if audio libraries are not available.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

# Try to import audio library
AUDIO_AVAILABLE = False
sa = None
try:
    import simpleaudio as sa
    AUDIO_AVAILABLE = True
except ImportError:
    pass

# Alternative: try pygame (lazy initialization)
PYGAME_AVAILABLE = False
pygame = None
try:
    import pygame as _pygame
    pygame = _pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pass


class SoundEffect(Enum):
    """Available sound effects."""
    
    KEYPRESS = auto()       # Tuş basma
    ENTER = auto()          # Enter tuşu
    SUCCESS = auto()        # Görev tamamlama
    ERROR = auto()          # Hata
    HINT = auto()           # İpucu
    MISSION_START = auto()  # Misyon başlangıç
    MISSION_COMPLETE = auto()  # Misyon tamamlama
    BOOT = auto()           # Boot sesi
    MENU_MOVE = auto()      # Menü navigasyon
    MENU_SELECT = auto()    # Menü seçim
    WARNING = auto()        # Uyarı
    NOTIFICATION = auto()   # Bildirim


@dataclass
class AudioConfig:
    """Audio configuration."""
    
    enabled: bool = True
    sfx_volume: float = 0.7      # 0.0 - 1.0
    music_volume: float = 0.3   # 0.0 - 1.0
    keypress_sound: bool = False  # Her tuşta ses (rahatsız edici olabilir)


class AudioManager:
    """
    Manages game audio - sound effects and background music.
    
    Usage:
        audio = AudioManager()
        audio.play(SoundEffect.SUCCESS)
        audio.play_music("ambient")
    """
    
    def __init__(self, config: AudioConfig | None = None):
        self.config = config or AudioConfig()
        self._sounds: dict[SoundEffect, any] = {}
        self._music_thread: threading.Thread | None = None
        self._music_playing = False
        self._initialized = False
        
        # Find sounds directory
        self._sounds_dir = self._find_sounds_dir()
        
        # Initialize if audio available
        if self.config.enabled and (AUDIO_AVAILABLE or PYGAME_AVAILABLE):
            self._initialize()
    
    def _find_sounds_dir(self) -> Path | None:
        """Find the sounds directory."""
        possible_paths = [
            Path(__file__).parent.parent.parent / "data" / "sounds",
            Path.cwd() / "data" / "sounds",
            Path.home() / ".linux-quest" / "sounds",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return possible_paths[0]  # Default, will be created
    
    def _initialize(self):
        """Initialize audio system and generate sounds."""
        if not self._sounds_dir:
            return
        
        # Initialize pygame mixer if using pygame
        if PYGAME_AVAILABLE and not AUDIO_AVAILABLE:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                return
        
        # Create sounds directory if needed
        self._sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate sounds if they don't exist
        self._generate_sounds()
        
        # Load sounds
        self._load_sounds()
        
        self._initialized = True
    
    def _generate_sounds(self):
        """Generate basic sound effects using wave synthesis."""
        import wave
        import struct
        import math
        
        def generate_wave(filename: str, frequency: float, duration: float, 
                         wave_type: str = "sine", fade: bool = True,
                         volume: float = 0.5):
            """Generate a WAV file with given parameters."""
            filepath = self._sounds_dir / filename
            
            if filepath.exists():
                return  # Don't regenerate
            
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            
            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                
                # Generate wave
                if wave_type == "sine":
                    value = math.sin(2 * math.pi * frequency * t)
                elif wave_type == "square":
                    value = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
                elif wave_type == "sawtooth":
                    value = 2 * (t * frequency - math.floor(t * frequency + 0.5))
                elif wave_type == "noise":
                    import random
                    value = random.uniform(-1, 1)
                else:
                    value = math.sin(2 * math.pi * frequency * t)
                
                # Apply fade in/out
                if fade:
                    fade_samples = int(0.01 * sample_rate)  # 10ms fade
                    if i < fade_samples:
                        value *= i / fade_samples
                    elif i > num_samples - fade_samples:
                        value *= (num_samples - i) / fade_samples
                
                # Apply volume and convert to 16-bit
                value = int(value * volume * 32767)
                samples.append(value)
            
            # Write WAV file
            with wave.open(str(filepath), 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                for sample in samples:
                    wav.writeframes(struct.pack('<h', max(-32768, min(32767, sample))))
        
        def generate_multi_tone(filename: str, tones: list[tuple], duration: float):
            """Generate multi-frequency sound."""
            filepath = self._sounds_dir / filename
            
            if filepath.exists():
                return
            
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            
            samples = []
            for i in range(num_samples):
                t = i / sample_rate
                value = 0
                
                for freq, vol, wave_type in tones:
                    if wave_type == "sine":
                        value += vol * math.sin(2 * math.pi * freq * t)
                    elif wave_type == "square":
                        value += vol * (1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0)
                
                # Fade
                fade_samples = int(0.02 * sample_rate)
                if i < fade_samples:
                    value *= i / fade_samples
                elif i > num_samples - fade_samples:
                    value *= (num_samples - i) / fade_samples
                
                value = int(value * 32767 / len(tones))
                samples.append(max(-32768, min(32767, value)))
            
            with wave.open(str(filepath), 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                for sample in samples:
                    wav.writeframes(struct.pack('<h', sample))
        
        # Generate sound effects
        try:
            # Keypress - short click
            generate_wave("keypress.wav", 800, 0.02, "square", volume=0.2)
            
            # Enter - slightly longer
            generate_wave("enter.wav", 600, 0.05, "sine", volume=0.3)
            
            # Success - pleasant rising tone
            generate_multi_tone("success.wav", [
                (523, 0.4, "sine"),  # C5
                (659, 0.3, "sine"),  # E5
                (784, 0.3, "sine"),  # G5
            ], 0.2)
            
            # Error - harsh low tone
            generate_wave("error.wav", 200, 0.15, "square", volume=0.3)
            
            # Hint - gentle notification
            generate_multi_tone("hint.wav", [
                (880, 0.5, "sine"),   # A5
                (1108, 0.3, "sine"),  # C#6
            ], 0.12)
            
            # Mission start - dramatic
            generate_multi_tone("mission_start.wav", [
                (330, 0.4, "sine"),  # E4
                (440, 0.3, "sine"),  # A4
                (554, 0.3, "sine"),  # C#5
            ], 0.3)
            
            # Mission complete - triumphant
            generate_multi_tone("mission_complete.wav", [
                (523, 0.3, "sine"),  # C5
                (659, 0.3, "sine"),  # E5
                (784, 0.3, "sine"),  # G5
                (1047, 0.2, "sine"), # C6
            ], 0.4)
            
            # Boot - tech sound
            generate_wave("boot.wav", 440, 0.1, "sawtooth", volume=0.3)
            
            # Menu move - subtle
            generate_wave("menu_move.wav", 1200, 0.02, "sine", volume=0.15)
            
            # Menu select - confirmation
            generate_wave("menu_select.wav", 880, 0.08, "sine", volume=0.25)
            
            # Warning - attention
            generate_multi_tone("warning.wav", [
                (440, 0.5, "square"),
                (880, 0.3, "square"),
            ], 0.1)
            
            # Notification - soft ping
            generate_wave("notification.wav", 1320, 0.08, "sine", volume=0.2)
            
        except Exception as e:
            print(f"Warning: Could not generate sounds: {e}")
    
    def _load_sounds(self):
        """Load sound files into memory."""
        sound_files = {
            SoundEffect.KEYPRESS: "keypress.wav",
            SoundEffect.ENTER: "enter.wav",
            SoundEffect.SUCCESS: "success.wav",
            SoundEffect.ERROR: "error.wav",
            SoundEffect.HINT: "hint.wav",
            SoundEffect.MISSION_START: "mission_start.wav",
            SoundEffect.MISSION_COMPLETE: "mission_complete.wav",
            SoundEffect.BOOT: "boot.wav",
            SoundEffect.MENU_MOVE: "menu_move.wav",
            SoundEffect.MENU_SELECT: "menu_select.wav",
            SoundEffect.WARNING: "warning.wav",
            SoundEffect.NOTIFICATION: "notification.wav",
        }
        
        for effect, filename in sound_files.items():
            filepath = self._sounds_dir / filename
            if filepath.exists():
                try:
                    if AUDIO_AVAILABLE and sa is not None:
                        self._sounds[effect] = sa.WaveObject.from_wave_file(str(filepath))
                    elif PYGAME_AVAILABLE and pygame is not None:
                        self._sounds[effect] = pygame.mixer.Sound(str(filepath))
                except Exception as e:
                    pass  # Skip this sound file
    
    def play(self, effect: SoundEffect):
        """
        Play a sound effect.
        
        Non-blocking - sound plays in background.
        """
        if not self.config.enabled:
            return
            
        if not self._initialized:
            return
        
        # Skip keypress if disabled
        if effect == SoundEffect.KEYPRESS and not self.config.keypress_sound:
            return
        
        if effect not in self._sounds:
            return
        
        try:
            sound = self._sounds[effect]
            
            if AUDIO_AVAILABLE and sa is not None:
                sound.play()
            elif PYGAME_AVAILABLE and pygame is not None:
                sound.set_volume(self.config.sfx_volume)
                sound.play()
                
        except Exception as e:
            # Silently ignore audio errors
            pass
    
    def play_music(self, track: str = "ambient"):
        """Start background music loop."""
        # TODO: Implement background music
        pass
    
    def stop_music(self):
        """Stop background music."""
        self._music_playing = False
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume (0.0 - 1.0)."""
        self.config.sfx_volume = max(0.0, min(1.0, volume))
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 - 1.0)."""
        self.config.music_volume = max(0.0, min(1.0, volume))
    
    def toggle_sfx(self) -> bool:
        """Toggle sound effects on/off. Returns new state."""
        self.config.enabled = not self.config.enabled
        return self.config.enabled
    
    def toggle_keypress_sound(self) -> bool:
        """Toggle keypress sounds. Returns new state."""
        self.config.keypress_sound = not self.config.keypress_sound
        return self.config.keypress_sound
    
    @property
    def is_available(self) -> bool:
        """Check if audio system is available."""
        return AUDIO_AVAILABLE or PYGAME_AVAILABLE
    
    @property  
    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self.config.enabled and self._initialized


# Global audio instance (lazy initialization)
_audio_manager: AudioManager | None = None


def get_audio() -> AudioManager:
    """Get global audio manager instance."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


def play_sound(effect: SoundEffect):
    """Convenience function to play a sound."""
    get_audio().play(effect)
