"""
Linux Command Quest - SysAdmin Commands
=======================================

System administration commands: id, groups, ps, kill, service, chmod, chown, useradd, passwd, su, sudo
"""

from __future__ import annotations

import random
from datetime import datetime
from .base import BaseCommand, CommandResult, register_command


@register_command
class IdCommand(BaseCommand):
    """Display user identity."""
    
    name = "id"
    help_short = "Kullanıcı kimlik bilgilerini gösterir"
    help_long = """id - kimlik bilgisi göster

Mevcut kullanıcının UID, GID ve grup bilgilerini gösterir.

Seçenekler:
  -u, --user     Sadece UID
  -g, --group    Sadece GID
  -n, --name     Sayı yerine isim göster"""
    usage = "id [seçenekler] [kullanıcı]"
    
    def execute(self, args: list[str]) -> CommandResult:
        username = self.fs.username
        uid = 1000
        gid = 1000
        groups = f"1000({username}),4(adm),24(cdrom),27(sudo),30(dip)"
        
        show_uid = False
        show_gid = False
        show_name = False
        
        for arg in args:
            if arg in ("-u", "--user"):
                show_uid = True
            elif arg in ("-g", "--group"):
                show_gid = True
            elif arg in ("-n", "--name"):
                show_name = True
            elif not arg.startswith("-"):
                username = arg
        
        if show_uid:
            return CommandResult.ok(username if show_name else str(uid))
        if show_gid:
            return CommandResult.ok(username if show_name else str(gid))
        
        return CommandResult.ok(f"uid={uid}({username}) gid={gid}({username}) gruplar={groups}")


@register_command
class GroupsCommand(BaseCommand):
    """Display group memberships."""
    
    name = "groups"
    help_short = "Kullanıcının gruplarını gösterir"
    help_long = """groups - grup üyelikleri

Kullanıcının üye olduğu grupları listeler."""
    usage = "groups [kullanıcı]"
    
    def execute(self, args: list[str]) -> CommandResult:
        username = args[0] if args else self.fs.username
        groups = f"{username} : {username} adm cdrom sudo dip plugdev"
        return CommandResult.ok(groups)


@register_command 
class PsCommand(BaseCommand):
    """Display process status."""
    
    name = "ps"
    help_short = "Çalışan işlemleri gösterir"
    help_long = """ps - işlem durumu

Çalışan işlemlerin listesini gösterir.

Seçenekler:
  aux     Tüm işlemler (detaylı)
  -e      Tüm işlemler
  -f      Tam format"""
    usage = "ps [aux|-ef]"
    
    PROCESSES = [
        ("1", "root", "0.0", "0.1", "init", "/sbin/init"),
        ("2", "root", "0.0", "0.0", "kthreadd", "[kthreadd]"),
        ("127", "root", "0.0", "0.2", "systemd-journal", "/lib/systemd/systemd-journald"),
        ("156", "root", "0.0", "0.1", "systemd-udevd", "/lib/systemd/systemd-udevd"),
        ("298", "root", "0.0", "0.3", "NetworkManager", "/usr/sbin/NetworkManager"),
        ("312", "root", "0.0", "0.1", "sshd", "/usr/sbin/sshd -D"),
        ("456", "root", "0.0", "0.2", "cron", "/usr/sbin/cron -f"),
        ("512", "{user}", "0.1", "1.2", "bash", "-bash"),
        ("1024", "{user}", "0.2", "0.8", "python3", "python3 -m src.main"),
    ]
    
    def execute(self, args: list[str]) -> CommandResult:
        username = self.fs.username
        
        if args and ("aux" in args[0] or "-e" in args or "-f" in args):
            # Detailed view
            lines = ["USER       PID %CPU %MEM COMMAND"]
            for pid, user, cpu, mem, name, cmd in self.PROCESSES:
                user = user.replace("{user}", username)
                cmd = cmd.replace("{user}", username)
                lines.append(f"{user:10} {pid:>5} {cpu:>4} {mem:>4} {cmd}")
            return CommandResult.ok("\n".join(lines))
        else:
            # Simple view
            lines = ["  PID TTY          TIME CMD"]
            lines.append(f"  512 pts/0    00:00:00 bash")
            lines.append(f" 1024 pts/0    00:00:01 python3")
            lines.append(f" 1025 pts/0    00:00:00 ps")
            return CommandResult.ok("\n".join(lines))


@register_command
class KillCommand(BaseCommand):
    """Send signal to process."""
    
    name = "kill"
    help_short = "İşleme sinyal gönderir"
    help_long = """kill - işlem sonlandır

Bir işleme sinyal gönderir (varsayılan: TERM).

Seçenekler:
  -9, -KILL    Zorla sonlandır
  -15, -TERM   Normal sonlandır (varsayılan)
  -l           Sinyal listesi"""
    usage = "kill [-sinyal] PID"
    
    def execute(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult.fail("kill: kullanım: kill [-sinyal] PID")
        
        if args[0] == "-l":
            signals = "1) SIGHUP  2) SIGINT  3) SIGQUIT  9) SIGKILL  15) SIGTERM  19) SIGSTOP"
            return CommandResult.ok(signals)
        
        signal = "TERM"
        pid = None
        
        for arg in args:
            if arg.startswith("-"):
                sig = arg[1:]
                if sig in ("9", "KILL"):
                    signal = "KILL"
                elif sig in ("15", "TERM"):
                    signal = "TERM"
            else:
                try:
                    pid = int(arg)
                except ValueError:
                    return CommandResult.fail(f"kill: geçersiz PID: {arg}")
        
        if pid is None:
            return CommandResult.fail("kill: PID belirtilmedi")
        
        # Simüle edilmiş sonuç
        if pid == 1:
            return CommandResult.fail("kill: (1) - İşlem sonlandırılamadı: İzin reddedildi")
        elif pid < 100:
            return CommandResult.fail(f"kill: ({pid}) - Böyle bir işlem yok")
        else:
            return CommandResult.ok(f"İşlem {pid} sonlandırıldı (SIG{signal})")


@register_command
class ServiceCommand(BaseCommand):
    """Control system services."""
    
    name = "service"
    aliases = ["systemctl"]
    help_short = "Sistem servislerini yönetir"
    help_long = """service - servis yönetimi

Sistem servislerini başlatır, durdurur veya durumunu gösterir.

Kullanım:
  service <servis> start|stop|restart|status
  systemctl start|stop|restart|status <servis>"""
    usage = "service <servis> <komut>"
    min_args = 2
    
    SERVICES = {
        "ssh": ("active", "running", "OpenSSH server"),
        "sshd": ("active", "running", "OpenSSH server"),
        "nginx": ("inactive", "dead", "nginx web server"),
        "apache2": ("inactive", "dead", "Apache HTTP Server"),
        "mysql": ("inactive", "dead", "MySQL Database Server"),
        "postgresql": ("inactive", "dead", "PostgreSQL Database"),
        "cron": ("active", "running", "Regular background program processing"),
        "NetworkManager": ("active", "running", "Network Manager"),
    }
    
    def execute(self, args: list[str]) -> CommandResult:
        # Handle both "service ssh status" and "systemctl status ssh"
        if args[0] in ("start", "stop", "restart", "status"):
            action = args[0]
            service = args[1] if len(args) > 1 else None
        else:
            service = args[0]
            action = args[1] if len(args) > 1 else "status"
        
        if not service:
            return CommandResult.fail("service: servis adı belirtilmedi")
        
        if service not in self.SERVICES:
            return CommandResult.fail(f"service: {service} servisi bulunamadı")
        
        status, sub_status, desc = self.SERVICES[service]
        
        if action == "status":
            lines = [
                f"● {service}.service - {desc}",
                f"   Loaded: loaded (/lib/systemd/system/{service}.service; enabled)",
                f"   Active: {status} ({sub_status})",
                f"   Main PID: {random.randint(200, 999)} ({service})",
            ]
            return CommandResult.ok("\n".join(lines))
        elif action == "start":
            if status == "active":
                return CommandResult.ok(f"{service} zaten çalışıyor.")
            return CommandResult.ok(f"{service} başlatıldı.")
        elif action == "stop":
            if status == "inactive":
                return CommandResult.ok(f"{service} zaten durmuş.")
            return CommandResult.ok(f"{service} durduruldu.")
        elif action == "restart":
            return CommandResult.ok(f"{service} yeniden başlatıldı.")
        else:
            return CommandResult.fail(f"service: bilinmeyen komut: {action}")


@register_command
class ChmodCommand(BaseCommand):
    """Change file permissions."""
    
    name = "chmod"
    help_short = "Dosya izinlerini değiştirir"
    help_long = """chmod - izin değiştir

Dosya veya dizin izinlerini değiştirir.

Kullanım:
  chmod 755 dosya       Sayısal mod
  chmod +x dosya        Çalıştırılabilir yap
  chmod u+w dosya       Kullanıcıya yazma izni

İzin bitleri: r=4, w=2, x=1"""
    usage = "chmod <mod> <dosya>"
    min_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        mode = args[0]
        files = args[1:]
        
        for filepath in files:
            try:
                node = self.fs._get_node(self.fs.resolve(filepath))
                if node is None:
                    return CommandResult.fail(f"chmod: '{filepath}' erişilemiyor: Böyle bir dosya ya da dizin yok")
                
                # Simüle et - gerçekte izinleri değiştirmiyoruz
                return CommandResult.ok(f"'{filepath}' izinleri '{mode}' olarak değiştirildi")
            except:
                return CommandResult.fail(f"chmod: '{filepath}' erişilemiyor: Böyle bir dosya ya da dizin yok")
        
        return CommandResult.ok()


@register_command
class ChownCommand(BaseCommand):
    """Change file owner."""
    
    name = "chown"
    help_short = "Dosya sahibini değiştirir"
    help_long = """chown - sahip değiştir

Dosya veya dizin sahibini değiştirir.

Kullanım:
  chown kullanıcı dosya
  chown kullanıcı:grup dosya
  chown -R kullanıcı dizin    Recursive"""
    usage = "chown <kullanıcı[:grup]> <dosya>"
    min_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        recursive = "-R" in args
        args = [a for a in args if a != "-R"]
        
        if len(args) < 2:
            return CommandResult.fail("chown: eksik işlenen")
        
        owner = args[0]
        filepath = args[1]
        
        try:
            node = self.fs._get_node(self.fs.resolve(filepath))
            if node is None:
                return CommandResult.fail(f"chown: '{filepath}' erişilemiyor: Böyle bir dosya ya da dizin yok")
            
            return CommandResult.ok(f"'{filepath}' sahibi '{owner}' olarak değiştirildi")
        except:
            return CommandResult.fail(f"chown: '{filepath}' erişilemiyor: Böyle bir dosya ya da dizin yok")


@register_command
class UseraddCommand(BaseCommand):
    """Add a new user."""
    
    name = "useradd"
    aliases = ["adduser"]
    help_short = "Yeni kullanıcı ekler"
    help_long = """useradd - kullanıcı ekle

Sisteme yeni kullanıcı ekler.

Seçenekler:
  -m, --create-home    Ev dizini oluştur
  -s, --shell SHELL    Kabuk belirt
  -G, --groups GRUPLAR Gruplara ekle"""
    usage = "useradd [seçenekler] <kullanıcı>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        create_home = False
        shell = "/bin/bash"
        groups = []
        username = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-m", "--create-home"):
                create_home = True
            elif arg in ("-s", "--shell"):
                i += 1
                shell = args[i] if i < len(args) else "/bin/bash"
            elif arg in ("-G", "--groups"):
                i += 1
                groups = args[i].split(",") if i < len(args) else []
            elif not arg.startswith("-"):
                username = arg
            i += 1
        
        if not username:
            return CommandResult.fail("useradd: kullanıcı adı belirtilmedi")
        
        # Simülasyon - sadece root yapabilir mesajı
        return CommandResult.ok(f"Kullanıcı '{username}' oluşturuldu (simülasyon)")


@register_command
class PasswdCommand(BaseCommand):
    """Change user password."""
    
    name = "passwd"
    help_short = "Kullanıcı şifresini değiştirir"
    help_long = """passwd - şifre değiştir

Kullanıcı şifresini değiştirir.

Kullanım:
  passwd           Kendi şifreni değiştir
  passwd kullanıcı Başka kullanıcının şifresi (root)"""
    usage = "passwd [kullanıcı]"
    
    def execute(self, args: list[str]) -> CommandResult:
        username = args[0] if args else self.fs.username
        
        lines = [
            f"{username} için şifre değiştiriliyor.",
            "Mevcut şifre: ",
            "Yeni şifre: ",
            "Yeni şifreyi tekrar girin: ",
            f"passwd: şifre başarıyla güncellendi (simülasyon)"
        ]
        return CommandResult.ok("\n".join(lines))


@register_command
class SuCommand(BaseCommand):
    """Switch user."""
    
    name = "su"
    help_short = "Kullanıcı değiştirir"
    help_long = """su - kullanıcı değiştir

Başka bir kullanıcıya geçiş yapar.

Kullanım:
  su              root'a geç
  su kullanıcı    belirtilen kullanıcıya geç
  su -            root'a geç (yeni ortam)"""
    usage = "su [-] [kullanıcı]"
    
    def execute(self, args: list[str]) -> CommandResult:
        target = "root"
        new_env = False
        
        for arg in args:
            if arg == "-":
                new_env = True
            elif not arg.startswith("-"):
                target = arg
        
        return CommandResult.ok(f"Kullanıcı '{target}' olarak geçildi (simülasyon)")


@register_command
class SudoCommand(BaseCommand):
    """Execute command as superuser."""
    
    name = "sudo"
    help_short = "Komutu root olarak çalıştırır"
    help_long = """sudo - süper kullanıcı olarak çalıştır

Komutu root yetkileriyle çalıştırır.

Kullanım:
  sudo komut      Komutu root olarak çalıştır
  sudo -i         root kabuğuna geç
  sudo -l         İzinleri listele"""
    usage = "sudo <komut>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        if args[0] == "-l":
            lines = [
                f"Kullanıcı {self.fs.username} bu makinede aşağıdaki komutları çalıştırabilir:",
                "    (ALL : ALL) ALL"
            ]
            return CommandResult.ok("\n".join(lines))
        
        if args[0] == "-i":
            return CommandResult.ok("root@quest:~# (simülasyon)")
        
        # Komutu "root olarak" çalıştır
        cmd = " ".join(args)
        return CommandResult.ok(f"[sudo] {self.fs.username} için şifre: ****\n{cmd} çalıştırıldı (root olarak)")


@register_command
class DfCommand(BaseCommand):
    """Display disk space usage."""
    
    name = "df"
    help_short = "Disk kullanımını gösterir"
    help_long = """df - disk alanı

Dosya sistemlerinin disk alanı kullanımını gösterir.

Seçenekler:
  -h, --human-readable    Okunabilir boyutlar (1K, 1M, 1G)"""
    usage = "df [-h]"
    
    def execute(self, args: list[str]) -> CommandResult:
        human = "-h" in args or "--human-readable" in args
        
        if human:
            lines = [
                "Dosya sistemi      Boyut  Kull.  Boş   Kull% Bağ. Nokt.",
                "/dev/sda1          50G    12G   35G    26%  /",
                "/dev/sda2         200G    80G  110G    42%  /home",
                "tmpfs              4.0G   1.2G  2.8G    30%  /tmp",
            ]
        else:
            lines = [
                "Dosya sistemi     1K-bloklar    Kull.     Boş   Kull% Bağ. Nokt.",
                "/dev/sda1          52428800  12582912  36700160   26% /",
                "/dev/sda2         209715200  83886080 115343360   42% /home",
                "tmpfs               4194304   1258291   2936013   30% /tmp",
            ]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class DuCommand(BaseCommand):
    """Display directory space usage."""
    
    name = "du"
    help_short = "Dizin boyutunu gösterir"
    help_long = """du - dizin boyutu

Dizin ve dosyaların disk kullanımını gösterir.

Seçenekler:
  -h, --human-readable    Okunabilir boyutlar
  -s, --summarize         Sadece toplam"""
    usage = "du [-hs] [dizin]"
    
    def execute(self, args: list[str]) -> CommandResult:
        human = "-h" in args or "--human-readable" in args
        summary = "-s" in args or "--summarize" in args
        
        path = "."
        for arg in args:
            if not arg.startswith("-"):
                path = arg
                break
        
        if summary:
            size = "4.2M" if human else "4300"
            return CommandResult.ok(f"{size}\t{path}")
        
        if human:
            lines = [
                f"12K\t{path}/Documents",
                f"8.0K\t{path}/Downloads",
                f"4.0K\t{path}/Music",
                f"4.2M\t{path}",
            ]
        else:
            lines = [
                f"12\t{path}/Documents",
                f"8\t{path}/Downloads", 
                f"4\t{path}/Music",
                f"4300\t{path}",
            ]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class FreeCommand(BaseCommand):
    """Display memory usage."""
    
    name = "free"
    help_short = "Bellek kullanımını gösterir"
    help_long = """free - bellek durumu

Sistem bellek kullanımını gösterir.

Seçenekler:
  -h, --human    Okunabilir boyutlar
  -m             Megabyte cinsinden
  -g             Gigabyte cinsinden"""
    usage = "free [-h|-m|-g]"
    
    def execute(self, args: list[str]) -> CommandResult:
        human = "-h" in args or "--human" in args
        
        if human:
            lines = [
                "              toplam    kull.     boş   paylaş.  tampon    kullan.",
                "Bellek:         16Gi    8.2Gi    4.1Gi     512Mi    3.2Gi    7.0Gi",
                "Takas:          4.0Gi   512Mi    3.5Gi",
            ]
        else:
            lines = [
                "              toplam       kull.        boş   paylaş.    tampon   kullan.",
                "Bellek:     16777216     8601804     4301332     524288    3349792   7340032",
                "Takas:       4194304      524288     3670016",
            ]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class TopCommand(BaseCommand):
    """Display system processes."""
    
    name = "top"
    aliases = ["htop"]
    help_short = "Sistem işlemlerini gösterir"
    help_long = """top - işlem izleme

Çalışan işlemleri ve sistem kaynak kullanımını gerçek zamanlı gösterir.

Not: Bu simülasyonda anlık görüntü gösterilir."""
    usage = "top"
    
    def execute(self, args: list[str]) -> CommandResult:
        username = self.fs.username
        lines = [
            f"top - {datetime.now().strftime('%H:%M:%S')} up 5 days, 2:30, 1 user, load average: 0.15, 0.10, 0.05",
            "Tasks: 128 total,   1 running, 127 sleeping,   0 stopped,   0 zombie",
            "%Cpu(s):  2.5 us,  0.8 sy,  0.0 ni, 96.2 id,  0.3 wa,  0.0 hi,  0.2 si",
            "MiB Mem:  16384.0 total,   4301.3 free,   8601.8 used,   3481.0 buff/cache",
            "MiB Swap:  4096.0 total,   3670.0 free,    426.0 used.   7340.0 avail Mem",
            "",
            "  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND",
            f" 1024 {username:8}  20   0  128456  24680  18920 S   0.3   0.2   0:01.23 python3",
            "    1 root      20   0  168936  13456   8384 S   0.0   0.1   0:02.45 systemd",
            "  312 root      20   0   72304   6328   5612 S   0.0   0.0   0:00.34 sshd",
        ]
        return CommandResult.ok("\n".join(lines))


@register_command
class UptimeCommand(BaseCommand):
    """Display system uptime."""
    
    name = "uptime"
    help_short = "Sistem çalışma süresini gösterir"
    help_long = """uptime - çalışma süresi

Sistemin ne kadar süredir çalıştığını gösterir."""
    usage = "uptime"
    
    def execute(self, args: list[str]) -> CommandResult:
        now = datetime.now().strftime("%H:%M:%S")
        result = f" {now} up 5 days,  2:30,  1 user,  load average: 0.15, 0.10, 0.05"
        return CommandResult.ok(result)
