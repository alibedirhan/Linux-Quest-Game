# 🐧 Linux Quest Game

<div align="center">

![Version](https://img.shields.io/badge/version-3.7.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
[![YouTube](https://img.shields.io/badge/YouTube-@ali__bedirhan-red.svg)](https://youtube.com/@ali_bedirhan)

**🎮 Hacknet tarzı interaktif Linux öğrenme oyunu**

[Özellikler](#-özellikler) •
[Kurulum](#-kurulum) •
[Kullanım](#-kullanım) •
[Görevler](#-görevler) •
[Katkıda Bulunma](#-katkıda-bulunma)

<img src="https://raw.githubusercontent.com/alibedirhan/Linux-Quest-Game/main/assets/demo.gif" alt="Demo" width="600">

</div>

---

## 🎮 Nedir?

**Linux Quest Game**, terminal tabanlı interaktif bir Linux öğrenme oyunudur. Güvenli bir sanal ortamda Linux komutlarını pratik yaparak öğrenirsiniz. `rm -rf /` gibi tehlikeli komutları bile güvenle deneyebilirsiniz!

### 🎬 Video Eğitim

Oyunun nasıl oynandığını görmek için YouTube kanalımı ziyaret edin:

[![YouTube](https://img.shields.io/badge/YouTube-Eğitim_Videoları-red?style=for-the-badge&logo=youtube)](https://youtube.com/@ali_bedirhan)

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

### 🔊 Ses Desteği
- Komut sesleri
- Başarı sesleri
- Opsiyonel (kapatılabilir)

## 📋 Gereksinimler

- **İşletim Sistemi:** Linux (Ubuntu, Debian, Fedora, Arch, vb.)
- **Python:** 3.10 veya üstü
- **Terminal:** Minimum 80x24, önerilen 120x35
- **Bağımlılık:** Yok! (Sadece Python standart kütüphanesi)

## 🚀 Kurulum

### Hızlı Kurulum

```bash
# Depoyu klonla
git clone https://github.com/alibedirhan/Linux-Quest-Game.git
cd Linux-Quest-Game

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
| `F1` | 💡 Akıllı Yardım (ipuçları) |
| `F2` | 📊 İstatistikler |
| `F3` | 🏆 Başarı Galerisi |
| `Tab` | ⌨️ Otomatik tamamlama |
| `↑` / `↓` | 📜 Komut geçmişi |
| `Ctrl+H` | 💭 Hızlı ipucu |
| `Ctrl+R` | 🔄 Görevi sıfırla |
| `ESC` | ⏸️ Duraklatma menüsü |

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
| 1 | Temel Komutlar | 🟢 Eğitim | `pwd`, `ls`, `cd` komutlarını öğren |
| 2 | Dosya İşlemleri | 🟢 Kolay | Dosya ve klasör oluşturma, silme |
| 3 | Sistem Gezisi | 🟡 Kolay | Linux dosya sistemi yapısını keşfet |
| 4 | Metin İşleme | 🟡 Orta | Dosya içeriği okuma ve metin işleme |
| 5 | Tehlike Bölgesi | 🟠 Orta | ⚠️ Tehlikeli komutları güvenle dene! |

### 🔓 Hacker Eğitimi Serisi

| # | Görev | Zorluk | Açıklama |
|---|-------|--------|----------|
| 1 | Sistem Keşfi | 🟡 Orta | `whoami`, `hostname`, `/etc/passwd` |
| 2 | Log Analizi | 🟡 Orta | `grep`, `tail`, log dosyaları |
| 3 | Dosya Avı | 🔴 Zor | Gizli dosyalar, `find`, `echo >` |

## 🎨 Temalar

```bash
./play.sh --theme matrix     # 💚 Klasik yeşil hacker
./play.sh --theme cyberpunk  # 💜 Neon mavi/pembe
./play.sh --theme retro      # 🟠 Amber terminal
./play.sh --theme ocean      # 💙 Mavi tonları
./play.sh --theme mono       # ⚪ Siyah/Beyaz
```

## 📁 Proje Yapısı

```
Linux-Quest-Game/
├── data/
│   └── sounds/             # Ses dosyaları
├── src/
│   ├── core/               # Çekirdek sistemler
│   │   ├── game.py         # Ana oyun döngüsü
│   │   ├── achievements.py # Başarı sistemi
│   │   └── audio.py        # Ses sistemi
│   ├── simulation/         # Sanal Linux
│   │   ├── filesystem.py   # Sanal dosya sistemi
│   │   ├── shell.py        # Komut yorumlayıcı
│   │   └── commands/       # Komut implementasyonları
│   └── missions/           # Görev sistemi
├── tests/                  # Test dosyaları (116 test)
├── play.sh                 # Başlatıcı script
└── README.md
```

## 🧪 Test

```bash
# Tüm testleri çalıştır
python3 -m pytest

# Detaylı çıktı
python3 -m pytest -v
```

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Detaylar için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'feat: amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Changelog

Tüm değişiklikler için [CHANGELOG.md](CHANGELOG.md) dosyasına bakın.

## 📄 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👤 Geliştirici

<div align="center">

**Ali Bedirhan**

[![YouTube](https://img.shields.io/badge/YouTube-@ali__bedirhan-red?style=for-the-badge&logo=youtube)](https://youtube.com/@ali_bedirhan)
[![GitHub](https://img.shields.io/badge/GitHub-alibedirhan-black?style=for-the-badge&logo=github)](https://github.com/alibedirhan)

</div>

---

<div align="center">

⭐ **Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!** ⭐

🐧 **Linux öğrenmeye başla!** 🐧

</div>
