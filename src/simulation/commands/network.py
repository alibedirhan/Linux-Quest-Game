"""
Linux Command Quest - Network Commands
======================================

Network commands: ping, ifconfig, ip, netstat, ss, curl, wget, host, dig, traceroute
"""

from __future__ import annotations

import random
from datetime import datetime
from .base import BaseCommand, CommandResult, register_command


@register_command
class PingCommand(BaseCommand):
    """Send ICMP echo requests."""
    
    name = "ping"
    help_short = "Ağ bağlantısını test eder"
    help_long = """ping - ağ testi

Hedefe ICMP paketleri göndererek bağlantıyı test eder.

Seçenekler:
  -c SAYI    Gönderilecek paket sayısı
  -i SÜRE    Paketler arası bekleme (saniye)"""
    usage = "ping [-c sayı] <hedef>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        count = 4
        target = None
        
        i = 0
        while i < len(args):
            if args[i] == "-c" and i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    pass
            elif not args[i].startswith("-"):
                target = args[i]
            i += 1
        
        if not target:
            return CommandResult.fail("ping: hedef belirtilmedi")
        
        # Simüle edilmiş ping
        ip = self._resolve_host(target)
        if not ip:
            return CommandResult.fail(f"ping: {target}: Ad veya servis bilinmiyor")
        
        lines = [f"PING {target} ({ip}) 56(84) bytes of data."]
        
        total_time = 0
        min_time = float('inf')
        max_time = 0
        
        for seq in range(1, count + 1):
            time = round(random.uniform(10, 50), 1)
            total_time += time
            min_time = min(min_time, time)
            max_time = max(max_time, time)
            lines.append(f"64 bytes from {ip}: icmp_seq={seq} ttl=64 time={time} ms")
        
        avg_time = round(total_time / count, 1)
        
        lines.append("")
        lines.append(f"--- {target} ping istatistikleri ---")
        lines.append(f"{count} paket gönderildi, {count} alındı, %0 paket kaybı")
        lines.append(f"rtt min/avg/max = {min_time}/{avg_time}/{max_time} ms")
        
        return CommandResult.ok("\n".join(lines))
    
    def _resolve_host(self, host: str) -> str | None:
        """Resolve hostname to IP."""
        known_hosts = {
            "localhost": "127.0.0.1",
            "google.com": "142.250.185.78",
            "github.com": "140.82.121.4",
            "8.8.8.8": "8.8.8.8",
            "1.1.1.1": "1.1.1.1",
        }
        
        if host in known_hosts:
            return known_hosts[host]
        
        # IP address
        if host.replace(".", "").isdigit():
            return host
        
        # Unknown host - generate fake IP
        return f"93.184.{random.randint(1, 254)}.{random.randint(1, 254)}"


@register_command
class IfconfigCommand(BaseCommand):
    """Display network interface configuration."""
    
    name = "ifconfig"
    help_short = "Ağ arayüzlerini gösterir"
    help_long = """ifconfig - ağ yapılandırması

Ağ arayüzlerinin yapılandırmasını gösterir.

Not: Modern sistemlerde 'ip' komutu tercih edilir."""
    usage = "ifconfig [arayüz]"
    
    def execute(self, args: list[str]) -> CommandResult:
        lines = [
            "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500",
            "        inet 192.168.1.105  netmask 255.255.255.0  broadcast 192.168.1.255",
            "        inet6 fe80::1  prefixlen 64  scopeid 0x20<link>",
            "        ether 02:42:ac:11:00:02  txqueuelen 1000  (Ethernet)",
            "        RX packets 15243  bytes 18234567 (17.3 MiB)",
            "        TX packets 12456  bytes 1234567 (1.1 MiB)",
            "",
            "lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536",
            "        inet 127.0.0.1  netmask 255.0.0.0",
            "        inet6 ::1  prefixlen 128  scopeid 0x10<host>",
            "        loop  txqueuelen 1000  (Local Loopback)",
            "        RX packets 1024  bytes 102400 (100.0 KiB)",
            "        TX packets 1024  bytes 102400 (100.0 KiB)",
        ]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class IpCommand(BaseCommand):
    """Show/manipulate network configuration."""
    
    name = "ip"
    help_short = "Ağ yapılandırmasını gösterir"
    help_long = """ip - ağ yönetimi

Modern ağ yapılandırma aracı.

Kullanım:
  ip addr       IP adreslerini göster
  ip link       Ağ arayüzlerini göster
  ip route      Yönlendirme tablosunu göster"""
    usage = "ip [addr|link|route]"
    
    def execute(self, args: list[str]) -> CommandResult:
        cmd = args[0] if args else "addr"
        
        if cmd in ("addr", "a", "address"):
            lines = [
                "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN",
                "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00",
                "    inet 127.0.0.1/8 scope host lo",
                "    inet6 ::1/128 scope host",
                "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP",
                "    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff",
                "    inet 192.168.1.105/24 brd 192.168.1.255 scope global eth0",
                "    inet6 fe80::42:acff:fe11:2/64 scope link",
            ]
        elif cmd in ("link", "l"):
            lines = [
                "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN",
                "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00",
                "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP",
                "    link/ether 02:42:ac:11:00:02 brd ff:ff:ff:ff:ff:ff",
            ]
        elif cmd in ("route", "r"):
            lines = [
                "default via 192.168.1.1 dev eth0 proto dhcp metric 100",
                "192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.105 metric 100",
            ]
        else:
            return CommandResult.fail(f"ip: '{cmd}' bilinmeyen komut")
        
        return CommandResult.ok("\n".join(lines))


@register_command
class NetstatCommand(BaseCommand):
    """Display network connections."""
    
    name = "netstat"
    help_short = "Ağ bağlantılarını gösterir"
    help_long = """netstat - ağ istatistikleri

Ağ bağlantıları, yönlendirme tablosu ve arayüz istatistiklerini gösterir.

Seçenekler:
  -t    TCP bağlantıları
  -u    UDP bağlantıları
  -l    Dinleyen soketler
  -n    Sayısal adresler
  -p    İşlem bilgisi"""
    usage = "netstat [-tulnp]"
    
    def execute(self, args: list[str]) -> CommandResult:
        flags = "".join(args) if args else ""
        
        lines = [
            "Aktif Internet bağlantıları (sunucular ve kurulmuş)",
            "Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program",
        ]
        
        if "l" in flags or not flags:
            lines.append("tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      312/sshd")
            lines.append("tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN      456/cupsd")
        
        if not "l" in flags or not flags:
            lines.append("tcp        0      0 192.168.1.105:22        192.168.1.10:52341      ESTABLISHED 1024/sshd")
            lines.append("tcp        0      0 192.168.1.105:443       142.250.185.78:443      TIME_WAIT   -")
        
        return CommandResult.ok("\n".join(lines))


@register_command
class SsCommand(BaseCommand):
    """Display socket statistics."""
    
    name = "ss"
    help_short = "Soket istatistiklerini gösterir"
    help_long = """ss - soket istatistikleri

netstat'ın modern alternatifi. Daha hızlı ve detaylı.

Seçenekler:
  -t    TCP soketleri
  -u    UDP soketleri  
  -l    Dinleyen soketler
  -n    Sayısal adresler"""
    usage = "ss [-tulnp]"
    
    def execute(self, args: list[str]) -> CommandResult:
        lines = [
            "Netid  State   Recv-Q  Send-Q   Local Address:Port    Peer Address:Port  Process",
            "tcp    LISTEN  0       128      0.0.0.0:22             0.0.0.0:*          sshd",
            "tcp    ESTAB   0       0        192.168.1.105:22       192.168.1.10:52341 sshd",
            "udp    UNCONN  0       0        0.0.0.0:68             0.0.0.0:*          dhclient",
        ]
        return CommandResult.ok("\n".join(lines))


@register_command
class CurlCommand(BaseCommand):
    """Transfer data from URLs."""
    
    name = "curl"
    help_short = "URL'den veri indirir"
    help_long = """curl - veri transferi

URL'lerden veri indirir veya gönderir.

Seçenekler:
  -I, --head     Sadece başlıkları göster
  -o DOSYA       Çıktıyı dosyaya yaz
  -s, --silent   Sessiz mod
  -v, --verbose  Detaylı çıktı"""
    usage = "curl [seçenekler] <URL>"
    min_args = 1
    
    MOCK_RESPONSES = {
        "http://example.com": "<!DOCTYPE html><html><head><title>Example</title></head><body><h1>Example Domain</h1></body></html>",
        "https://api.github.com": '{"current_user_url":"https://api.github.com/user"}',
        "https://httpbin.org/ip": '{"origin": "192.168.1.105"}',
    }
    
    def execute(self, args: list[str]) -> CommandResult:
        head_only = False
        silent = False
        verbose = False
        output_file = None
        url = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-I", "--head"):
                head_only = True
            elif arg in ("-s", "--silent"):
                silent = True
            elif arg in ("-v", "--verbose"):
                verbose = True
            elif arg in ("-o", "--output"):
                i += 1
                output_file = args[i] if i < len(args) else None
            elif not arg.startswith("-"):
                url = arg
            i += 1
        
        if not url:
            return CommandResult.fail("curl: URL belirtilmedi")
        
        # Normalize URL
        if not url.startswith("http"):
            url = "http://" + url
        
        if head_only:
            lines = [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html; charset=UTF-8",
                "Content-Length: 1256",
                "Server: nginx/1.18.0",
                f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}",
            ]
            return CommandResult.ok("\n".join(lines))
        
        # Get response
        response = self.MOCK_RESPONSES.get(url, f"<html><body>Response from {url}</body></html>")
        
        if output_file:
            try:
                self.fs.write(output_file, response)
                return CommandResult.ok(f"'{output_file}' dosyasına kaydedildi")
            except Exception as e:
                return CommandResult.fail(f"curl: '{output_file}' yazılamadı: {e}")
        
        if verbose:
            lines = [
                f"* Connecting to {url}...",
                "* Connected",
                "> GET / HTTP/1.1",
                f"> Host: {url.split('/')[2]}",
                "< HTTP/1.1 200 OK",
                "<",
                response
            ]
            return CommandResult.ok("\n".join(lines))
        
        return CommandResult.ok(response)


@register_command
class WgetCommand(BaseCommand):
    """Download files from web."""
    
    name = "wget"
    help_short = "Dosya indirir"
    help_long = """wget - web'den indirme

URL'den dosya indirir.

Seçenekler:
  -O DOSYA    Çıktı dosya adı
  -q          Sessiz mod
  -c          Devam et (yarım kalan)"""
    usage = "wget [seçenekler] <URL>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        output_file = None
        quiet = False
        url = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("-O", "--output-document"):
                i += 1
                output_file = args[i] if i < len(args) else None
            elif arg in ("-q", "--quiet"):
                quiet = True
            elif not arg.startswith("-"):
                url = arg
            i += 1
        
        if not url:
            return CommandResult.fail("wget: URL eksik")
        
        # Get filename from URL
        if not output_file:
            output_file = url.split("/")[-1] or "index.html"
        
        # Simüle et
        lines = []
        if not quiet:
            lines = [
                f"--{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}--  {url}",
                f"Resolving {url.split('/')[2]}...",
                "Connecting... connected.",
                "HTTP request sent, awaiting response... 200 OK",
                f"Length: 1256 (1.2K) [text/html]",
                f"Saving to: '{output_file}'",
                "",
                f"'{output_file}'          100%[===================>]   1.23K  --.-KB/s    in 0s",
                "",
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (12.3 MB/s) - '{output_file}' saved [1256/1256]",
            ]
        
        # Dosyayı oluştur
        try:
            self.fs.write(output_file, f"<html><body>Downloaded from {url}</body></html>")
        except:
            pass
        
        return CommandResult.ok("\n".join(lines) if lines else "")


@register_command
class HostCommand(BaseCommand):
    """DNS lookup utility."""
    
    name = "host"
    help_short = "DNS sorgusu yapar"
    help_long = """host - DNS arama

Alan adı DNS bilgilerini sorgular."""
    usage = "host <alan_adı>"
    min_args = 1
    
    DNS_RECORDS = {
        "google.com": ("142.250.185.78", "2607:f8b0:4004:800::200e"),
        "github.com": ("140.82.121.4", "2606:50c0:8000::64"),
        "localhost": ("127.0.0.1", "::1"),
    }
    
    def execute(self, args: list[str]) -> CommandResult:
        domain = args[0]
        
        if domain in self.DNS_RECORDS:
            ipv4, ipv6 = self.DNS_RECORDS[domain]
            lines = [
                f"{domain} has address {ipv4}",
                f"{domain} has IPv6 address {ipv6}",
            ]
        else:
            ip = f"93.184.{random.randint(1, 254)}.{random.randint(1, 254)}"
            lines = [f"{domain} has address {ip}"]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class DigCommand(BaseCommand):
    """DNS lookup utility (detailed)."""
    
    name = "dig"
    help_short = "Detaylı DNS sorgusu"
    help_long = """dig - detaylı DNS arama

DNS kayıtlarını detaylı sorgular."""
    usage = "dig <alan_adı> [kayıt_tipi]"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        domain = args[0]
        record_type = args[1].upper() if len(args) > 1 else "A"
        
        ip = f"93.184.{random.randint(1, 254)}.{random.randint(1, 254)}"
        
        lines = [
            f"; <<>> DiG 9.16.1 <<>> {domain}",
            ";; QUESTION SECTION:",
            f";{domain}.\t\t\tIN\t{record_type}",
            "",
            ";; ANSWER SECTION:",
            f"{domain}.\t\t300\tIN\t{record_type}\t{ip}",
            "",
            f";; Query time: {random.randint(10, 50)} msec",
            ";; SERVER: 8.8.8.8#53(8.8.8.8)",
            f";; WHEN: {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}",
        ]
        
        return CommandResult.ok("\n".join(lines))


@register_command
class TracerouteCommand(BaseCommand):
    """Trace packet route to host."""
    
    name = "traceroute"
    aliases = ["tracepath"]
    help_short = "Paket yolunu izler"
    help_long = """traceroute - yol izleme

Hedefe giden paketlerin geçtiği yönlendiricileri gösterir."""
    usage = "traceroute <hedef>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        target = args[0]
        
        # Simüle edilmiş traceroute
        lines = [f"traceroute to {target}, 30 hops max, 60 byte packets"]
        
        hops = [
            ("192.168.1.1", "gateway"),
            ("10.0.0.1", "isp-router"),
            ("72.14.215.85", "google-edge"),
        ]
        
        for i, (ip, name) in enumerate(hops, 1):
            time1 = round(random.uniform(1, 10), 3)
            time2 = round(random.uniform(1, 10), 3)
            time3 = round(random.uniform(1, 10), 3)
            lines.append(f" {i}  {name} ({ip})  {time1} ms  {time2} ms  {time3} ms")
        
        # Final hop
        final_ip = f"93.184.{random.randint(1, 254)}.{random.randint(1, 254)}"
        lines.append(f" {len(hops)+1}  {target} ({final_ip})  {random.uniform(10, 30):.3f} ms")
        
        return CommandResult.ok("\n".join(lines))


@register_command
class NslookupCommand(BaseCommand):
    """Query DNS nameservers."""
    
    name = "nslookup"
    help_short = "DNS sunucusunu sorgular"
    help_long = """nslookup - isim sunucusu sorgusu

DNS sunucusundan alan adı bilgisi sorgular."""
    usage = "nslookup <alan_adı>"
    min_args = 1
    
    def execute(self, args: list[str]) -> CommandResult:
        domain = args[0]
        ip = f"93.184.{random.randint(1, 254)}.{random.randint(1, 254)}"
        
        lines = [
            "Server:\t\t8.8.8.8",
            "Address:\t8.8.8.8#53",
            "",
            "Non-authoritative answer:",
            f"Name:\t{domain}",
            f"Address: {ip}",
        ]
        
        return CommandResult.ok("\n".join(lines))
