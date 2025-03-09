@echo off
echo HYPERINGS DEV - Dogruluk mu Cesaret mi?
echo =====================================
echo Ngrok ile uygulamayi baslatiliyor...
echo.
echo NOT: Eger ngrok hatasi aliyorsaniz, asagidaki secenekleri deneyebilirsiniz:
echo 1. Calisan diger ngrok oturumlarini kapatin
echo 2. Alternatif yontem kullanin:
echo    a) Ilk once ngrok'u baslatin: ngrok http 5000
echo    b) Sonra baska bir komut satirinda uygulamayi calistirin: python app.py
echo 3. Ngrok yapilandirma dosyasi kullanin:
echo    a) ngrok.yml dosyasini duzenleyip auth token'inizi ekleyin
echo    b) ngrok start --all --config=ngrok.yml
echo    c) Baska bir komut satirinda: python app.py
echo 4. Uygulamayi ngrok olmadan calistirin: run.bat
echo.
python app.py --ngrok
pause 