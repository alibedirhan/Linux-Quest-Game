"""
Linux Command Quest - Navigation Commands
==========================================

Commands for filesystem navigation: pwd, cd, ls
"""

from __future__ import annotations

from .base import BaseCommand, CommandResult, register_command


@register_command
class PwdCommand(BaseCommand):
    """Print working directory."""
    
    name = "pwd"
    help_short = "Mevcut çalışma dizinini gösterir"
    help_long = """pwd - mevcut çalışma dizinini göster

Mevcut çalışma dizininin tam yolunu yazdırır.
PWD = Print Working Directory"""
    usage = "pwd"
    max_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.ok(self.fs.cwd)
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        return []  # pwd takes no arguments


@register_command
class CdCommand(BaseCommand):
    """Change directory."""
    
    name = "cd"
    help_short = "Çalışma dizinini değiştirir"
    help_long = """cd - dizin değiştir

Mevcut çalışma dizinini belirtilen dizine değiştirir.

Özel yollar:
  ~       Ev dizini (/home/kullanıcı)
  ..      Üst dizin
  -       Önceki dizin
  /       Kök dizin"""
    usage = "cd [dizin]"
    min_args = 0
    max_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        path = args[0] if args else "~"
        
        if self.fs.cd(path):
            return CommandResult.ok()
        else:
            return CommandResult.fail(f"cd: {path}: Böyle bir dosya ya da dizin yok")
    
    def autocomplete(self, partial: str, args: list[str]) -> list[str]:
        # Only complete directories
        completions = self._complete_path(partial)
        return [c for c in completions if c.endswith("/")]


@register_command
class LsCommand(BaseCommand):
    """List directory contents."""
    
    name = "ls"
    aliases = ["dir"]
    help_short = "Dizin içeriğini listeler"
    help_long = """ls - dizin içeriğini listele

Belirtilen dizinin (varsayılan: mevcut dizin) içeriğini listeler.

Seçenekler:
  -a, --all       Gizli dosyaları da göster (. ile başlayanlar)
  -l              Uzun format (detaylı bilgi)
  -la, -al        Gizli dosyalar + uzun format

Renkler:
  Mavi   = Dizin
  Beyaz  = Normal dosya
  Yeşil  = Çalıştırılabilir dosya"""
    usage = "ls [-a] [-l] [dizin]"
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        show_hidden = False
        long_format = False
        path = ""
        
        for arg in args:
            if arg in ("-a", "--all"):
                show_hidden = True
            elif arg == "-l":
                long_format = True
            elif arg in ("-la", "-al", "-all"):
                show_hidden = True
                long_format = True
            elif arg.startswith("-"):
                return CommandResult.fail(f"ls: geçersiz seçenek -- '{arg[1:]}'")
            else:
                path = arg
        
        try:
            if long_format:
                return self._ls_long(path, show_hidden)
            else:
                return self._ls_simple(path, show_hidden)
        except Exception as e:
            return CommandResult.fail(str(e))
    
    def _ls_simple(self, path: str, show_hidden: bool) -> CommandResult:
        """Simple listing (names only)."""
        items = self.fs.ls(path, show_hidden)
        
        if not items:
            return CommandResult.ok("")
        
        # Format output
        lines = []
        for name, is_dir in items:
            if is_dir:
                lines.append(f"\033[34m{name}/\033[0m")  # Blue for directories
            else:
                lines.append(name)
        
        # Multi-column output (simplified: 2 columns)
        return CommandResult.ok("  ".join(lines))
    
    def _ls_long(self, path: str, show_hidden: bool) -> CommandResult:
        """Long format listing (like ls -l)."""
        items = self.fs.ls_detailed(path, show_hidden)
        
        if not items:
            return CommandResult.ok("toplam 0")
        
        lines = ["toplam " + str(len(items))]
        
        for item in items:
            # Build ls -l style line
            type_char = "d" if item["is_dir"] else "-"
            perms = item["permissions"]
            owner = item["owner"][:8].ljust(8)
            group = item["group"][:8].ljust(8)
            size = str(item["size"]).rjust(5)
            date = item["modified"].strftime("%b %d %H:%M")
            name = item["name"]
            
            if item["is_dir"]:
                name = f"\033[34m{name}/\033[0m"
            
            line = f"{type_char}{perms} 1 {owner} {group} {size} {date} {name}"
            lines.append(line)
        
        return CommandResult.ok("\n".join(lines))
