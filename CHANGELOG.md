# Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına uygundur.

## [3.7.0] - 2024-12-16

### Eklendi
- 🔓 **Hacker Eğitimi Serisi** - 3 yeni görev paketi
  - Hacker 101: Sistem Keşfi (`whoami`, `hostname`, `uname`)
  - Hacker 102: Log Analizi (`grep`, `tail`, log dosyaları)
  - Hacker 103: Dosya Avı (`find`, gizli dosyalar)
- 💡 **F1 Akıllı Yardım Sistemi** - Kademeli ipuçları (cevabı vermeden öğretici)
- ⌨️ **Kısayollar Ekranı** - Ayarlar menüsünden erişilebilir
- 🔍 **find komutu** - `-name` ve `-type` parametreleri ile dosya arama
- 🏠 **$HOME ve $USER desteği** - Ortam değişkenleri artık çalışıyor
- 📊 **Oyun içi kısayol paneli** - Sol panelde her zaman görünür

### Değiştirildi
- Ana menüden kısayol kutusu kaldırıldı (oyun içinde zaten mevcut)
- Ayarlar menüsüne "Kısayollar" seçeneği eklendi
- README.md tamamen yenilendi

### Düzeltildi
- Ayarlar → Kısayollar → Geri dönmeme sorunu
- State geçişlerinde `_previous_state` tutarlılığı
- Görev kilit açma zincirindeki hatalı referans

## [3.5.0] - 2024-12-15

### Eklendi
- 🎮 **Görev Kategorileri** - Tutorial ve Hacker kategorileri
- 📁 **/var/log/auth.log** - Hacker görevleri için log dosyası
- 🔒 **/etc/shadow** - İzin reddedildi simülasyonu

### Düzeltildi
- F2/F3/F4 tuşlarının doğru state'e dönmesi
- Profile edit önizleme canlı güncelleme

## [3.0.0] - 2024-12-14

### Eklendi
- 🏆 **Başarı Sistemi** - 44 farklı başarı
- 📊 **İstatistik Takibi** - Komut, süre, combo istatistikleri
- 💾 **Save/Load Sistemi** - Oyun ilerlemesi kaydedilir
- ⏸️ **Pause Menü** - ESC ile duraklatma
- 👤 **Profil Düzenleme** - F4 ile kullanıcı/makine adı değiştirme
- 🎨 **5 Tema** - Matrix, Cyberpunk, Retro, Ocean, Mono
- 🔊 **Ses Efektleri** - Opsiyonel ses desteği

## [2.0.0] - 2024-12-13

### Eklendi
- 📚 **5 Görev Paketi** - Temel'den Tehlike Bölgesi'ne
- 🖥️ **Çift Panel Arayüz** - Görevler + Terminal
- ⌨️ **Tab Tamamlama** - Otomatik komut/dosya tamamlama
- 📜 **Komut Geçmişi** - ↑/↓ tuşları ile gezinme
- 💡 **İpucu Sistemi** - Ctrl+H ile ipucu

## [1.0.0] - 2024-12-12

### İlk Sürüm
- Sanal dosya sistemi
- Temel Linux komutları (pwd, ls, cd, cat, echo, mkdir, touch, rm)
- Boot animasyonu
- Türkçe arayüz
