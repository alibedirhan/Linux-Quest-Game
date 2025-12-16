"""
Tests for Achievement System
============================
"""

import pytest
from src.core.achievements import (
    Achievement, AchievementManager, AchievementCategory, AchievementRarity,
    GameStatistics, UnlockedAchievement, ACHIEVEMENTS
)


class TestGameStatistics:
    """Test GameStatistics class."""
    
    def test_initial_values(self):
        """Statistics should start at zero."""
        stats = GameStatistics()
        assert stats.total_commands == 0
        assert stats.total_errors == 0
        assert stats.missions_completed == 0
    
    def test_increment_command(self):
        """Command tracking should work."""
        stats = GameStatistics()
        stats.increment_command("ls -la")
        stats.increment_command("pwd")
        stats.increment_command("ls")
        
        assert stats.total_commands == 3
        assert stats.commands_by_type["ls"] == 2
        assert stats.commands_by_type["pwd"] == 1
        assert "ls" in stats.unique_commands_used
        assert "pwd" in stats.unique_commands_used
    
    def test_visit_directory(self):
        """Directory tracking should work."""
        stats = GameStatistics()
        stats.visit_directory("/home/user")
        stats.visit_directory("/etc")
        stats.visit_directory("/home/user")  # Duplicate
        
        assert len(stats.visited_directories) == 2
    
    def test_combo_tracking(self):
        """Combo tracking should work."""
        stats = GameStatistics()
        
        for i in range(5):
            stats.increment_command("pwd")
        
        assert stats.correct_commands_streak == 5
        assert stats.best_combo == 5
        
        stats.increment_error()
        assert stats.correct_commands_streak == 0
        assert stats.best_combo == 5  # Best preserved
    
    def test_mission_completion(self):
        """Mission completion tracking should work."""
        stats = GameStatistics()
        stats.start_mission()
        
        time, perfect = stats.complete_mission("test_mission")
        
        assert stats.missions_completed == 1
        assert stats.current_streak == 1
        assert time >= 0
    
    def test_perfect_mission(self):
        """Perfect mission detection should work."""
        stats = GameStatistics()
        stats.start_mission()
        # No errors, no hints
        time, perfect = stats.complete_mission("test")
        assert perfect
        assert stats.missions_perfect == 1
        
        stats.start_mission()
        stats.use_hint()
        time, perfect = stats.complete_mission("test2")
        assert not perfect
        assert stats.missions_perfect == 1  # Still 1
    
    def test_serialization(self):
        """Stats should serialize and deserialize."""
        stats = GameStatistics()
        stats.increment_command("ls")
        stats.visit_directory("/home")
        stats.missions_completed = 3
        
        data = stats.to_dict()
        restored = GameStatistics.from_dict(data)
        
        assert restored.total_commands == 1
        assert restored.missions_completed == 3


class TestAchievementManager:
    """Test AchievementManager class."""
    
    def test_all_achievements_loaded(self):
        """All achievements should be loaded."""
        manager = AchievementManager()
        assert len(manager.get_all_achievements()) == len(ACHIEVEMENTS)
    
    def test_unlock_achievement(self):
        """Manual unlock should work."""
        manager = AchievementManager()
        
        assert not manager.is_unlocked("first_steps")
        result = manager.unlock("first_steps")
        assert result
        assert manager.is_unlocked("first_steps")
        
        # Can't unlock twice
        result = manager.unlock("first_steps")
        assert not result
    
    def test_auto_unlock_on_command(self):
        """Achievements should auto-unlock based on conditions."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        # First command should unlock "first_steps"
        stats.increment_command("pwd")
        manager.check_command("pwd", stats)
        
        assert manager.is_unlocked("first_steps")
    
    def test_command_count_achievement(self):
        """Command count achievements should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        for i in range(10):
            stats.increment_command("ls")
            manager.check_command("ls", stats)
        
        assert manager.is_unlocked("getting_started")  # 10 commands
    
    def test_unique_dirs_achievement(self):
        """Directory visit achievements should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        for i in range(10):
            stats.visit_directory(f"/dir{i}")
            stats.increment_command("cd")
            manager.check_command("cd", stats)
        
        assert manager.is_unlocked("explorer")  # 10 unique dirs
    
    def test_specific_command_achievement(self):
        """Specific command achievements should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        stats.increment_command("whoami")
        manager.check_command("whoami", stats)
        
        assert manager.is_unlocked("identity_crisis")
    
    def test_pending_notifications(self):
        """Pending notifications should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        stats.increment_command("pwd")
        manager.check_command("pwd", stats)
        
        pending = manager.get_pending_notifications()
        assert len(pending) > 0
        assert pending[0].id == "first_steps"
        
        # Should be cleared
        pending2 = manager.get_pending_notifications()
        assert len(pending2) == 0
    
    def test_calculate_points(self):
        """Point calculation should work."""
        manager = AchievementManager()
        
        manager.unlock("first_steps")  # 10 points
        manager.unlock("getting_started")  # 10 points
        
        assert manager.calculate_total_points() == 20
    
    def test_mission_complete_achievements(self):
        """Mission completion achievements should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        stats.start_mission()
        time, perfect = stats.complete_mission("test")
        
        manager.check_mission_complete(time, perfect, stats)
        
        assert manager.is_unlocked("first_mission")
        assert manager.is_unlocked("flawless")  # Perfect
    
    def test_combo_achievement(self):
        """Combo achievements should work."""
        manager = AchievementManager()
        stats = GameStatistics()
        
        for i in range(5):
            stats.increment_command("ls")
            manager.check_command("ls", stats)
        
        assert manager.is_unlocked("combo_starter")  # 5 combo
    
    def test_serialization(self):
        """Manager state should serialize and deserialize."""
        manager = AchievementManager()
        manager.unlock("first_steps")
        manager.unlock("reader")
        manager._pipe_used = True
        
        data = manager.to_dict()
        
        manager2 = AchievementManager()
        manager2.from_dict(data)
        
        assert manager2.is_unlocked("first_steps")
        assert manager2.is_unlocked("reader")
        assert manager2._pipe_used


class TestAchievementRarity:
    """Test AchievementRarity enum."""
    
    def test_rarity_values(self):
        """Rarity should have correct values."""
        assert AchievementRarity.COMMON.value == 1
        assert AchievementRarity.LEGENDARY.value == 5
    
    def test_turkish_names(self):
        """Turkish names should work."""
        assert AchievementRarity.COMMON.to_turkish() == "Yaygın"
        assert AchievementRarity.LEGENDARY.to_turkish() == "Efsane"
    
    def test_icons(self):
        """Icons should be defined."""
        assert AchievementRarity.COMMON.to_icon() == "🥉"
        assert AchievementRarity.LEGENDARY.to_icon() == "🏆"


class TestAchievementCategory:
    """Test AchievementCategory enum."""
    
    def test_turkish_names(self):
        """Turkish names should work."""
        assert AchievementCategory.EXPLORATION.to_turkish() == "Keşif"
        assert AchievementCategory.FILE_MASTER.to_turkish() == "Dosya Ustası"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
