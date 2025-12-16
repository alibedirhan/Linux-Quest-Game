# 🤝 Katkıda Bulunma Rehberi

Linux Quest Game'e katkıda bulunmak istediğiniz için teşekkürler! 

## 🚀 Nasıl Katkıda Bulunabilirim?

### 🐛 Hata Bildirimi

1. [Issues](https://github.com/alibedirhan/Linux-Quest-Game/issues) sayfasını kontrol edin
2. Aynı hata daha önce bildirilmemiş mi bakın
3. Yeni bir issue açın ve şunları belirtin:
   - Hatanın açıklaması
   - Hatayı tekrarlama adımları
   - Beklenen davranış
   - Gerçekleşen davranış
   - Python versiyonu ve işletim sistemi

### 💡 Yeni Özellik Önerisi

1. Önce bir issue açarak önerinizi tartışın
2. Topluluk geri bildirimi alın
3. Onaylandıktan sonra geliştirmeye başlayın

### 🔧 Kod Katkısı

#### Hazırlık

```bash
# Repo'yu fork edin ve klonlayın
git clone https://github.com/KULLANICI_ADINIZ/Linux-Quest-Game.git
cd Linux-Quest-Game

# Virtual environment oluşturun
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleyin (sadece test için)
pip install pytest
```

#### Geliştirme Süreci

```bash
# Yeni branch oluşturun
git checkout -b feature/yeni-ozellik

# Değişikliklerinizi yapın
# ...

# Testleri çalıştırın
python3 -m pytest

# Commit edin
git add .
git commit -m "feat: yeni özellik açıklaması"

# Push edin
git push origin feature/yeni-ozellik
```

#### Pull Request

1. GitHub'da Pull Request açın
2. Değişikliklerinizi açıklayın
3. İlgili issue'ları referans verin

## 📝 Kod Standartları

### Python

- PEP 8 stiline uyun
- Type hints kullanın
- Docstring'ler ekleyin
- Türkçe yorumlar yazabilirsiniz

### Commit Mesajları

[Conventional Commits](https://www.conventionalcommits.org/) formatını kullanın:

```
feat: yeni özellik
fix: hata düzeltmesi
docs: dokümantasyon
style: kod formatı
refactor: kod yeniden yapılandırma
test: test ekleme/düzeltme
chore: bakım işleri
```

## 🎯 Katkı Alanları

### Kolay (Good First Issue)

- Türkçe çeviri düzeltmeleri
- Yeni başarılar ekleme
- Dokümantasyon iyileştirmeleri
- Hata mesajlarını geliştirme

### Orta

- Yeni Linux komutu ekleme
- Yeni görev paketi oluşturma
- UI geliştirmeleri

### İleri

- Yeni oyun modu ekleme
- Performans optimizasyonları
- Test coverage artırma

## 🆕 Yeni Komut Ekleme

```python
# src/simulation/commands/dosya_adi.py

from .base import BaseCommand, CommandResult, register_command

@register_command
class YeniKomut(BaseCommand):
    name = "komut_adi"
    help_short = "Kısa açıklama"
    help_long = """Uzun açıklama ve kullanım örnekleri"""
    usage = "komut_adi [seçenekler] <argümanlar>"
    min_args = 0
    max_args = 2
    
    def execute(self, args: list[str]) -> CommandResult:
        # Implementasyon
        return CommandResult.ok("Çıktı")
```

## 🎮 Yeni Görev Ekleme

```python
# src/missions/missions.py içinde

self._missions["yeni_gorev"] = Mission(
    id="yeni_gorev",
    name="Görev Adı",
    description="Görev açıklaması",
    difficulty=Difficulty.MEDIUM,
    category="tutorial",  # veya "hacker"
    tasks=[
        Task(
            id="task1",
            description="Görev açıklaması",
            hint="İpucu",
            accepted_commands=["kabul edilen komut"],
        ),
    ],
    unlocks=["sonraki_gorev"],
)
```

## ❓ Sorular?

- [Discussions](https://github.com/alibedirhan/Linux-Quest-Game/discussions) sayfasını kullanın
- YouTube: [@ali_bedirhan](https://youtube.com/@ali_bedirhan)

---

Katkılarınız için teşekkürler! 🐧
