"""
Linux Command Quest - Text Commands
====================================

Commands for text processing: cat, echo, head, tail, grep, wc
"""

from __future__ import annotations

import re
from .base import BaseCommand, CommandResult, register_command
from ..filesystem import PathNotFoundError, IsADirectoryError


@register_command
class CatCommand(BaseCommand):
    """Concatenate and display files."""
    
    name = "cat"
    help_short = "Dosya içeriğini görüntüler"
    help_long = """cat - dosya içeriğini göster

Dosya içeriğini ekrana yazdırır. Birden fazla dosya verilirse
hepsini sırayla gösterir.

Seçenekler:
  -n, --number    Satır numaralarını göster"""
    usage = "cat [-n] <dosya> [dosya2] ..."
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        show_numbers = False
        files = []
        
        for arg in args:
            if arg in ("-n", "--number"):
                show_numbers = True
            elif arg.startswith("-"):
                return CommandResult.fail(f"cat: geçersiz seçenek -- '{arg[1:]}'")
            else:
                files.append(arg)
        
        if not files:
            return CommandResult.fail("cat: eksik dosya işleneni")
        
        output_lines = []
        line_num = 1
        
        for filepath in files:
            # Special case: /etc/shadow - permission denied
            resolved = self.fs.resolve(filepath)
            if resolved == "/etc/shadow":
                return CommandResult.fail("cat: /etc/shadow: İzin reddedildi")
            
            try:
                content = self.fs.cat(filepath)
                lines = content.split("\n")
                
                # Remove trailing empty line if content ends with newline
                if lines and lines[-1] == "":
                    lines = lines[:-1]
                
                for line in lines:
                    if show_numbers:
                        output_lines.append(f"  {line_num:4d}  {line}")
                        line_num += 1
                    else:
                        output_lines.append(line)
                        
            except PathNotFoundError:
                return CommandResult.fail(f"cat: {filepath}: Böyle bir dosya ya da dizin yok")
            except IsADirectoryError:
                return CommandResult.fail(f"cat: {filepath}: Bir dizin")
            except Exception as e:
                return CommandResult.fail(f"cat: {filepath}: {e}")
        
        return CommandResult.ok("\n".join(output_lines))


@register_command
class EchoCommand(BaseCommand):
    """Display text."""
    
    name = "echo"
    help_short = "Metni ekrana yazdırır"
    help_long = """echo - metin yazdır

Verilen metni ekrana yazdırır.

Seçenekler:
  -n    Sonuna yeni satır ekleme
  -e    Escape karakterlerini yorumla (\\n, \\t, vb.)

Örnekler:
  echo Merhaba Dünya
  echo -e "Satır 1\\nSatır 2"
  echo $HOME"""
    usage = "echo [-n] [-e] [metin ...]"
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        no_newline = False
        interpret_escapes = False
        text_parts = []
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-n" and not text_parts:
                no_newline = True
            elif arg == "-e" and not text_parts:
                interpret_escapes = True
            elif arg == "-ne" or arg == "-en":
                no_newline = True
                interpret_escapes = True
            else:
                text_parts.append(arg)
            i += 1
        
        text = " ".join(text_parts)
        
        # Simple variable expansion
        text = text.replace("$HOME", self.fs.home)
        text = text.replace("$USER", self.fs.username)
        text = text.replace("$PWD", self.fs.cwd)
        text = text.replace("$HOSTNAME", self.fs.hostname)
        
        # Remove surrounding quotes if present
        if len(text) >= 2:
            if (text.startswith('"') and text.endswith('"')) or \
               (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
        
        # Interpret escape sequences
        if interpret_escapes:
            text = text.replace("\\n", "\n")
            text = text.replace("\\t", "\t")
            text = text.replace("\\r", "\r")
            text = text.replace("\\\\", "\\")
        
        return CommandResult.ok(text)


@register_command
class HeadCommand(BaseCommand):
    """Display first lines of file."""
    
    name = "head"
    help_short = "Dosyanın ilk satırlarını gösterir"
    help_long = """head - dosyanın başını göster

Dosyanın ilk N satırını gösterir (varsayılan: 10).

Seçenekler:
  -n SAYI    Gösterilecek satır sayısı"""
    usage = "head [-n sayı] <dosya>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        num_lines = 10
        filepath = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n":
                if i + 1 >= len(args):
                    return CommandResult.fail("head: '-n' seçeneği bir argüman gerektiriyor")
                try:
                    num_lines = int(args[i + 1])
                except ValueError:
                    return CommandResult.fail(f"head: geçersiz satır sayısı: '{args[i + 1]}'")
                i += 2
            elif args[i].startswith("-n"):
                try:
                    num_lines = int(args[i][2:])
                except ValueError:
                    return CommandResult.fail(f"head: geçersiz satır sayısı")
                i += 1
            elif args[i].startswith("-"):
                # Try numeric flag like -5
                try:
                    num_lines = int(args[i][1:])
                except ValueError:
                    return CommandResult.fail(f"head: geçersiz seçenek -- '{args[i][1:]}'")
                i += 1
            else:
                filepath = args[i]
                i += 1
        
        if not filepath:
            return CommandResult.fail("head: eksik dosya işleneni")
        
        try:
            content = self.fs.cat(filepath)
            lines = content.split("\n")
            
            # Handle trailing newline
            if lines and lines[-1] == "":
                lines = lines[:-1]
            
            result_lines = lines[:num_lines]
            return CommandResult.ok("\n".join(result_lines))
            
        except PathNotFoundError:
            return CommandResult.fail(f"head: '{filepath}' okunamıyor: Böyle bir dosya ya da dizin yok")
        except IsADirectoryError:
            return CommandResult.fail(f"head: hata '{filepath}' okurken: Bir dizin")


@register_command
class TailCommand(BaseCommand):
    """Display last lines of file."""
    
    name = "tail"
    help_short = "Dosyanın son satırlarını gösterir"
    help_long = """tail - dosyanın sonunu göster

Dosyanın son N satırını gösterir (varsayılan: 10).

Seçenekler:
  -n SAYI    Gösterilecek satır sayısı"""
    usage = "tail [-n sayı] <dosya>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        num_lines = 10
        filepath = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n":
                if i + 1 >= len(args):
                    return CommandResult.fail("tail: '-n' seçeneği bir argüman gerektiriyor")
                try:
                    num_lines = int(args[i + 1])
                except ValueError:
                    return CommandResult.fail(f"tail: geçersiz satır sayısı: '{args[i + 1]}'")
                i += 2
            elif args[i].startswith("-n"):
                try:
                    num_lines = int(args[i][2:])
                except ValueError:
                    return CommandResult.fail(f"tail: geçersiz satır sayısı")
                i += 1
            elif args[i].startswith("-"):
                try:
                    num_lines = int(args[i][1:])
                except ValueError:
                    return CommandResult.fail(f"tail: geçersiz seçenek -- '{args[i][1:]}'")
                i += 1
            else:
                filepath = args[i]
                i += 1
        
        if not filepath:
            return CommandResult.fail("tail: eksik dosya işleneni")
        
        try:
            content = self.fs.cat(filepath)
            lines = content.split("\n")
            
            if lines and lines[-1] == "":
                lines = lines[:-1]
            
            result_lines = lines[-num_lines:] if num_lines > 0 else []
            return CommandResult.ok("\n".join(result_lines))
            
        except PathNotFoundError:
            return CommandResult.fail(f"tail: '{filepath}' okunamıyor: Böyle bir dosya ya da dizin yok")
        except IsADirectoryError:
            return CommandResult.fail(f"tail: hata '{filepath}' okurken: Bir dizin")


@register_command
class GrepCommand(BaseCommand):
    """Search for patterns in files."""
    
    name = "grep"
    help_short = "Dosyalarda desen arar"
    help_long = """grep - desen ara

Dosyalarda belirtilen deseni arar ve eşleşen satırları gösterir.

Seçenekler:
  -i, --ignore-case    Büyük/küçük harf duyarsız
  -n, --line-number    Satır numaralarını göster
  -v, --invert-match   Eşleşmeyen satırları göster
  -c, --count          Sadece eşleşme sayısını göster

Örnekler:
  grep "root" /etc/passwd
  grep -i "ERROR" log.txt
  grep -n "def " code.py"""
    usage = "grep [-inv] <desen> <dosya>"
    min_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        ignore_case = False
        show_line_numbers = False
        invert_match = False
        count_only = False
        pattern = None
        filepath = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-i", "--ignore-case"):
                ignore_case = True
            elif arg in ("-n", "--line-number"):
                show_line_numbers = True
            elif arg in ("-v", "--invert-match"):
                invert_match = True
            elif arg in ("-c", "--count"):
                count_only = True
            elif arg.startswith("-") and len(arg) > 1 and not arg.startswith("--"):
                # Combined flags like -in
                for flag in arg[1:]:
                    if flag == "i":
                        ignore_case = True
                    elif flag == "n":
                        show_line_numbers = True
                    elif flag == "v":
                        invert_match = True
                    elif flag == "c":
                        count_only = True
                    else:
                        return CommandResult.fail(f"grep: geçersiz seçenek -- '{flag}'")
            elif pattern is None:
                pattern = arg
            else:
                filepath = arg
            i += 1
        
        if not pattern:
            return CommandResult.fail("grep: eksik desen")
        if not filepath:
            return CommandResult.fail("grep: eksik dosya işleneni")
        
        try:
            content = self.fs.cat(filepath)
            lines = content.split("\n")
            
            if lines and lines[-1] == "":
                lines = lines[:-1]
            
            # Compile pattern
            flags = re.IGNORECASE if ignore_case else 0
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return CommandResult.fail(f"grep: geçersiz düzenli ifade: {e}")
            
            matches = []
            for line_num, line in enumerate(lines, 1):
                match = regex.search(line)
                
                if (match and not invert_match) or (not match and invert_match):
                    if count_only:
                        matches.append(line)
                    elif show_line_numbers:
                        # Highlight match
                        if match and not invert_match:
                            highlighted = regex.sub(f"\033[31m{match.group()}\033[0m", line)
                            matches.append(f"\033[32m{line_num}\033[0m:{highlighted}")
                        else:
                            matches.append(f"\033[32m{line_num}\033[0m:{line}")
                    else:
                        if match and not invert_match:
                            highlighted = regex.sub(lambda m: f"\033[31m{m.group()}\033[0m", line)
                            matches.append(highlighted)
                        else:
                            matches.append(line)
            
            if count_only:
                return CommandResult.ok(str(len(matches)))
            
            return CommandResult.ok("\n".join(matches))
            
        except PathNotFoundError:
            return CommandResult.fail(f"grep: {filepath}: Böyle bir dosya ya da dizin yok")
        except IsADirectoryError:
            return CommandResult.fail(f"grep: {filepath}: Bir dizin")


@register_command
class WcCommand(BaseCommand):
    """Word, line, character count."""
    
    name = "wc"
    help_short = "Satır, kelime ve karakter sayar"
    help_long = """wc - sayaç

Dosyadaki satır, kelime ve karakter sayısını gösterir.

Seçenekler:
  -l    Sadece satır sayısı
  -w    Sadece kelime sayısı
  -c    Sadece karakter (byte) sayısı
  -m    Sadece karakter sayısı"""
    usage = "wc [-lwcm] <dosya>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        # Parse flags
        count_lines = False
        count_words = False
        count_chars = False
        show_all = True
        filepath = None
        
        for arg in args:
            if arg == "-l":
                count_lines = True
                show_all = False
            elif arg == "-w":
                count_words = True
                show_all = False
            elif arg in ("-c", "-m"):
                count_chars = True
                show_all = False
            elif arg.startswith("-"):
                for flag in arg[1:]:
                    if flag == "l":
                        count_lines = True
                        show_all = False
                    elif flag == "w":
                        count_words = True
                        show_all = False
                    elif flag in ("c", "m"):
                        count_chars = True
                        show_all = False
                    else:
                        return CommandResult.fail(f"wc: geçersiz seçenek -- '{flag}'")
            else:
                filepath = arg
        
        if not filepath:
            return CommandResult.fail("wc: eksik dosya işleneni")
        
        try:
            content = self.fs.cat(filepath)
            
            lines = content.count("\n")
            if content and not content.endswith("\n"):
                lines += 1
            
            words = len(content.split())
            chars = len(content)
            
            parts = []
            if show_all or count_lines:
                parts.append(f"{lines:7d}")
            if show_all or count_words:
                parts.append(f"{words:7d}")
            if show_all or count_chars:
                parts.append(f"{chars:7d}")
            
            parts.append(filepath)
            
            return CommandResult.ok(" ".join(parts))
            
        except PathNotFoundError:
            return CommandResult.fail(f"wc: {filepath}: Böyle bir dosya ya da dizin yok")
        except IsADirectoryError:
            return CommandResult.fail(f"wc: {filepath}: Bir dizin")
