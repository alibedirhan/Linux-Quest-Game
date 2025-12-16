"""
Linux Command Quest - System Commands
======================================

System utility commands: clear, whoami, date, hostname, help, exit, history
"""

from __future__ import annotations

from datetime import datetime
from .base import BaseCommand, CommandResult, register_command, get_registry


@register_command
class ClearCommand(BaseCommand):
    """Clear the terminal screen."""
    
    name = "clear"
    aliases = ["cls"]
    help_short = "Ekranı temizler"
    help_long = """clear - ekranı temizle

Terminal ekranını temizler ve imleci sol üst köşeye taşır."""
    usage = "clear"
    max_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.clear()
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class WhoamiCommand(BaseCommand):
    """Print current username."""
    
    name = "whoami"
    help_short = "Mevcut kullanıcı adını gösterir"
    help_long = """whoami - kullanıcı adını göster

Mevcut oturumun kullanıcı adını yazdırır."""
    usage = "whoami"
    max_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.ok(self.fs.username)
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class HostnameCommand(BaseCommand):
    """Print system hostname."""
    
    name = "hostname"
    help_short = "Sistem ana bilgisayar adını gösterir"
    help_long = """hostname - ana bilgisayar adını göster

Sistemin ana bilgisayar adını (hostname) yazdırır."""
    usage = "hostname"
    max_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.ok(self.fs.hostname)
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class DateCommand(BaseCommand):
    """Display current date and time."""
    
    name = "date"
    help_short = "Tarih ve saati gösterir"
    help_long = """date - tarih ve saat göster

Mevcut tarih ve saati gösterir.

Seçenekler:
  +FORMAT    Özel format belirt

Format karakterleri:
  %Y    Yıl (4 haneli)
  %m    Ay (01-12)
  %d    Gün (01-31)
  %H    Saat (00-23)
  %M    Dakika (00-59)
  %S    Saniye (00-59)
  %A    Gün adı (Pazartesi, ...)
  %B    Ay adı (Ocak, ...)"""
    usage = "date [+format]"
    
    # Turkish day and month names
    DAYS_TR = {
        "Monday": "Pazartesi",
        "Tuesday": "Salı", 
        "Wednesday": "Çarşamba",
        "Thursday": "Perşembe",
        "Friday": "Cuma",
        "Saturday": "Cumartesi",
        "Sunday": "Pazar"
    }
    
    MONTHS_TR = {
        "January": "Ocak",
        "February": "Şubat",
        "March": "Mart",
        "April": "Nisan",
        "May": "Mayıs",
        "June": "Haziran",
        "July": "Temmuz",
        "August": "Ağustos",
        "September": "Eylül",
        "October": "Ekim",
        "November": "Kasım",
        "December": "Aralık"
    }
    
    def execute(self, args: list[str]) -> CommandResult:
        now = datetime.now()
        
        if args and args[0].startswith("+"):
            # Custom format
            fmt = args[0][1:]
            result = now.strftime(fmt)
        else:
            # Default format: "Pzt Ara 15 14:30:00 +03 2025"
            day_name = self.DAYS_TR.get(now.strftime("%A"), now.strftime("%a"))[:3]
            month_name = self.MONTHS_TR.get(now.strftime("%B"), now.strftime("%b"))[:3]
            result = f"{day_name} {month_name} {now.strftime('%d %H:%M:%S +03 %Y')}"
        
        return CommandResult.ok(result)
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class UnameCommand(BaseCommand):
    """Print system information."""
    
    name = "uname"
    help_short = "Sistem bilgilerini gösterir"
    help_long = """uname - sistem bilgisi göster

İşletim sistemi bilgilerini yazdırır.

Seçenekler:
  -a, --all       Tüm bilgileri göster
  -s, --kernel    Çekirdek adı
  -n, --nodename  Ağ düğüm adı (hostname)
  -r, --release   Çekirdek sürümü
  -m, --machine   Makine donanım adı
  -o, --os        İşletim sistemi"""
    usage = "uname [-a]"
    
    def execute(self, args: list[str]) -> CommandResult:
        kernel = "Linux"
        nodename = self.fs.hostname
        release = "6.1.0-quest"
        machine = "x86_64"
        os_name = "GNU/Linux"
        
        if not args:
            return CommandResult.ok(kernel)
        
        show_all = False
        parts = []
        
        for arg in args:
            if arg in ("-a", "--all"):
                show_all = True
            elif arg in ("-s", "--kernel"):
                parts.append(kernel)
            elif arg in ("-n", "--nodename"):
                parts.append(nodename)
            elif arg in ("-r", "--release"):
                parts.append(release)
            elif arg in ("-m", "--machine"):
                parts.append(machine)
            elif arg in ("-o", "--os"):
                parts.append(os_name)
            elif arg.startswith("-"):
                return CommandResult.fail(f"uname: geçersiz seçenek -- '{arg[1:]}'")
        
        if show_all:
            return CommandResult.ok(f"{kernel} {nodename} {release} {machine} {os_name}")
        
        if parts:
            return CommandResult.ok(" ".join(parts))
        
        return CommandResult.ok(kernel)
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class HelpCommand(BaseCommand):
    """Display help information."""
    
    name = "help"
    aliases = ["?"]
    help_short = "Yardım bilgisi gösterir"
    help_long = """help - yardım göster

Kullanılabilir komutları ve açıklamalarını listeler.
Belirli bir komut için: help <komut>"""
    usage = "help [komut]"
    
    def execute(self, args: list[str]) -> CommandResult:
        registry = get_registry()
        
        if args:
            # Help for specific command
            cmd_name = args[0]
            cmd_class = registry.get(cmd_name)
            
            if cmd_class:
                cmd = cmd_class(self.fs, self.shell)
                return CommandResult.ok(cmd.get_help())
            else:
                return CommandResult.fail(f"help: '{cmd_name}' komutu bulunamadı")
        
        # List all commands
        lines = [
            "\033[36m╔══════════════════════════════════════════════════════════════╗\033[0m",
            "\033[36m║\033[0m  \033[1;33mLINUX COMMAND QUEST - KOMUT LİSTESİ\033[0m                        \033[36m║\033[0m",
            "\033[36m╠══════════════════════════════════════════════════════════════╣\033[0m",
        ]
        
        help_table = registry.get_help_table()
        
        # Group commands by category
        categories = {
            "Navigasyon": ["pwd", "cd", "ls"],
            "Dosya İşlemleri": ["touch", "mkdir", "rm", "rmdir", "cp", "mv"],
            "Metin İşleme": ["cat", "echo", "head", "tail", "grep", "wc"],
            "Sistem": ["clear", "whoami", "hostname", "date", "uname", "help", "history", "exit"],
        }
        
        for category, cmds in categories.items():
            lines.append(f"\033[36m║\033[0m  \033[1;32m{category}:\033[0m")
            for cmd_name, desc in help_table:
                if cmd_name in cmds:
                    lines.append(f"\033[36m║\033[0m    \033[33m{cmd_name:12}\033[0m {desc}")
        
        lines.append("\033[36m╠══════════════════════════════════════════════════════════════╣\033[0m")
        lines.append("\033[36m║\033[0m  \033[90mDetaylı yardım için: help <komut>\033[0m                          \033[36m║\033[0m")
        lines.append("\033[36m╚══════════════════════════════════════════════════════════════╝\033[0m")
        
        return CommandResult.ok("\n".join(lines))
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        registry = get_registry()
        return [name for name in registry.all_names() if name.startswith(partial)]


@register_command
class HistoryCommand(BaseCommand):
    """Display command history."""
    
    name = "history"
    help_short = "Komut geçmişini gösterir"
    help_long = """history - komut geçmişi

Girilen komutların geçmişini listeler.
Geçmişte gezinmek için yukarı/aşağı ok tuşlarını kullanın."""
    usage = "history [sayı]"
    
    def execute(self, args: list[str]) -> CommandResult:
        history = self.shell.get_history()
        
        if not history:
            return CommandResult.ok("Geçmiş boş")
        
        # Number of items to show
        count = len(history)
        if args:
            try:
                count = int(args[0])
            except ValueError:
                return CommandResult.fail(f"history: geçersiz sayı: '{args[0]}'")
        
        lines = []
        start = max(0, len(history) - count)
        
        for i, cmd in enumerate(history[start:], start + 1):
            lines.append(f"  {i:4d}  {cmd}")
        
        return CommandResult.ok("\n".join(lines))
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class ExitCommand(BaseCommand):
    """Exit the shell."""
    
    name = "exit"
    aliases = ["quit", "logout"]
    help_short = "Kabuktan çıkar"
    help_long = """exit - çıkış

Kabuk oturumunu sonlandırır.
Ayrıca 'quit' veya 'logout' da kullanılabilir."""
    usage = "exit"
    max_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        result = CommandResult.ok("Oturum sonlandırılıyor...")
        result.exit_game = True
        return result
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []


@register_command
class TypeCommand(BaseCommand):
    """Display information about command type."""
    
    name = "type"
    help_short = "Komut türünü gösterir"
    help_long = """type - komut türü

Bir komutun türünü (yerleşik, takma ad, vb.) gösterir."""
    usage = "type <komut>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        registry = get_registry()
        lines = []
        
        for cmd_name in args:
            cmd_class = registry.get(cmd_name)
            if cmd_class:
                if cmd_name in getattr(cmd_class, 'aliases', []):
                    real_name = cmd_class.name
                    lines.append(f"{cmd_name}, {real_name} için bir takma addır")
                else:
                    lines.append(f"{cmd_name} bir kabuk yerleşik komutudur")
            else:
                lines.append(f"type: {cmd_name}: bulunamadı")
        
        return CommandResult.ok("\n".join(lines))
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        registry = get_registry()
        return [name for name in registry.all_names() if name.startswith(partial)]


@register_command
class AliasCommand(BaseCommand):
    """Display or set command aliases."""
    
    name = "alias"
    help_short = "Takma adları gösterir"
    help_long = """alias - takma adları göster

Tanımlı komut takma adlarını listeler.
Not: Bu oyunda takma ad tanımlama devre dışıdır."""
    usage = "alias"
    
    def execute(self, args: list[str]) -> CommandResult:
        # Predefined aliases
        aliases = [
            ("ll", "ls -la"),
            ("la", "ls -A"),
            ("l", "ls -CF"),
            ("..", "cd .."),
            ("...", "cd ../.."),
            ("cls", "clear"),
        ]
        
        lines = []
        for name, value in aliases:
            lines.append(f"alias {name}='{value}'")
        
        return CommandResult.ok("\n".join(lines))
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []
