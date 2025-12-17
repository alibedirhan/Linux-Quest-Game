# 🐧 Linux Command Quest

<div align="center">

![Version](https://img.shields.io/badge/version-3.7.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**Hacknet tarzı interaktif Linux öğrenme oyunu**

[Özellikler](#-özellikler) •
[Kurulum](#-kurulum) •
[Kullanım](#-kullanım) •
[Görevler](#-görevler) •
[Geliştirme](#-geliştirme)

</div>

---

## 🎮 Nedir?

**Linux Command Quest**, terminal tabanlı interaktif bir Linux öğrenme oyunudur. Güvenli bir sanal ortamda Linux komutlarını pratik yaparak öğrenirsiniz. `rm -rf /` gibi tehlikeli komutları bile güvenle deneyebilirsiniz!

<details>
<summary>📸 Ekran Görüntüleri</summary>

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🐧 LINUX QUEST │ Temel Komutlar          Puan: 30 │ 🏆 50 │ 💡 3/3         │
├──────────────────────────────┬──────────────────────────────────────────────┤
│ ┌──────────────────────────┐ │ ┌──────────────────────────────────────────┐ │
│ │       📋 GÖREVLER        │ │ │               TERMİNAL                   │ │
│ ├──────────────────────────┤ │ ├──────────────────────────────────────────┤ │
│ │ ✓ Mevcut dizini göster   │ │ │                                          │ │
│ │ ✓ Dizin içeriğini listele│ │ │ user@quest:~$ pwd                        │ │
│ │ ▶ Gizli dosyaları göster │ │ │ /home/user                               │ │
│ │ ○ Documents'a git        │ │ │                                          │ │
│ │ ○ Üst dizine çık         │ │ │   ✓ DOĞRU! +10 puan                      │ │
│ │ ○ Ev dizinine dön        │ │ │                                          │ │
│ │                          │ │ │ user@quest:~$ ls                         │ │
│ ├──────────────────────────┤ │ │ Documents  Downloads  Music  Pictures    │ │
│ │ ⌨ KISAYOLLAR             │ │ │                                          │ │
│ │  F1       Yardım         │ │ │                                          │ │
│ │  F2       İstatistik     │ │ │                                          │ │
│ │  Tab      Tamamla        │ │ │                                          │ │
│ └──────────────────────────┘ │ └──────────────────────────────────────────┘ │
├──────────────────────────────┴──────────────────────────────────────────────┤
│ [▓▓▓░░░░░░░] 30% │ F1: Yardım │ F2: Stats │ F3: Başarılar │ ESC: Menü     │
└─────────────────────────────────────────────────────────────────────────────┘
```

</details>

## ✨ Özellikler

### 🔒 Güvenli Sandbox
- Sanal dosya sistemi - gerçek sisteminize dokunmaz
- Tehlikeli komutları güvenle deneyebilirsiniz
- `rm -rf /` bile simüle edilir!

### 📚 Kapsamlı Eğitim
- **8 görev paketi** (Eğitim + Hacker Eğitimi)
- **49 interaktif görev**
- **25+ Linux komutu**
- Türkçe açıklamalar ve ipuçları
- Akıllı yardım sistemi (F1)

### 🏆 Başarı Sistemi
- **44 başarı** kazanılabilir
- İstatistik takibi (F2)
- Başarı galerisi (F3)
- Puan ve combo sistemi

### 🎨 Profesyonel Arayüz
- Hacknet tarzı terminal estetiği
- **5 farklı renk teması** (Matrix, Cyberpunk, Retro, Ocean, Mono)
- Boot animasyonu
- Profil özelleştirme (F4)

### 🛠 Gelişmiş Özellikler
- Komut geçmişi (↑/↓ tuşları)
- Tab ile otomatik tamamlama
- Pipe ve redirect desteği (`|`, `>`, `>>`)
- $HOME ve $USER değişken desteği
- Save/Load sistemi

## 📋 Gereksinimler

- **İşletim Sistemi:** Linux (Ubuntu, Debian, Fedora, Arch, vb.)
- **Python:** 3.10 veya üstü
- **Terminal:** Minimum 80x24, önerilen 120x35
- **Bağımlılık:** Yok! (Sadece Python standart kütüphanesi)

## 🚀 Kurulum

### Hızlı Kurulum

```bash
# Depoyu klonla
git clone https://github.com/alibedirhan/linux-command-quest.git
cd linux-command-quest

# İzinleri ayarla
chmod +x play.sh

# Başlat!
./play.sh
```

### Alternatif Başlatma

```bash
# Doğrudan Python ile
python3 -m src.main

# Farklı tema ile
./play.sh --theme cyberpunk

# Boot animasyonu olmadan
./play.sh --no-boot

# Özel kullanıcı adı
./play.sh --user ali
```

## 🎮 Kullanım

### Oyun İçi Kontroller

| Tuş | İşlev |
|-----|-------|
| `F1` | Akıllı Yardım (ipuçları) |
| `F2` | İstatistikler |
| `F3` | Başarı Galerisi |
| `Tab` | Otomatik tamamlama |
| `↑` / `↓` | Komut geçmişi |
| `Ctrl+H` | Hızlı ipucu |
| `Ctrl+R` | Görevi sıfırla |
| `ESC` | Duraklatma menüsü |

### Ana Menü Kontroller

| Tuş | İşlev |
|-----|-------|
| `F2` | İstatistikler |
| `F3` | Başarılar |
| `F4` | Profil düzenle |
| `Q` | Çıkış |

### Desteklenen Komutlar

| Kategori | Komutlar |
|----------|----------|
| **Navigasyon** | `pwd`, `cd`, `ls` |
| **Dosya İşlemleri** | `touch`, `mkdir`, `rm`, `rmdir`, `cp`, `mv`, `find` |
| **Metin İşleme** | `cat`, `echo`, `head`, `tail`, `grep`, `wc` |
| **Sistem** | `clear`, `whoami`, `hostname`, `date`, `uname`, `help`, `history` |

## 📖 Görevler

### 📚 Eğitim Serisi

| # | Görev | Zorluk | Açıklama |
|---|-------|--------|----------|
| 1 | Temel Komutlar | Eğitim | `pwd`, `ls`, `cd` komutlarını öğren |
| 2 | Dosya İşlemleri | Kolay | Dosya ve klasör oluşturma, silme |
| 3 | Sistem Gezisi | Kolay | Linux dosya sistemi yapısını keşfet |
| 4 | Metin İşleme | Orta | Dosya içeriği okuma ve metin işleme |
| 5 | Tehlike Bölgesi | Orta | ⚠️ Tehlikeli komutları güvenle dene! |

### 🔓 Hacker Eğitimi Serisi

| # | Görev | Zorluk | Açıklama |
|---|-------|--------|----------|
| 1 | Sistem Keşfi | Orta | `whoami`, `hostname`, `/etc/passwd` |
| 2 | Log Analizi | Orta | `grep`, `tail`, log dosyaları |
| 3 | Dosya Avı | Zor | Gizli dosyalar, `find`, `echo >` |

## 🎨 Temalar

Ayarlar menüsünden veya komut satırından tema değiştirin:

```bash
# Matrix (Varsayılan) - Klasik yeşil hacker teması
./play.sh --theme matrix

# Cyberpunk - Neon mavi/pembe
./play.sh --theme cyberpunk

# Retro - Amber terminal
./play.sh --theme retro

# Ocean - Mavi tonları
./play.sh --theme ocean

# Mono - Siyah/Beyaz
./play.sh --theme mono
```

## 📁 Proje Yapısı

```
linux-command-quest/
├── src/
│   ├── core/               # Çekirdek sistemler
│   │   ├── game.py         # Ana oyun döngüsü
│   │   ├── colors.py       # Renk ve tema yönetimi
│   │   ├── achievements.py # Başarı sistemi
│   │   └── audio.py        # Ses sistemi
│   │
│   ├── simulation/         # Sanal Linux
│   │   ├── filesystem.py   # Sanal dosya sistemi
│   │   ├── shell.py        # Komut yorumlayıcı
│   │   └── commands/       # Komut implementasyonları
│   │
│   ├── missions/           # Görev sistemi
│   │   └── missions.py     # 8 görev paketi, 49 task
│   │
│   └── ui/                 # Arayüz
│       └── widgets.py      # Panel ve widget'lar
│
├── tests/                  # Test dosyaları (116 test)
├── play.sh                 # Başlatıcı script
├── pyproject.toml          # Proje yapılandırması
└── README.md               # Bu dosya
```

## 🧪 Test

```bash
# Tüm testleri çalıştır
python3 -m pytest

# Detaylı çıktı
python3 -m pytest -v

# Belirli test dosyası
python3 -m pytest tests/test_filesystem.py
```

## 🔧 Geliştirme

### Yeni Komut Ekleme

```python
from .base import BaseCommand, CommandResult, register_command

@register_command
class MyCommand(BaseCommand):
    name = "mycommand"
    help_short = "Kısa açıklama"
    usage = "mycommand [argümanlar]"
    
    def execute(self, args: list[str]) -> CommandResult:
        return CommandResult.ok("Çıktı")
```

### Yeni Görev Ekleme

`src/missions/missions.py` dosyasına:

```python
self._missions["new_mission"] = Mission(
    id="new_mission",
    name="Yeni Görev",
    description="Açıklama",
    difficulty=Difficulty.MEDIUM,
    category="tutorial",
    tasks=[
        Task(
            id="task1",
            description="Görev açıklaması",
            hint="İpucu",
            accepted_commands=["komut"],
        ),
    ],
)
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👤 Geliştirici

**Ali Bedirhan**

- YouTube: [@ali_bedirhan](https://youtube.com/@ali_bedirhan)
- GitHub: [@alibedirhan](https://github.com/alibedirhan)

---

<div align="center">

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!

**Linux öğrenmeye başla! 🐧**

</div>
