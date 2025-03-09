from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
import os
import json
from datetime import datetime
import argparse
from pyngrok import ngrok

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app)

# Aktif oyunları sakla
oyunlar = {}

# Soruları JSON dosyasından yükle
def sorulari_yukle():
    """Soruları questions.json dosyasından yükle"""
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Dosya bulunamazsa varsayılan soruları döndür
        return {
            "truth": ["Bir doğruluk sorusu cevaplayın."],
            "dare": ["Bir cesaret görevi yapın."]
        }

def oyun_id_olustur():
    """Rastgele bir oyun ID'si oluştur"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

@app.route('/')
def anasayfa():
    """Ana sayfayı göster"""
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def oyun_olustur():
    """Yeni bir oyun oluştur"""
    oyuncu_sayisi = int(request.form.get('player_count', 2))
    
    # Oyuncu sayısını doğrula
    if oyuncu_sayisi < 2 or oyuncu_sayisi > 50:
        return jsonify({'error': 'Oyuncu sayısı 2 ile 50 arasında olmalıdır'}), 400
    
    # Benzersiz bir oyun ID'si oluştur
    oyun_id = oyun_id_olustur()
    while oyun_id in oyunlar:
        oyun_id = oyun_id_olustur()
    
    # Oyunu oluştur
    oyunlar[oyun_id] = {
        'oyuncular': {},
        'oyuncu_sayisi': oyuncu_sayisi,
        'siradaki_oyuncu': None,
        'baslamis': False,
        'olusturulma_zamani': datetime.now(),
        'turlar': [],
        'mevcut_soru': None,
        'soru_tipi': None,
        'hazir_oyuncular': 0
    }
    
    # Oluşturan kişiyi ilk oyuncu olarak ekle
    oyuncu_adi = request.form.get('player_name', 'Ev Sahibi')
    oyuncu_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    oyunlar[oyun_id]['oyuncular'][oyuncu_id] = {
        'ad': oyuncu_adi,
        'id': oyuncu_id,
        'ev_sahibi': True,
        'bagli': True,
        'hazir': False
    }
    
    # Oyuncu bilgilerini oturumda sakla
    session['oyuncu_id'] = oyuncu_id
    session['oyun_id'] = oyun_id
    
    return jsonify({
        'game_id': oyun_id,
        'player_id': oyuncu_id,
        'join_url': f"/tod/{oyun_id}"
    })

@app.route('/tod/<oyun_id>')
def oyuna_katil_sayfasi(oyun_id):
    """Oyuna katılma sayfasını göster"""
    if oyun_id not in oyunlar:
        return render_template('error.html', message="Oyun bulunamadı")
    
    # Oyuncunun zaten oyunda olup olmadığını kontrol et
    oyuncu_id = session.get('oyuncu_id')
    if oyuncu_id and oyuncu_id in oyunlar[oyun_id]['oyuncular']:
        return render_template('game.html', game_id=oyun_id, player_id=oyuncu_id)
    
    return render_template('join.html', game_id=oyun_id)

@app.route('/tod/<oyun_id>/join', methods=['POST'])
def oyuna_katil(oyun_id):
    """Mevcut bir oyuna katıl"""
    if oyun_id not in oyunlar:
        return jsonify({'error': 'Oyun bulunamadı'}), 404
    
    oyun = oyunlar[oyun_id]
    
    # Oyunun dolu olup olmadığını kontrol et
    if len(oyun['oyuncular']) >= oyun['oyuncu_sayisi']:
        return jsonify({'error': 'Oyun dolu'}), 400
    
    # Oyunun başlamış olup olmadığını kontrol et
    if oyun['baslamis']:
        return jsonify({'error': 'Oyun zaten başlamış'}), 400
    
    # Oyuncuyu oyuna ekle
    oyuncu_adi = request.form.get('player_name')
    if not oyuncu_adi:
        return jsonify({'error': 'Oyuncu adı gereklidir'}), 400
    
    oyuncu_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    oyun['oyuncular'][oyuncu_id] = {
        'ad': oyuncu_adi,
        'id': oyuncu_id,
        'ev_sahibi': False,
        'bagli': True,
        'hazir': False
    }
    
    # Oyuncu bilgilerini oturumda sakla
    session['oyuncu_id'] = oyuncu_id
    session['oyun_id'] = oyun_id
    
    # Diğer oyunculara bildir
    socketio.emit('player_joined', {
        'player_name': oyuncu_adi,
        'player_id': oyuncu_id,
        'player_count': len(oyun['oyuncular']),
        'max_players': oyun['oyuncu_sayisi']
    }, room=oyun_id)
    
    return jsonify({
        'success': True,
        'player_id': oyuncu_id
    })

@app.route('/tod/<oyun_id>/game')
def oyun_sayfasi(oyun_id):
    """Oyun sayfasını göster"""
    if oyun_id not in oyunlar:
        return render_template('error.html', message="Oyun bulunamadı")
    
    oyuncu_id = session.get('oyuncu_id')
    if not oyuncu_id or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return redirect(url_for('oyuna_katil_sayfasi', oyun_id=oyun_id))
    
    return render_template('game.html', game_id=oyun_id, player_id=oyuncu_id)

# Socket.IO olayları
@socketio.on('connect')
def baglanti_kur():
    """İstemci bağlantısını yönet"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if oyun_id and oyuncu_id and oyun_id in oyunlar and oyuncu_id in oyunlar[oyun_id]['oyuncular']:
        join_room(oyun_id)
        oyunlar[oyun_id]['oyuncular'][oyuncu_id]['bagli'] = True
        oyunlar[oyun_id]['oyuncular'][oyuncu_id]['connected'] = True
        
        # Hazır oyuncuları yeniden say
        hazir_sayisi = 0
        for o in oyunlar[oyun_id]['oyuncular'].values():
            if o.get('hazir', False) or o.get('ready', False):
                hazir_sayisi += 1
        
        oyunlar[oyun_id]['hazir_oyuncular'] = hazir_sayisi
        
        # Diğer oyunculara bildir
        emit('player_connected', {
            'player_id': oyuncu_id,
            'player_name': oyunlar[oyun_id]['oyuncular'][oyuncu_id]['ad']
        }, room=oyun_id)
        
        # Oyun durumunu oyuncuya gönder
        emit('game_state', {
            'players': list(oyunlar[oyun_id]['oyuncular'].values()),
            'started': oyunlar[oyun_id]['baslamis'],
            'current_player': oyunlar[oyun_id]['siradaki_oyuncu'],
            'player_count': oyunlar[oyun_id]['oyuncu_sayisi'],
            'current_players': len(oyunlar[oyun_id]['oyuncular']),
            'ready_players': oyunlar[oyun_id]['hazir_oyuncular']
        })
        
        # Tüm oyunculara oyuncu listesini güncelle
        emit('player_list_update', {
            'players': list(oyunlar[oyun_id]['oyuncular'].values())
        }, room=oyun_id)

@socketio.on('disconnect')
def baglanti_kes():
    """İstemci bağlantı kesimini yönet"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if oyun_id and oyuncu_id and oyun_id in oyunlar and oyuncu_id in oyunlar[oyun_id]['oyuncular']:
        oyunlar[oyun_id]['oyuncular'][oyuncu_id]['bagli'] = False
        
        # Diğer oyunculara bildir
        emit('player_disconnected', {
            'player_id': oyuncu_id,
            'player_name': oyunlar[oyun_id]['oyuncular'][oyuncu_id]['ad']
        }, room=oyun_id)
        
        # Boş oyunları temizle
        tum_baglanti_kesik = all(not oyuncu['bagli'] for oyuncu in oyunlar[oyun_id]['oyuncular'].values())
        if tum_baglanti_kesik:
            del oyunlar[oyun_id]

@socketio.on('player_ready')
def oyuncu_hazir():
    """Oyuncu hazır olduğunu bildirir"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    oyuncu = oyun['oyuncular'][oyuncu_id]
    
    # Oyuncu zaten hazırsa işlem yapma
    if oyuncu.get('hazir', False) or oyuncu.get('ready', False):
        return
    
    # Oyuncuyu hazır olarak işaretle
    oyuncu['hazir'] = True
    oyuncu['ready'] = True
    
    # Hazır oyuncuları yeniden say
    hazir_sayisi = 0
    for o in oyun['oyuncular'].values():
        if o.get('hazir', False) or o.get('ready', False):
            hazir_sayisi += 1
    
    oyun['hazir_oyuncular'] = hazir_sayisi
    
    print(f"Oyuncu hazır: {oyuncu['ad']}, Hazır oyuncular: {oyun['hazir_oyuncular']}")
    
    # Tüm oyunculara bildir
    emit('player_ready_update', {
        'player_id': oyuncu_id,
        'player_name': oyuncu['ad'],
        'ready_players': oyun['hazir_oyuncular'],
        'total_players': len(oyun['oyuncular'])
    }, room=oyun_id)
    
    # Tüm oyunculara güncel oyuncu listesini gönder
    emit('player_list_update', {
        'players': list(oyun['oyuncular'].values())
    }, room=oyun_id)

@socketio.on('get_game_state')
def get_game_state():
    """Oyun durumunu istemciye gönderir"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    
    # Hazır oyuncuları yeniden say
    hazir_sayisi = 0
    for o in oyun['oyuncular'].values():
        if o.get('hazir', False) or o.get('ready', False):
            hazir_sayisi += 1
    
    oyun['hazir_oyuncular'] = hazir_sayisi
    
    # Oyun durumunu oyuncuya gönder
    emit('game_state', {
        'players': list(oyun['oyuncular'].values()),
        'started': oyun['baslamis'],
        'current_player': oyun['siradaki_oyuncu'],
        'player_count': oyun['oyuncu_sayisi'],
        'current_players': len(oyun['oyuncular']),
        'ready_players': oyun['hazir_oyuncular']
    })

@socketio.on('start_game')
def oyunu_baslat(data):
    """Oyunu başlat"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    oyuncu = oyun['oyuncular'][oyuncu_id]
    
    # Sadece ev sahibi oyunu başlatabilir
    if not oyuncu['ev_sahibi']:
        return
    
    # Başlamak için en az 2 oyuncu gerekli
    if len(oyun['oyuncular']) < 2:
        emit('error', {'message': 'Başlamak için en az 2 oyuncu gerekli'})
        return
    
    # Oyunu başlat
    oyun['baslamis'] = True
    
    print(f"Oyun başlatıldı! Oyun ID: {oyun_id}, Oyuncu sayısı: {len(oyun['oyuncular'])}")
    
    # İlk oyuncuyu rastgele seç
    oyun['siradaki_oyuncu'] = random.choice(list(oyun['oyuncular'].keys()))
    
    print(f"İlk oyuncu: {oyun['oyuncular'][oyun['siradaki_oyuncu']]['ad']}")
    
    # Tüm oyunculara bildir
    emit('game_started', {
        'current_player': oyun['siradaki_oyuncu'],
        'current_player_name': oyun['oyuncular'][oyun['siradaki_oyuncu']]['ad']
    }, room=oyun_id)

@socketio.on('choose_type')
def tur_sec(data):
    """Oyuncu doğruluk veya cesaret seçer"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    
    # Sıranın bu oyuncuda olduğundan emin ol
    if oyun['siradaki_oyuncu'] != oyuncu_id:
        return
    
    soru_tipi = data.get('type')
    if soru_tipi not in ['truth', 'dare']:
        return
    
    # Soruları yükle
    sorular = sorulari_yukle()
    
    # Tipe göre rastgele bir soru seç
    soru = random.choice(sorular[soru_tipi])
    oyun['mevcut_soru'] = soru
    oyun['soru_tipi'] = soru_tipi
    
    # Tüm oyunculara bildir
    emit('question_chosen', {
        'player_id': oyuncu_id,
        'player_name': oyun['oyuncular'][oyuncu_id]['ad'],
        'question_type': soru_tipi,
        'question': soru
    }, room=oyun_id)

@socketio.on('complete_turn')
def turu_tamamla(data):
    """Oyuncu turunu tamamlar"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    
    # Sıranın bu oyuncuda olduğundan emin ol
    if oyun['siradaki_oyuncu'] != oyuncu_id:
        return
    
    # Turu kaydet
    oyun['turlar'].append({
        'oyuncu_id': oyuncu_id,
        'oyuncu_adi': oyun['oyuncular'][oyuncu_id]['ad'],
        'soru_tipi': oyun['soru_tipi'],
        'soru': oyun['mevcut_soru'],
        'tamamlandi': True
    })
    
    # Sonraki oyuncuyu seç
    oyuncu_idleri = list(oyun['oyuncular'].keys())
    mevcut_index = oyuncu_idleri.index(oyuncu_id)
    sonraki_index = (mevcut_index + 1) % len(oyuncu_idleri)
    oyun['siradaki_oyuncu'] = oyuncu_idleri[sonraki_index]
    
    # Mevcut soruyu sıfırla
    oyun['mevcut_soru'] = None
    oyun['soru_tipi'] = None
    
    # Tüm oyunculara bildir
    emit('turn_completed', {
        'next_player': oyun['siradaki_oyuncu'],
        'next_player_name': oyun['oyuncular'][oyun['siradaki_oyuncu']]['ad']
    }, room=oyun_id)

@socketio.on('skip_turn')
def turu_atla(data):
    """Oyuncu turunu atlar"""
    oyun_id = session.get('oyun_id')
    oyuncu_id = session.get('oyuncu_id')
    
    if not oyun_id or not oyuncu_id or oyun_id not in oyunlar or oyuncu_id not in oyunlar[oyun_id]['oyuncular']:
        return
    
    oyun = oyunlar[oyun_id]
    
    # Sıranın bu oyuncuda olduğundan emin ol
    if oyun['siradaki_oyuncu'] != oyuncu_id:
        return
    
    # Turu kaydet
    if oyun['soru_tipi']:
        oyun['turlar'].append({
            'oyuncu_id': oyuncu_id,
            'oyuncu_adi': oyun['oyuncular'][oyuncu_id]['ad'],
            'soru_tipi': oyun['soru_tipi'],
            'soru': oyun['mevcut_soru'],
            'tamamlandi': False
        })
    
    # Sonraki oyuncuyu seç
    oyuncu_idleri = list(oyun['oyuncular'].keys())
    mevcut_index = oyuncu_idleri.index(oyuncu_id)
    sonraki_index = (mevcut_index + 1) % len(oyuncu_idleri)
    oyun['siradaki_oyuncu'] = oyuncu_idleri[sonraki_index]
    
    # Mevcut soruyu sıfırla
    oyun['mevcut_soru'] = None
    oyun['soru_tipi'] = None
    
    # Tüm oyunculara bildir
    emit('turn_skipped', {
        'player_id': oyuncu_id,
        'player_name': oyun['oyuncular'][oyuncu_id]['ad'],
        'next_player': oyun['siradaki_oyuncu'],
        'next_player_name': oyun['oyuncular'][oyun['siradaki_oyuncu']]['ad']
    }, room=oyun_id)

def ngrok_baslat(port):
    """Uygulamayı internete açmak için ngrok tüneli başlat"""
    try:
        public_url = ngrok.connect(port).public_url
        print(f" * Ngrok tüneli şu adreste kullanılabilir: {public_url}")
        print(f" * Web arayüzüne şu adresten erişebilirsiniz: {public_url}")
        return public_url
    except Exception as e:
        print(f" * Ngrok bağlantısı kurulamadı: {str(e)}")
        print(" * Ngrok olmadan devam ediliyor. Uygulama sadece yerel ağda erişilebilir olacak.")
        print(f" * Yerel adres: http://localhost:{port}")
        print(" * Eğer başka bir ngrok oturumu çalışıyorsa, lütfen onu kapatın veya ngrok yapılandırma dosyası kullanın.")
        print(" * Daha fazla bilgi için: https://ngrok.com/docs/secure-tunnels/ngrok-agent/reference/config")
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Doğruluk mu Cesaret mi Oyun Sunucusu')
    parser.add_argument('--ngrok', action='store_true', help='Ngrok tünelini etkinleştir')
    parser.add_argument('--port', type=int, default=5000, help='Sunucunun çalışacağı port')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Sunucunun çalışacağı host')
    args = parser.parse_args()
    
    port = args.port
    
    # İstenirse ngrok'u başlat
    if args.ngrok:
        public_url = ngrok_baslat(port)
        if public_url:
            print(f" * Bu bağlantıyı arkadaşlarınızla paylaşın: {public_url}")
    
    # Uygulamayı çalıştır
    socketio.run(app, debug=True, host=args.host, port=port) 