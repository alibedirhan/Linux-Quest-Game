"""
Linux Command Quest - Mission System
=====================================

JSON-based mission loading, validation, and progress tracking.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..simulation.filesystem import VirtualFileSystem


class Difficulty(Enum):
    """Mission difficulty levels."""
    TUTORIAL = auto()
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()
    EXPERT = auto()
    
    @classmethod
    def from_string(cls, s: str) -> "Difficulty":
        mapping = {
            "tutorial": cls.TUTORIAL,
            "kolay": cls.EASY,
            "easy": cls.EASY,
            "orta": cls.MEDIUM,
            "medium": cls.MEDIUM,
            "zor": cls.HARD,
            "hard": cls.HARD,
            "uzman": cls.EXPERT,
            "expert": cls.EXPERT,
        }
        return mapping.get(s.lower(), cls.EASY)
    
    def to_turkish(self) -> str:
        mapping = {
            Difficulty.TUTORIAL: "Eğitim",
            Difficulty.EASY: "Kolay",
            Difficulty.MEDIUM: "Orta",
            Difficulty.HARD: "Zor",
            Difficulty.EXPERT: "Uzman",
        }
        return mapping.get(self, "Kolay")
    
    def to_color(self) -> str:
        """Get ANSI color for difficulty."""
        mapping = {
            Difficulty.TUTORIAL: "\033[36m",  # Cyan
            Difficulty.EASY: "\033[32m",      # Green
            Difficulty.MEDIUM: "\033[33m",    # Yellow
            Difficulty.HARD: "\033[31m",      # Red
            Difficulty.EXPERT: "\033[35m",    # Magenta
        }
        return mapping.get(self, "\033[0m")


class ValidationType(Enum):
    """Types of task validation."""
    COMMAND = auto()          # Check exact command
    COMMAND_CONTAINS = auto() # Check command contains string
    CWD = auto()              # Check current directory
    FILE_EXISTS = auto()      # Check file exists
    FILE_NOT_EXISTS = auto()  # Check file doesn't exist
    FILE_CONTAINS = auto()    # Check file content
    CUSTOM = auto()           # Custom validation function


@dataclass
class TaskValidation:
    """Validation rule for a task."""
    
    type: ValidationType
    expected: Any
    message: str = ""


@dataclass
class Task:
    """A single task within a mission."""
    
    id: str
    description: str
    hint: str = ""
    validations: list[TaskValidation] = field(default_factory=list)
    points: int = 10
    success_message: str = ""
    
    # Accepted commands (for simple command matching)
    accepted_commands: list[str] = field(default_factory=list)
    
    # State checks
    check_cwd: str | None = None
    check_exists: str | None = None
    check_not_exists: str | None = None
    
    # Smart hints for F1 help (progressive hints)
    smart_hints: list[str] = field(default_factory=list)


@dataclass
class Mission:
    """A complete mission with multiple tasks."""
    
    id: str
    name: str
    description: str
    difficulty: Difficulty = Difficulty.EASY
    category: str = "tutorial"  # tutorial, hacker, sysadmin, etc.
    estimated_time: str = "5 dakika"
    prerequisites: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    
    # Filesystem setup
    fs_create: list[dict] = field(default_factory=list)
    
    # Completion rewards
    completion_message: str = ""
    unlocks: list[str] = field(default_factory=list)
    total_points: int = 0
    
    def __post_init__(self):
        if self.total_points == 0:
            self.total_points = sum(t.points for t in self.tasks)


@dataclass
class PlayerProgress:
    """Tracks player's progress across missions."""
    
    completed_missions: list[str] = field(default_factory=list)
    current_mission: str | None = None
    current_task_index: int = 0
    total_score: int = 0
    hints_used: int = 0
    achievements: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    
    def to_dict(self) -> dict:
        return {
            "completed_missions": self.completed_missions,
            "current_mission": self.current_mission,
            "current_task_index": self.current_task_index,
            "total_score": self.total_score,
            "hints_used": self.hints_used,
            "achievements": self.achievements,
            "start_time": self.start_time.isoformat() if self.start_time else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PlayerProgress":
        progress = cls(
            completed_missions=data.get("completed_missions", []),
            current_mission=data.get("current_mission"),
            current_task_index=data.get("current_task_index", 0),
            total_score=data.get("total_score", 0),
            hints_used=data.get("hints_used", 0),
            achievements=data.get("achievements", []),
        )
        if data.get("start_time"):
            progress.start_time = datetime.fromisoformat(data["start_time"])
        return progress


class MissionLoader:
    """Loads missions from JSON files."""
    
    def __init__(self, missions_dir: Path | str | None = None):
        if missions_dir:
            self.missions_dir = Path(missions_dir)
        else:
            self.missions_dir = None
        self._missions: dict[str, Mission] = {}
        self._load_builtin_missions()
    
    def _load_builtin_missions(self):
        """Load built-in missions."""
        # Mission 1: Basic Commands
        self._missions["basics"] = Mission(
            id="basics",
            name="Temel Komutlar",
            description="Linux terminalinin temel komutlarını öğren: pwd, ls, cd",
            difficulty=Difficulty.TUTORIAL,
            estimated_time="5 dakika",
            tasks=[
                Task(
                    id="pwd",
                    description="Mevcut dizini göster",
                    hint="'pwd' komutunu kullan (Print Working Directory)",
                    accepted_commands=["pwd"],
                    success_message="Harika! pwd komutu bulunduğun dizini gösterir.",
                ),
                Task(
                    id="ls",
                    description="Dizin içeriğini listele",
                    hint="'ls' komutunu kullan (List)",
                    accepted_commands=["ls"],
                    success_message="Süper! ls komutu dizin içeriğini listeler.",
                ),
                Task(
                    id="ls_hidden",
                    description="Gizli dosyaları da göster",
                    hint="'ls -a' veya 'ls -la' kullan (-a = all)",
                    accepted_commands=["ls -a", "ls -la", "ls -al", "ls --all"],
                    success_message="Mükemmel! -a bayrağı gizli dosyaları gösterir.",
                ),
                Task(
                    id="cd_docs",
                    description="Documents klasörüne git",
                    hint="'cd Documents' komutunu kullan",
                    accepted_commands=["cd Documents", "cd Documents/"],
                    check_cwd="~/Documents",
                    success_message="Bravo! cd komutu ile dizin değiştirdin.",
                ),
                Task(
                    id="cd_parent",
                    description="Üst dizine çık",
                    hint="'cd ..' komutunu kullan (.. = üst dizin)",
                    accepted_commands=["cd .."],
                    success_message="Harika! .. her zaman üst dizini temsil eder.",
                ),
                Task(
                    id="cd_home",
                    description="Ev dizinine dön",
                    hint="'cd ~' veya sadece 'cd' kullan",
                    accepted_commands=["cd ~", "cd", "cd ~/", "cd $HOME"],
                    check_cwd="~",
                    success_message="Tebrikler! Temel navigasyonu öğrendin!",
                ),
            ],
            completion_message="🎉 Temel komutları başarıyla tamamladın!\nArtık Linux terminalinde gezinebilirsin.",
            unlocks=["files", "explore"],
        )
        
        # Mission 2: File Operations
        self._missions["files"] = Mission(
            id="files",
            name="Dosya İşlemleri",
            description="Dosya ve klasör oluşturma, silme işlemlerini öğren",
            difficulty=Difficulty.EASY,
            estimated_time="7 dakika",
            prerequisites=["basics"],
            tasks=[
                Task(
                    id="mkdir",
                    description="'projeler' adında bir klasör oluştur",
                    hint="'mkdir projeler' komutunu kullan",
                    accepted_commands=["mkdir projeler"],
                    check_exists="projeler",
                    success_message="mkdir = Make Directory (Dizin Oluştur)",
                ),
                Task(
                    id="cd_projeler",
                    description="projeler klasörüne gir",
                    hint="'cd projeler' kullan",
                    accepted_commands=["cd projeler"],
                    check_cwd="~/projeler",
                    success_message="Şimdi projeler klasörünün içindesin.",
                ),
                Task(
                    id="touch",
                    description="'README.md' dosyası oluştur",
                    hint="'touch README.md' kullan",
                    accepted_commands=["touch README.md"],
                    check_exists="README.md",
                    success_message="touch komutu boş dosya oluşturur veya zaman damgası günceller.",
                ),
                Task(
                    id="touch_multi",
                    description="'app.py' ve 'config.json' dosyalarını oluştur",
                    hint="'touch app.py config.json' ile ikisini birden oluştur",
                    accepted_commands=["touch app.py config.json", "touch config.json app.py"],
                    check_exists="app.py",
                    success_message="Birden fazla dosya tek komutla oluşturulabilir!",
                ),
                Task(
                    id="rm_file",
                    description="config.json dosyasını sil",
                    hint="'rm config.json' kullan",
                    accepted_commands=["rm config.json"],
                    check_not_exists="config.json",
                    success_message="rm = Remove (Sil). Dikkatli kullan!",
                ),
                Task(
                    id="cd_back",
                    description="Ana dizine dön",
                    hint="'cd ~' kullan",
                    accepted_commands=["cd ~", "cd", "cd .."],
                    check_cwd="~",
                    success_message="Dosya işlemlerini öğrendin!",
                ),
            ],
            completion_message="🎉 Dosya işlemlerini başarıyla tamamladın!\nArtık dosya ve klasör yönetebilirsin.",
            unlocks=["text", "danger"],
        )
        
        # Mission 3: System Exploration
        self._missions["explore"] = Mission(
            id="explore",
            name="Sistem Gezisi",
            description="Linux dosya sistemi yapısını keşfet",
            difficulty=Difficulty.MEDIUM,
            estimated_time="10 dakika",
            prerequisites=["basics"],
            tasks=[
                Task(
                    id="goto_root",
                    description="Kök dizine (/) git",
                    hint="'cd /' kullan",
                    accepted_commands=["cd /"],
                    check_cwd="/",
                    success_message="/ (root) tüm dosya sisteminin başlangıcıdır.",
                ),
                Task(
                    id="ls_root",
                    description="Kök dizinin içeriğini listele",
                    hint="'ls' veya 'ls -la' kullan",
                    accepted_commands=["ls", "ls -la", "ls -l", "ls -a"],
                    success_message="Linux'ta her şey kök dizinin altındadır.",
                ),
                Task(
                    id="goto_etc",
                    description="/etc dizinine git",
                    hint="'cd /etc' veya 'cd etc' kullan",
                    accepted_commands=["cd /etc", "cd etc"],
                    check_cwd="/etc",
                    success_message="/etc sistem yapılandırma dosyalarını içerir.",
                ),
                Task(
                    id="cat_passwd",
                    description="passwd dosyasını oku",
                    hint="'cat passwd' kullan",
                    accepted_commands=["cat passwd", "cat /etc/passwd"],
                    success_message="/etc/passwd kullanıcı hesap bilgilerini içerir.",
                ),
                Task(
                    id="cat_hosts",
                    description="hosts dosyasını oku",
                    hint="'cat hosts' kullan",
                    accepted_commands=["cat hosts", "cat /etc/hosts"],
                    success_message="/etc/hosts yerel DNS çözümlemeleri içerir.",
                ),
                Task(
                    id="goto_var",
                    description="/var/log dizinine git",
                    hint="'cd /var/log' kullan",
                    accepted_commands=["cd /var/log"],
                    check_cwd="/var/log",
                    success_message="/var/log sistem günlüklerini içerir.",
                ),
                Task(
                    id="cat_syslog",
                    description="syslog dosyasını oku",
                    hint="'cat syslog' kullan",
                    accepted_commands=["cat syslog", "cat /var/log/syslog"],
                    success_message="Sistem günlükleri sorun çözmede çok işe yarar!",
                ),
                Task(
                    id="go_home",
                    description="Ev dizinine dön",
                    hint="'cd ~' kullan",
                    accepted_commands=["cd ~", "cd", "cd $HOME"],
                    check_cwd="~",
                    success_message="Sistem yapısını keşfettin!",
                ),
            ],
            completion_message="🎉 Linux dosya sistemi yapısını keşfettin!\n/etc, /var, /home gibi önemli dizinleri öğrendin.",
            unlocks=["text"],
        )
        
        # Mission 4: Text Processing
        self._missions["text"] = Mission(
            id="text",
            name="Metin İşleme",
            description="Dosya içeriğini okuma ve metin işleme komutları",
            difficulty=Difficulty.MEDIUM,
            estimated_time="10 dakika",
            prerequisites=["files"],
            tasks=[
                Task(
                    id="echo_basic",
                    description="Ekrana 'Merhaba Linux!' yazdır",
                    hint="'echo Merhaba Linux!' kullan",
                    accepted_commands=["echo Merhaba Linux!", "echo 'Merhaba Linux!'", 'echo "Merhaba Linux!"'],
                    success_message="echo komutu metni ekrana yazdırır.",
                ),
                Task(
                    id="echo_redirect",
                    description="'Merhaba' metnini hello.txt dosyasına yaz",
                    hint="'echo Merhaba > hello.txt' kullan",
                    accepted_commands=["echo Merhaba > hello.txt", "echo 'Merhaba' > hello.txt"],
                    check_exists="hello.txt",
                    success_message="> operatörü çıktıyı dosyaya yönlendirir.",
                ),
                Task(
                    id="cat_hello",
                    description="hello.txt dosyasını oku",
                    hint="'cat hello.txt' kullan",
                    accepted_commands=["cat hello.txt"],
                    success_message="cat = concatenate (birleştir/göster)",
                ),
                Task(
                    id="echo_append",
                    description="'Dünya' metnini hello.txt'e ekle",
                    hint="'echo Dünya >> hello.txt' kullan (>> = ekle)",
                    accepted_commands=["echo Dünya >> hello.txt", "echo 'Dünya' >> hello.txt"],
                    success_message=">> operatörü dosyanın sonuna ekler.",
                ),
                Task(
                    id="wc_hello",
                    description="hello.txt'in satır sayısını göster",
                    hint="'wc -l hello.txt' kullan",
                    accepted_commands=["wc -l hello.txt", "wc hello.txt"],
                    success_message="wc = word count (kelime/satır sayacı)",
                ),
                Task(
                    id="head_bashrc",
                    description=".bashrc dosyasının ilk 5 satırını göster",
                    hint="'head -n 5 .bashrc' kullan",
                    accepted_commands=["head -n 5 .bashrc", "head -5 .bashrc", "head -n5 .bashrc"],
                    success_message="head dosyanın başını gösterir.",
                ),
            ],
            completion_message="🎉 Metin işleme komutlarını öğrendin!\necho, cat, head, tail, wc artık senin araçların.",
            unlocks=["danger"],
        )
        
        # Mission 5: Danger Zone
        self._missions["danger"] = Mission(
            id="danger",
            name="Tehlike Bölgesi",
            description="⚠️ Tehlikeli komutları güvenle dene",
            difficulty=Difficulty.HARD,
            estimated_time="5 dakika",
            prerequisites=["files"],
            tasks=[
                Task(
                    id="create_test_dir",
                    description="'test_zone' klasörü oluştur",
                    hint="'mkdir test_zone' kullan",
                    accepted_commands=["mkdir test_zone"],
                    check_exists="test_zone",
                    success_message="Deney alanımız hazır!",
                ),
                Task(
                    id="cd_test",
                    description="test_zone klasörüne gir",
                    hint="'cd test_zone' kullan",
                    accepted_commands=["cd test_zone"],
                    check_cwd="~/test_zone",
                    success_message="Şimdi güvenli alandayız.",
                ),
                Task(
                    id="create_files",
                    description="file1.txt, file2.txt, file3.txt oluştur",
                    hint="'touch file1.txt file2.txt file3.txt' kullan",
                    accepted_commands=["touch file1.txt file2.txt file3.txt"],
                    success_message="Test dosyaları hazır.",
                ),
                Task(
                    id="rm_recursive",
                    description="cd .. ile çık ve test_zone'u tamamen sil",
                    hint="Önce 'cd ..' sonra 'rm -rf test_zone' kullan",
                    accepted_commands=["rm -rf test_zone", "rm -r test_zone"],
                    check_not_exists="test_zone",
                    success_message="rm -rf dizini ve içindekileri tamamen siler!",
                    points=20,
                ),
                Task(
                    id="dangerous_rm",
                    description="⚠️ ŞİMDİ TEHLİKELİ KOMUT: 'rm -rf /' çalıştır",
                    hint="Sadece 'rm -rf /' yaz ve enter'a bas. (Simülasyon güvenli!)",
                    accepted_commands=["rm -rf /", "rm -rf /*"],
                    success_message="😱 Gerçek sistemde ASLA yapma! Ama burada güvendesin.",
                    points=50,
                ),
            ],
            completion_message="🎉 Tehlike bölgesini atlattın!\n⚠️ Gerçek sistemde 'rm -rf /' ASLA kullanma!\nCtrl+R ile sistemi sıfırlayabilirsin.",
            unlocks=["hacker_intro"],
        )
        
        # === HACKER EĞİTİMİ SERİSİ ===
        
        # Hacker 1: Giriş - Sistem Keşfi
        self._missions["hacker_intro"] = Mission(
            id="hacker_intro",
            name="🔓 Hacker 101: Sistem Keşfi",
            description="Bir sisteme bağlandın. Bilgi topla ve keşfet!",
            difficulty=Difficulty.MEDIUM,
            category="hacker",
            estimated_time="10 dakika",
            prerequisites=["danger"],
            tasks=[
                Task(
                    id="whoami",
                    description="Hangi kullanıcı olduğunu öğren",
                    hint="'whoami' komutu mevcut kullanıcıyı gösterir",
                    accepted_commands=["whoami"],
                    success_message="✓ Kimliğini tespit ettin. İlk adım tamamlandı!",
                ),
                Task(
                    id="hostname",
                    description="Bağlı olduğun sunucunun adını öğren",
                    hint="'hostname' komutunu kullan",
                    accepted_commands=["hostname"],
                    success_message="✓ Hedef: Bu sunucu!",
                ),
                Task(
                    id="uname",
                    description="İşletim sistemi bilgilerini öğren",
                    hint="'uname -a' tüm sistem bilgisini verir",
                    accepted_commands=["uname -a", "uname --all"],
                    success_message="✓ Sistem: Linux! Şimdi neler yapabileceğimizi biliyoruz.",
                ),
                Task(
                    id="explore_etc",
                    description="/etc dizinini keşfet (sistem ayarları)",
                    hint="'ls /etc' ile sistem ayarlarını gör",
                    accepted_commands=["ls /etc", "ls -la /etc", "ls -l /etc"],
                    success_message="✓ /etc dizini kritik sistem dosyalarını içerir.",
                ),
                Task(
                    id="find_passwd",
                    description="Kullanıcı listesini bul: /etc/passwd dosyasını oku",
                    hint="'cat /etc/passwd' ile kullanıcıları gör",
                    accepted_commands=["cat /etc/passwd"],
                    success_message="✓ Tüm kullanıcılar! root, daemon, user... hepsi burada.",
                    points=15,
                ),
                Task(
                    id="check_shadow",
                    description="Şifre hash'lerini aramayı dene: /etc/shadow",
                    hint="'cat /etc/shadow' - ama erişim reddedilebilir!",
                    accepted_commands=["cat /etc/shadow"],
                    success_message="❌ Erişim engellendi! shadow dosyası root yetkisi ister.",
                    points=15,
                ),
            ],
            completion_message="🔓 BÖLÜM 1 TAMAMLANDI!\n\nÖğrendiklerin:\n• whoami, hostname, uname - Sistem bilgisi\n• /etc/passwd - Kullanıcı listesi\n• /etc/shadow - Şifreler (korumalı!)\n\nSonraki: Log Analizi!",
            unlocks=["hacker_logs"],
        )
        
        # Hacker 2: Log Analizi
        self._missions["hacker_logs"] = Mission(
            id="hacker_logs",
            name="🔍 Hacker 102: Log Analizi",
            description="Sistem loglarını analiz et, şüpheli aktiviteleri bul!",
            difficulty=Difficulty.MEDIUM,
            category="hacker",
            estimated_time="12 dakika",
            prerequisites=["hacker_intro"],
            tasks=[
                Task(
                    id="go_var_log",
                    description="Log dizinine git: /var/log",
                    hint="'cd /var/log' kullan",
                    accepted_commands=["cd /var/log"],
                    check_cwd="/var/log",
                    success_message="✓ Log merkezi! Tüm sistem olayları burada kayıtlı.",
                ),
                Task(
                    id="list_logs",
                    description="Mevcut log dosyalarını listele",
                    hint="'ls -la' ile tüm logları gör",
                    accepted_commands=["ls", "ls -la", "ls -l", "ls -a"],
                    success_message="✓ auth.log, syslog, messages... her biri önemli!",
                ),
                Task(
                    id="read_auth",
                    description="Kimlik doğrulama loglarını oku: auth.log",
                    hint="'cat auth.log' veya 'less auth.log'",
                    accepted_commands=["cat auth.log", "less auth.log", "more auth.log"],
                    success_message="✓ Giriş denemeleri burada! Failed password dikkat!",
                ),
                Task(
                    id="grep_failed",
                    description="Başarısız giriş denemelerini filtrele",
                    hint="'grep Failed auth.log' veya 'grep -i fail auth.log'",
                    accepted_commands=["grep Failed auth.log", "grep failed auth.log", "grep -i fail auth.log", "grep -i failed auth.log"],
                    success_message="✓ Brute-force saldırısı izleri! Birisi şifre deniyor.",
                    points=15,
                ),
                Task(
                    id="grep_root",
                    description="Root kullanıcı aktivitelerini ara",
                    hint="'grep root auth.log' kullan",
                    accepted_commands=["grep root auth.log", "grep -i root auth.log"],
                    success_message="✓ Root erişim denemeleri! Bu ciddi bir durum.",
                    points=15,
                ),
                Task(
                    id="tail_log",
                    description="Son 5 log kaydını göster",
                    hint="'tail -5 auth.log' veya 'tail -n 5 auth.log'",
                    accepted_commands=["tail -5 auth.log", "tail -n 5 auth.log", "tail -n5 auth.log"],
                    success_message="✓ Canlı izleme için 'tail -f' kullanabilirsin!",
                    points=15,
                ),
            ],
            completion_message="🔍 BÖLÜM 2 TAMAMLANDI!\n\nÖğrendiklerin:\n• /var/log - Tüm loglar burada\n• grep - Metin arama ve filtreleme\n• tail - Son kayıtları görme\n\nSonraki: Dosya Avı!",
            unlocks=["hacker_hunt"],
        )
        
        # Hacker 3: Dosya Avı
        self._missions["hacker_hunt"] = Mission(
            id="hacker_hunt",
            name="🎯 Hacker 103: Dosya Avı",
            description="Gizli dosyaları bul, şüpheli içerikleri tespit et!",
            difficulty=Difficulty.HARD,
            category="hacker",
            estimated_time="15 dakika",
            prerequisites=["hacker_logs"],
            tasks=[
                Task(
                    id="go_home",
                    description="Ev dizinine dön",
                    hint="'cd ~' veya 'cd' kullan",
                    accepted_commands=["cd", "cd ~", "cd $HOME"],
                    check_cwd="~",
                    success_message="✓ Ev dizinine döndün.",
                ),
                Task(
                    id="find_hidden",
                    description="Gizli dosyaları ara (nokta ile başlayanlar)",
                    hint="'ls -la' ile gizli dosyaları gör",
                    accepted_commands=["ls -la", "ls -al", "ls -a"],
                    success_message="✓ .bashrc, .profile, .secret... Gizli dosyalar!",
                ),
                Task(
                    id="create_secret",
                    description="Bir .secret_notes dosyası oluştur",
                    hint="'touch .secret_notes' kullan",
                    accepted_commands=["touch .secret_notes"],
                    check_exists=".secret_notes",
                    success_message="✓ Gizli dosya oluşturuldu!",
                ),
                Task(
                    id="write_secret",
                    description="Gizli dosyaya 'password: admin123' yaz",
                    hint="'echo \"password: admin123\" > .secret_notes'",
                    accepted_commands=["echo 'password: admin123' > .secret_notes", 
                                      "echo \"password: admin123\" > .secret_notes",
                                      "echo password: admin123 > .secret_notes"],
                    success_message="✓ Tehlikeli! Şifreler asla düz metin saklanmamalı!",
                    points=15,
                ),
                Task(
                    id="read_secret",
                    description="Gizli dosyayı oku",
                    hint="'cat .secret_notes' kullan",
                    accepted_commands=["cat .secret_notes"],
                    success_message="✓ İşte şifre! Gerçek hayatta bu büyük güvenlik açığı.",
                ),
                Task(
                    id="find_command",
                    description="find komutuyla .txt dosyalarını ara",
                    hint="'find . -name \"*.txt\"' kullan",
                    accepted_commands=["find . -name \"*.txt\"", "find . -name '*.txt'", 
                                      "find . -name *.txt"],
                    success_message="✓ find komutu çok güçlü bir arama aracı!",
                    points=20,
                ),
            ],
            completion_message="🎯 BÖLÜM 3 TAMAMLANDI!\n\nÖğrendiklerin:\n• Gizli dosyalar (. ile başlar)\n• echo ve yönlendirme (>)\n• find - Güçlü dosya arama\n\n🏆 HACKER EĞİTİMİ TAMAMLANDI!",
            unlocks=[],
        )
    
    def load_from_file(self, filepath: Path | str) -> Mission | None:
        """Load a mission from JSON file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._parse_mission(data)
        except Exception as e:
            print(f"Error loading mission {filepath}: {e}")
            return None
    
    def _parse_mission(self, data: dict) -> Mission:
        """Parse mission from dictionary."""
        tasks = []
        for task_data in data.get("tasks", []):
            validations = []
            for v in task_data.get("validations", []):
                validations.append(TaskValidation(
                    type=ValidationType[v["type"].upper()],
                    expected=v["expected"],
                    message=v.get("message", ""),
                ))
            
            tasks.append(Task(
                id=task_data["id"],
                description=task_data["description"],
                hint=task_data.get("hint", ""),
                validations=validations,
                points=task_data.get("points", 10),
                success_message=task_data.get("success_message", ""),
                accepted_commands=task_data.get("accepted_commands", []),
                check_cwd=task_data.get("check_cwd"),
                check_exists=task_data.get("check_exists"),
                check_not_exists=task_data.get("check_not_exists"),
            ))
        
        return Mission(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            difficulty=Difficulty.from_string(data.get("difficulty", "easy")),
            estimated_time=data.get("estimated_time", "5 dakika"),
            prerequisites=data.get("prerequisites", []),
            tasks=tasks,
            fs_create=data.get("filesystem_setup", {}).get("create", []),
            completion_message=data.get("completion", {}).get("message", ""),
            unlocks=data.get("completion", {}).get("unlock", []),
        )
    
    def get_mission(self, mission_id: str) -> Mission | None:
        """Get mission by ID."""
        return self._missions.get(mission_id)
    
    def get_all_missions(self) -> list[Mission]:
        """Get all available missions."""
        return list(self._missions.values())
    
    def get_available_missions(self, completed: list[str]) -> list[Mission]:
        """Get missions that player can start (prerequisites met)."""
        available = []
        for mission in self._missions.values():
            if mission.id in completed:
                continue
            
            # Check prerequisites
            if all(prereq in completed for prereq in mission.prerequisites):
                available.append(mission)
        
        return available


class TaskValidator:
    """Validates task completion."""
    
    def __init__(self, fs: VirtualFileSystem):
        self.fs = fs
    
    def validate(self, task: Task, command: str) -> tuple[bool, str]:
        """
        Check if a command completes the task.
        
        Validation logic:
        - If file checks exist (check_exists/check_not_exists), prioritize those
        - Otherwise check accepted_commands
        - This allows alternative commands like 'touch' or 'echo > file'
        
        Returns:
            (success, message) tuple
        """
        command = command.strip()
        
        # Determine if this task has file-based validation
        has_file_checks = task.check_exists or task.check_not_exists
        has_cwd_check = task.check_cwd
        
        # If task has file checks, validate by result not command
        if has_file_checks:
            # Check file exists
            if task.check_exists:
                if not self.fs.exists(task.check_exists):
                    return False, ""
            
            # Check file not exists
            if task.check_not_exists:
                if self.fs.exists(task.check_not_exists):
                    return False, ""
            
            # File checks passed!
            return True, task.success_message
        
        # If task has CWD check
        if has_cwd_check:
            expected_cwd = task.check_cwd.replace("~", self.fs.home)
            if self.fs.cwd != expected_cwd:
                return False, ""
            
            # CWD check passed!
            return True, task.success_message
        
        # No file/cwd checks - validate by accepted commands
        if task.accepted_commands:
            # Normalize command for comparison
            cmd_normalized = " ".join(command.split())
            
            for accepted in task.accepted_commands:
                accepted_normalized = " ".join(accepted.split())
                if cmd_normalized == accepted_normalized:
                    return True, task.success_message
                
                # Also check if command starts with accepted (for variations)
                if cmd_normalized.startswith(accepted_normalized.split()[0]):
                    # Check if it's the same base command
                    if command.split()[0] == accepted.split()[0]:
                        # For commands like 'ls -la' vs 'ls -l -a'
                        return True, task.success_message
            
            return False, ""
        
        # No validation criteria - pass
        return True, task.success_message
