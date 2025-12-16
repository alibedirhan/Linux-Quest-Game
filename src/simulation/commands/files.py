"""
Linux Command Quest - File Commands
====================================

Commands for file operations: touch, mkdir, rm, cp, mv, rmdir
"""

from __future__ import annotations

from .base import BaseCommand, CommandResult, register_command
from ..filesystem import (
    PathNotFoundError, FileExistsError, IsADirectoryError, 
    NotADirectoryError, PermissionError as FSPermissionError
)


@register_command
class TouchCommand(BaseCommand):
    """Create empty file or update timestamp."""
    
    name = "touch"
    help_short = "Boş dosya oluşturur veya zaman damgasını günceller"
    help_long = """touch - dosya oluştur veya zaman damgası güncelle

Belirtilen dosya yoksa boş bir dosya oluşturur.
Dosya varsa, erişim ve değişiklik zamanını günceller."""
    usage = "touch <dosya> [dosya2] ..."
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        errors = []
        
        for path in args:
            try:
                self.fs.touch(path)
            except PathNotFoundError:
                errors.append(f"touch: '{path}' erişilemiyor: Böyle bir dosya ya da dizin yok")
            except Exception as e:
                errors.append(f"touch: '{path}': {e}")
        
        if errors:
            return CommandResult.fail("\n".join(errors))
        
        return CommandResult.ok()


@register_command
class MkdirCommand(BaseCommand):
    """Create directory."""
    
    name = "mkdir"
    help_short = "Dizin oluşturur"
    help_long = """mkdir - dizin oluştur

Belirtilen dizini oluşturur.

Seçenekler:
  -p, --parents   Gerekli üst dizinleri de oluşturur"""
    usage = "mkdir [-p] <dizin> [dizin2] ..."
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        parents = False
        paths = []
        
        for arg in args:
            if arg in ("-p", "--parents"):
                parents = True
            elif arg.startswith("-"):
                return CommandResult.fail(f"mkdir: geçersiz seçenek -- '{arg[1:]}'")
            else:
                paths.append(arg)
        
        if not paths:
            return CommandResult.fail("mkdir: eksik işlenen")
        
        errors = []
        for path in paths:
            try:
                self.fs.mkdir(path, parents=parents)
            except FileExistsError:
                errors.append(f"mkdir: '{path}' dizini oluşturulamıyor: Dosya mevcut")
            except PathNotFoundError:
                errors.append(f"mkdir: '{path}' dizini oluşturulamıyor: Böyle bir dosya ya da dizin yok")
            except Exception as e:
                errors.append(f"mkdir: '{path}': {e}")
        
        if errors:
            return CommandResult.fail("\n".join(errors))
        
        return CommandResult.ok()


@register_command
class RmCommand(BaseCommand):
    """Remove files or directories."""
    
    name = "rm"
    help_short = "Dosya veya dizinleri siler"
    help_long = """rm - dosya veya dizin sil

Belirtilen dosya veya dizinleri siler.

Seçenekler:
  -r, -R, --recursive   Dizinleri ve içeriklerini özyinelemeli sil
  -f, --force           Uyarı vermeden sil, var olmayan dosyaları yoksay

DİKKAT: rm -rf / komutu TÜM dosya sistemini siler!
(Bu oyunda güvenle deneyebilirsiniz)"""
    usage = "rm [-rf] <dosya> [dosya2] ..."
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        recursive = False
        force = False
        paths = []
        
        for arg in args:
            if arg in ("-r", "-R", "--recursive"):
                recursive = True
            elif arg in ("-f", "--force"):
                force = True
            elif arg in ("-rf", "-fr", "-Rf", "-fR"):
                recursive = True
                force = True
            elif arg.startswith("-"):
                # Check combined flags like -rf
                flags = arg[1:]
                for f in flags:
                    if f in "rR":
                        recursive = True
                    elif f == "f":
                        force = True
                    else:
                        return CommandResult.fail(f"rm: geçersiz seçenek -- '{f}'")
            else:
                paths.append(arg)
        
        if not paths:
            return CommandResult.fail("rm: eksik işlenen")
        
        # Special warning for rm -rf /
        if "/" in paths and recursive:
            output_lines = [
                "\033[31m╔════════════════════════════════════════════════════════════╗\033[0m",
                "\033[31m║  ⚠️  TEHLİKE! TÜM DOSYA SİSTEMİ SİLİNİYOR!                 ║\033[0m",
                "\033[31m╠════════════════════════════════════════════════════════════╣\033[0m",
                "\033[31m║  rm -rf / komutu çalıştırıldı...                          ║\033[0m",
                "\033[31m║                                                            ║\033[0m",
                "\033[31m║  /bin      [SİLİNDİ]                                       ║\033[0m",
                "\033[31m║  /etc      [SİLİNDİ]                                       ║\033[0m",
                "\033[31m║  /home     [SİLİNDİ]                                       ║\033[0m",
                "\033[31m║  /usr      [SİLİNDİ]                                       ║\033[0m",
                "\033[31m║  /var      [SİLİNDİ]                                       ║\033[0m",
                "\033[31m║  ...                                                       ║\033[0m",
                "\033[31m║                                                            ║\033[0m",
                "\033[31m║  Sistem kullanılamaz hale geldi!                           ║\033[0m",
                "\033[31m║                                                            ║\033[0m",
                "\033[32m║  ✓ Neyse ki bu bir simülasyon :)                           ║\033[0m",
                "\033[32m║    Ctrl+R ile sıfırlayabilirsiniz.                         ║\033[0m",
                "\033[31m╚════════════════════════════════════════════════════════════╝\033[0m",
            ]
        
        errors = []
        for path in paths:
            try:
                self.fs.rm(path, recursive=recursive, force=force)
            except IsADirectoryError:
                errors.append(f"rm: '{path}' silinemedi: Bir dizin")
            except PathNotFoundError:
                if not force:
                    errors.append(f"rm: '{path}' kaldırılamıyor: Böyle bir dosya ya da dizin yok")
            except FSPermissionError:
                errors.append(f"rm: '{path}' kaldırılamıyor: İzin reddedildi")
            except Exception as e:
                errors.append(f"rm: '{path}': {e}")
        
        # Check if root was deleted
        if "/" in paths and recursive:
            return CommandResult.ok("\n".join(output_lines))
        
        if errors:
            return CommandResult.fail("\n".join(errors))
        
        return CommandResult.ok()


@register_command  
class RmdirCommand(BaseCommand):
    """Remove empty directories."""
    
    name = "rmdir"
    help_short = "Boş dizinleri siler"
    help_long = """rmdir - boş dizin sil

Yalnızca BOŞ dizinleri siler. Dizin içinde dosya varsa hata verir.
İçi dolu dizinleri silmek için rm -r kullanın."""
    usage = "rmdir <dizin> [dizin2] ..."
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        errors = []
        
        for path in args:
            try:
                # Check if empty
                items = self.fs.ls(path, show_hidden=True)
                if items:
                    errors.append(f"rmdir: '{path}' silinemedi: Dizin boş değil")
                    continue
                
                self.fs.rm(path, recursive=True)
            except PathNotFoundError:
                errors.append(f"rmdir: '{path}' silinemedi: Böyle bir dosya ya da dizin yok")
            except IsADirectoryError:
                errors.append(f"rmdir: '{path}' silinemedi: Bir dizin değil")
            except Exception as e:
                errors.append(f"rmdir: '{path}': {e}")
        
        if errors:
            return CommandResult.fail("\n".join(errors))
        
        return CommandResult.ok()


@register_command
class CpCommand(BaseCommand):
    """Copy files and directories."""
    
    name = "cp"
    help_short = "Dosya ve dizinleri kopyalar"
    help_long = """cp - dosya veya dizin kopyala

Kaynak dosya/dizini hedefe kopyalar.

Seçenekler:
  -r, -R, --recursive   Dizinleri özyinelemeli kopyala"""
    usage = "cp [-r] <kaynak> <hedef>"
    min_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        recursive = False
        paths = []
        
        for arg in args:
            if arg in ("-r", "-R", "--recursive"):
                recursive = True
            elif arg.startswith("-"):
                return CommandResult.fail(f"cp: geçersiz seçenek -- '{arg[1:]}'")
            else:
                paths.append(arg)
        
        if len(paths) < 2:
            return CommandResult.fail("cp: eksik hedef dosya işleneni")
        
        src = paths[0]
        dst = paths[1]
        
        try:
            self.fs.cp(src, dst, recursive=recursive)
            return CommandResult.ok()
        except IsADirectoryError:
            return CommandResult.fail(f"cp: -r belirtilmedi; '{src}' dizini atlanıyor")
        except PathNotFoundError as e:
            return CommandResult.fail(str(e))
        except Exception as e:
            return CommandResult.fail(f"cp: {e}")


@register_command
class MvCommand(BaseCommand):
    """Move or rename files and directories."""
    
    name = "mv"
    help_short = "Dosya/dizin taşır veya yeniden adlandırır"
    help_long = """mv - taşı veya yeniden adlandır

Kaynak dosya/dizini hedefe taşır veya yeniden adlandırır.

Örnekler:
  mv dosya.txt yeni_ad.txt    # Yeniden adlandır
  mv dosya.txt klasor/        # Klasöre taşı
  mv klasor1 klasor2          # Dizini yeniden adlandır"""
    usage = "mv <kaynak> <hedef>"
    min_args = 2
    max_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        src = args[0]
        dst = args[1]
        
        try:
            self.fs.mv(src, dst)
            return CommandResult.ok()
        except PathNotFoundError as e:
            return CommandResult.fail(str(e))
        except Exception as e:
            return CommandResult.fail(f"mv: {e}")


@register_command
class FindCommand(BaseCommand):
    """Find files and directories."""
    
    name = "find"
    help_short = "Dosya ve dizin ara"
    help_long = """find - dosya ve dizin ara

Belirtilen dizinde dosya ve dizinleri arar.

Seçenekler:
  -name <pattern>    İsme göre ara (glob pattern)
  -type f            Sadece dosyalar
  -type d            Sadece dizinler

Örnekler:
  find .                      # Tüm dosyaları listele
  find . -name "*.txt"        # .txt dosyalarını bul
  find /etc -name "passwd"    # /etc'de passwd ara"""
    usage = "find [dizin] [-name pattern] [-type f|d]"
    min_args = 0
    
    def execute(self, args: list[str]) -> CommandResult:
        import fnmatch
        
        # Parse arguments
        search_dir = "."
        name_pattern = None
        type_filter = None  # 'f' for files, 'd' for directories
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-name" and i + 1 < len(args):
                name_pattern = args[i + 1].strip("'\"")
                i += 2
            elif arg == "-type" and i + 1 < len(args):
                type_filter = args[i + 1]
                i += 2
            elif not arg.startswith("-"):
                search_dir = arg
                i += 1
            else:
                i += 1
        
        # Resolve search directory
        try:
            resolved_dir = self.fs.resolve(search_dir)
        except:
            return CommandResult.fail(f"find: '{search_dir}': Böyle bir dosya ya da dizin yok")
        
        # Find all matching files
        results = []
        self._find_recursive(resolved_dir, search_dir, name_pattern, type_filter, results)
        
        if results:
            return CommandResult.ok("\n".join(sorted(results)))
        else:
            return CommandResult.ok()
    
    def _find_recursive(self, abs_path: str, display_path: str, 
                       name_pattern: str | None, type_filter: str | None,
                       results: list[str]):
        """Recursively find files."""
        import fnmatch
        
        try:
            node = self.fs._get_node(abs_path)
        except:
            return
        
        # Check current path
        name = node.name if node.name else display_path
        
        # Apply filters
        matches = True
        
        if type_filter == 'f' and node.is_dir:
            matches = False
        elif type_filter == 'd' and not node.is_dir:
            matches = False
        
        if name_pattern and matches:
            if not fnmatch.fnmatch(name, name_pattern):
                matches = False
        
        if matches:
            results.append(display_path)
        
        # Recurse into directories
        if node.is_dir:
            for child_name, child_node in node.children.items():
                if child_name.startswith('.'):
                    continue  # Skip hidden files in find by default
                child_display = f"{display_path}/{child_name}" if display_path != "." else f"./{child_name}"
                child_abs = f"{abs_path}/{child_name}"
                self._find_recursive(child_abs, child_display, name_pattern, type_filter, results)
