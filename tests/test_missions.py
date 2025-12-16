"""
Tests for Mission System
========================
"""

import pytest
from src.simulation.filesystem import VirtualFileSystem
from src.missions.missions import (
    Mission, Task, MissionLoader, TaskValidator, 
    PlayerProgress, Difficulty
)


class TestTask:
    """Test Task class."""
    
    def test_task_creation(self):
        """Task should be created with required fields."""
        task = Task(
            id="test_task",
            description="Test description",
        )
        assert task.id == "test_task"
        assert task.description == "Test description"
        assert task.points == 10  # default
    
    def test_task_with_all_fields(self):
        """Task should accept all fields."""
        task = Task(
            id="full_task",
            description="Full task",
            hint="Use this hint",
            accepted_commands=["pwd", "ls"],
            check_cwd="/home/user",
            check_exists="file.txt",
            check_not_exists="deleted.txt",
            success_message="Well done!",
            points=20,
        )
        assert task.hint == "Use this hint"
        assert task.points == 20
        assert len(task.accepted_commands) == 2


class TestMission:
    """Test Mission class."""
    
    def test_mission_creation(self):
        """Mission should be created with required fields."""
        mission = Mission(
            id="test_mission",
            name="Test Mission",
            description="A test mission",
            difficulty=Difficulty.EASY,
            tasks=[
                Task(id="t1", description="Task 1"),
                Task(id="t2", description="Task 2"),
            ],
        )
        assert mission.id == "test_mission"
        assert mission.name == "Test Mission"
        assert len(mission.tasks) == 2
    
    def test_mission_total_points(self):
        """Mission should calculate total points."""
        mission = Mission(
            id="test",
            name="Test",
            description="Test",
            difficulty=Difficulty.EASY,
            tasks=[
                Task(id="t1", description="T1", points=10),
                Task(id="t2", description="T2", points=20),
            ],
        )
        assert mission.total_points == 30


class TestDifficulty:
    """Test Difficulty enum."""
    
    def test_difficulty_values(self):
        """Difficulty should have all expected values."""
        assert Difficulty.TUTORIAL.value == 1
        assert Difficulty.EASY.value == 2
        assert Difficulty.MEDIUM.value == 3
        assert Difficulty.HARD.value == 4
        assert Difficulty.EXPERT.value == 5
    
    def test_difficulty_to_turkish(self):
        """Difficulty should have Turkish names."""
        assert Difficulty.TUTORIAL.to_turkish() == "Eğitim"
        assert Difficulty.EASY.to_turkish() == "Kolay"
        assert Difficulty.HARD.to_turkish() == "Zor"


class TestMissionLoader:
    """Test MissionLoader class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.loader = MissionLoader()
    
    def test_loads_builtin_missions(self):
        """Built-in missions should be loaded."""
        missions = self.loader.get_all_missions()
        assert len(missions) >= 5
    
    def test_get_mission_by_id(self):
        """Should get mission by ID."""
        mission = self.loader.get_mission("basics")
        assert mission is not None
        assert mission.name == "Temel Komutlar"
    
    def test_get_nonexistent_mission(self):
        """Nonexistent mission should return None."""
        mission = self.loader.get_mission("nonexistent")
        assert mission is None
    
    def test_mission_prerequisites(self):
        """Missions should have prerequisites."""
        files_mission = self.loader.get_mission("files")
        assert "basics" in files_mission.prerequisites
    
    def test_mission_unlocks(self):
        """Missions should unlock other missions."""
        basics = self.loader.get_mission("basics")
        assert "files" in basics.unlocks
    
    def test_get_available_missions(self):
        """Should filter by completed prerequisites."""
        # No missions completed - only basics available
        available = self.loader.get_available_missions([])
        mission_ids = [m.id for m in available]
        assert "basics" in mission_ids
        
        # basics completed - files and explore available
        available = self.loader.get_available_missions(["basics"])
        mission_ids = [m.id for m in available]
        assert "files" in mission_ids
        assert "explore" in mission_ids


class TestTaskValidator:
    """Test TaskValidator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.fs = VirtualFileSystem("testuser")
        self.validator = TaskValidator(self.fs)
    
    def test_validate_by_file_exists(self):
        """Should validate by file existence."""
        task = Task(
            id="create_file",
            description="Create a file",
            check_exists="myfile.txt",
            success_message="File created!",
        )
        
        # File doesn't exist
        success, msg = self.validator.validate(task, "touch myfile.txt")
        assert not success
        
        # Create file
        self.fs.touch("myfile.txt")
        success, msg = self.validator.validate(task, "touch myfile.txt")
        assert success
        assert msg == "File created!"
    
    def test_validate_by_file_not_exists(self):
        """Should validate by file non-existence."""
        task = Task(
            id="delete_file",
            description="Delete a file",
            check_not_exists="todelete.txt",
            success_message="File deleted!",
        )
        
        # File exists
        self.fs.touch("todelete.txt")
        success, msg = self.validator.validate(task, "rm todelete.txt")
        assert not success
        
        # Delete file
        self.fs.rm("todelete.txt")
        success, msg = self.validator.validate(task, "rm todelete.txt")
        assert success
    
    def test_validate_by_cwd(self):
        """Should validate by current directory."""
        task = Task(
            id="goto_documents",
            description="Go to Documents",
            check_cwd="~/Documents",
            success_message="You're in Documents!",
        )
        
        # Wrong directory
        success, msg = self.validator.validate(task, "cd Documents")
        assert not success
        
        # Correct directory
        self.fs.cd("Documents")
        success, msg = self.validator.validate(task, "cd Documents")
        assert success
    
    def test_validate_by_accepted_commands(self):
        """Should validate by accepted commands when no file checks."""
        task = Task(
            id="run_pwd",
            description="Run pwd",
            accepted_commands=["pwd"],
            success_message="Correct!",
        )
        
        # Wrong command
        success, msg = self.validator.validate(task, "ls")
        assert not success
        
        # Correct command
        success, msg = self.validator.validate(task, "pwd")
        assert success
    
    def test_validate_alternative_methods(self):
        """Should accept alternative methods for file creation."""
        task = Task(
            id="create_readme",
            description="Create README.md",
            accepted_commands=["touch README.md"],
            check_exists="README.md",
            success_message="README created!",
        )
        
        # Create with echo redirect
        self.fs.touch("README.md")  # Simulating echo > README.md
        success, msg = self.validator.validate(task, "echo test > README.md")
        assert success  # Should pass because file exists


class TestPlayerProgress:
    """Test PlayerProgress class."""
    
    def test_progress_creation(self):
        """Progress should be created with defaults."""
        progress = PlayerProgress()
        assert progress.completed_missions == []
        assert progress.total_score == 0
    
    def test_progress_to_dict(self):
        """Progress should serialize to dict."""
        progress = PlayerProgress(
            completed_missions=["basics", "files"],
            total_score=120,
        )
        data = progress.to_dict()
        assert data["completed_missions"] == ["basics", "files"]
        assert data["total_score"] == 120
    
    def test_progress_from_dict(self):
        """Progress should deserialize from dict."""
        data = {
            "completed_missions": ["basics"],
            "total_score": 60,
            "hints_used": 2,
        }
        progress = PlayerProgress.from_dict(data)
        assert progress.completed_missions == ["basics"]
        assert progress.total_score == 60
        assert progress.hints_used == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
