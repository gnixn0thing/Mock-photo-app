cat << 'EOF' > README.md
# Mock PhotoShare App - Eğitim Demosi

Bu proje sosyal mühendislik ve penetrasyon testi eğitimi için hazırlanmış güvenli bir demo uygulamasıdır.

## ⚠️ ÖNEMLİ UYARI
Bu uygulama sadece eğitim ve laboratuvar amaçlıdır. Gerçek hesap bilgilerini girmeyin!

## 🚀 Kurulum

```bash
# Gerekli paketi yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python app.py


## 🔑 4. Git ve GitHub Yapılandırması

### Git yapılandırması:
```bash
# İlk kez kullanıyorsanız git config ayarlayın
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# SSH key oluştur (eğer yoksa)
ssh-keygen -t ed25519 -C "your.email@example.com"

# SSH key'i kopyala
cat ~/.ssh/id_ed25519.pub
