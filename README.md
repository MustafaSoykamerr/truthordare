# Doğruluk mu Cesaret mi? (Truth or Dare)

<div align="center">
    <h3>MİDENİUM</h3>
    <p><i>Herkes İçin</i></p>
</div>

Bu proje, çevrimiçi olarak arkadaşlarınızla oynayabileceğiniz bir Doğruluk mu Cesaret mi oyunudur.

## Özellikler

- Çevrimiçi çok oyunculu oyun (2-50 oyuncu)
- Paylaşılabilir bağlantılar ile kolay katılım
- Gerçek zamanlı oyun deneyimi
- Responsive tasarım (mobil uyumlu)
- Ngrok ve özel domain desteği
- Türkçe arayüz ve kodlama
- Şık ve modern tasarım
- Koyu ve açık renk tonları
- Harici JSON dosyasında saklanan sorular

## Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)

### Adımlar

1. Projeyi klonlayın veya indirin:

```bash
git clone https://github.com/MustafaSoykamerr/truthordare.git
cd truthordare
```

2. Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

3. Uygulamayı çalıştırın:

```bash
python app.py
```

5. Tarayıcınızda `http://localhost:5000` adresine gidin.

## Ngrok ile Dış Erişim

Oyunu internet üzerinden erişilebilir yapmak için Ngrok kullanabilirsiniz:

1. Ngrok'u yükleyin (https://ngrok.com/download)
2. Uygulamayı çalıştırın:

```bash
python app.py --ngrok
```

Veya hazır script kullanın:

```bash
# Windows
run_with_ngrok.bat

# Linux/Mac
chmod +x run_with_ngrok.sh
./run_with_ngrok.sh
```

3. Ngrok tarafından verilen URL'i kullanarak oyuna internet üzerinden erişebilirsiniz.

## Özel Sorular Ekleme

Oyundaki soruları özelleştirmek için `questions.json` dosyasını düzenleyebilirsiniz. Dosya şu yapıdadır:

```json
{
    "truth": [
        "Doğruluk sorusu 1",
        "Doğruluk sorusu 2",
        ...
    ],
    "dare": [
        "Cesaret görevi 1",
        "Cesaret görevi 2",
        ...
    ]
}
```

## Özel Domain Kullanımı

Özel bir domain kullanmak için:

1. Domain DNS ayarlarınızı sunucunuzun IP adresine yönlendirin
2. Bir reverse proxy (Nginx, Apache vb.) kullanarak trafiği uygulamanıza yönlendirin

## Oyun Nasıl Oynanır?

1. Ana sayfada "Yeni Oyun Oluştur" butonuna tıklayın
2. Adınızı ve oyuncu sayısını girin
3. Oluşturulan bağlantıyı arkadaşlarınızla paylaşın
4. Tüm oyuncular katıldığında "Oyunu Başlat" butonuna tıklayın
5. Sıra size geldiğinde "Doğruluk" veya "Cesaret" seçin
6. Soruyu cevaplayın veya görevi tamamlayın
7. Eğlenceye devam edin!

## Geliştirici

Bu proje Midenium tarafından geliştirilmiştir.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için `LICENSE` dosyasına bakın. 
