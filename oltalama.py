#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Güvenli Mock "Fotoğraf Paylaşım Uygulaması" Login - Eğitim Demo
Bu uygulama sosyal mühendislik/pentest eğitimi içindir.
Gerçek marka taklit etmez, gerçek kullanıcı verisi toplamaz.
"""

from flask import Flask, request, render_template_string, redirect, url_for, flash
import json
import os
import time
from datetime import datetime
from collections import defaultdict
import threading

app = Flask(__name__)
app.secret_key = 'demo-secret-key-for-education-only'

# Rate limiting için basit in-memory store
rate_limit_store = defaultdict(list)
rate_limit_lock = threading.Lock()


def get_client_ip():
    """Client IP adresini al - proxy arkasında ise X-Forwarded-For header'ını kontrol et"""
    if request.headers.get('X-Forwarded-For'):
        # Proxy arkasındaysa ilk IP'yi al
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def check_rate_limit(ip, max_requests=10, window_seconds=60):
    """Basit rate limiting - IP başına dakikada max_requests kadar POST isteği"""
    with rate_limit_lock:
        now = time.time()
        # Eski istekleri temizle
        rate_limit_store[ip] = [req_time for req_time in rate_limit_store[ip]
                                if now - req_time < window_seconds]

        if len(rate_limit_store[ip]) >= max_requests:
            return False

        rate_limit_store[ip].append(now)
        return True


def log_request_data(form_data):
    """İstek verilerini eğitim amaçlı log dosyasına kaydet"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'client_ip': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', ''),
        'referer': request.headers.get('Referer', ''),
        'accept_language': request.headers.get('Accept-Language', ''),
        'all_headers': dict(request.headers),
        'form_data': form_data,
        'remote_port': request.environ.get('REMOTE_PORT', ''),
        'request_method': request.method,
        'request_path': request.path
    }

    # Log dosyasına JSON formatında tek satır olarak yaz
    log_file = 'demo_logs.txt'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    # Log dosyası izinlerini ayarla (sadece owner okuyabilir/yazabilir)
    try:
        os.chmod(log_file, 0o600)
    except:
        pass  # Windows'ta çalışmayabilir


# HTML Templates
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhotoShare - Giriş</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .warning-banner {
            background-color: #dc3545;
            color: white;
            text-align: center;
            padding: 10px;
            font-weight: bold;
            font-size: 14px;
        }

        .container {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }

        .logo {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo h1 {
            color: #333;
            font-size: 32px;
            font-weight: 300;
            letter-spacing: -1px;
        }

        .logo p {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102,126,234,0.1);
        }

        .form-options {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            font-size: 14px;
        }

        .remember-me {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .forgot-password {
            color: #667eea;
            text-decoration: none;
        }

        .forgot-password:hover {
            text-decoration: underline;
        }

        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .login-btn:hover {
            transform: translateY(-1px);
        }

        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-size: 14px;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: white;
            font-size: 12px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="warning-banner">
        ⚠️ Bu sayfa sadece eğitim ve laboratuvar amaçlıdır. Gerçek hesap bilgisi girmeyin. ⚠️
    </div>

    <div class="container">
        <div class="login-box">
            <div class="logo">
                <h1>PhotoShare</h1>
                <p>Fotoğraflarınızı paylaşın</p>
            </div>

            {% if error_message %}
            <div class="error-message">
                {{ error_message }}
            </div>
            {% endif %}

            <form method="POST" action="{{ url_for('login') }}">
                <div class="form-group">
                    <label for="username">Kullanıcı Adı</label>
                    <input type="text" id="username" name="username" required 
                           minlength="3" maxlength="32" 
                           placeholder="Kullanıcı adınızı girin">
                </div>

                <div class="form-group">
                    <label for="password">Şifre</label>
                    <input type="password" id="password" name="password" required 
                           minlength="3" maxlength="128" 
                           placeholder="Şifrenizi girin">
                </div>

                <div class="form-options">
                    <div class="remember-me">
                        <input type="checkbox" id="remember" name="remember" value="1">
                        <label for="remember">Beni hatırla</label>
                    </div>
                    <a href="#" class="forgot-password" onclick="alert('Bu demo bir eğitim uygulamasıdır.'); return false;">
                        Şifremi unuttum?
                    </a>
                </div>

                <button type="submit" class="login-btn">Giriş Yap</button>
            </form>
        </div>
    </div>

    <div class="footer">
        PhotoShare Demo - Sadece eğitim amaçlıdır
    </div>
</body>
</html>
'''

THANKS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo Tamamlandı - PhotoShare</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
            padding: 20px;
        }

        .success-container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 15px;
            max-width: 600px;
        }

        .success-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }

        h1 {
            font-size: 28px;
            margin-bottom: 15px;
            font-weight: 300;
        }

        p {
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 15px;
            opacity: 0.9;
        }

        .info-box {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }

        .info-box h3 {
            margin-bottom: 10px;
            color: #fff;
        }

        .info-box ul {
            list-style-type: none;
            padding-left: 0;
        }

        .info-box li {
            margin-bottom: 5px;
            padding-left: 20px;
            position: relative;
        }

        .info-box li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
        }

        .back-btn {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: rgba(255,255,255,0.2);
            color: white;
            text-decoration: none;
            border-radius: 25px;
            transition: background-color 0.3s;
        }

        .back-btn:hover {
            background: rgba(255,255,255,0.3);
        }
    </style>
</head>
<body>
    <div class="success-container">
        <div class="success-icon">✅</div>
        <h1>Eğitim Demo Başarılı</h1>
        <p>Form verileriniz başarıyla kaydedildi (dummy veri).</p>

        <div class="info-box">
            <h3>Kaydedilen Bilgiler:</h3>
            <ul>
                <li>Zaman damgası (UTC)</li>
                <li>Client IP adresi</li>
                <li>Tarayıcı bilgileri (User-Agent)</li>
                <li>Referrer bilgisi</li>
                <li>Dil tercihleri</li>
                <li>HTTP header'ları</li>
                <li>Form verileri (kullanıcı adı/şifre)</li>
                <li>Uzak port bilgisi</li>
            </ul>
        </div>

        <p><strong>Not:</strong> Bu veriler sadece eğitim amaçlıdır ve demo_logs.txt dosyasına kaydedilmiştir.</p>
        <p><strong>Güvenlik:</strong> Gerçek uygulamalarda asla kullanıcı şifrelerini düz metin olarak kaydetmeyin!</p>

        <a href="{{ url_for('login') }}" class="back-btn">Tekrar Dene</a>
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    """Ana sayfa - login'e yönlendir"""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login formu göster veya form verilerini işle"""
    if request.method == 'GET':
        # Login formunu göster
        return render_template_string(LOGIN_TEMPLATE)

    elif request.method == 'POST':
        # Rate limiting kontrolü
        client_ip = get_client_ip()
        if not check_rate_limit(client_ip):
            error_message = "Çok fazla deneme yaptınız. Lütfen bir dakika bekleyin."
            return render_template_string(LOGIN_TEMPLATE, error_message=error_message), 429

        # Form verilerini al
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == '1'

        # Basit doğrulama
        if not username or len(username) < 3 or len(username) > 32:
            error_message = "Kullanıcı adı 3-32 karakter arasında olmalıdır."
            return render_template_string(LOGIN_TEMPLATE, error_message=error_message)

        if not password or len(password) < 3 or len(password) > 128:
            error_message = "Şifre 3-128 karakter arasında olmalıdır."
            return render_template_string(LOGIN_TEMPLATE, error_message=error_message)

        # Form verilerini hazırla ve logla
        form_data = {
            'username': username,
            'password': password,  # Gerçek uygulamalarda asla düz metin kaydetmeyin!
            'remember_me': remember
        }

        try:
            log_request_data(form_data)
        except Exception as e:
            print(f"Loglama hatası: {e}")

        # Teşekkür sayfasına yönlendir
        return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    """Başarılı giriş sonrası teşekkür sayfası"""
    return render_template_string(THANKS_TEMPLATE)


@app.errorhandler(404)
def not_found(error):
    """404 hatası için basit sayfa"""
    return "<h1>404 - Sayfa Bulunamadı</h1><p>Bu bir eğitim demosudur.</p>", 404


@app.errorhandler(429)
def rate_limited(error):
    """429 Rate Limit hatası"""
    return "<h1>429 - Çok Fazla İstek</h1><p>Lütfen bir dakika bekleyin.</p>", 429


if __name__ == '__main__':
    print("=" * 60)
    print("🎓 GÜVENLI MOCK FOTOĞRAF PAYLAŞIM UYGULAMASI - EĞİTİM DEMO")
    print("=" * 60)
    print("⚠️  Bu uygulama sadece eğitim ve laboratuvar amaçlıdır!")
    print("⚠️  Gerçek hesap bilgilerini girmeyin!")
    print("📁 Log dosyası: demo_logs.txt")
    print("🌐 Uygulama çalışıyor: http://127.0.0.1:5000")
    print("=" * 60)

    # Log dosyası için izinleri ayarla
    if not os.path.exists('demo_logs.txt'):
        with open('demo_logs.txt', 'w') as f:
            f.write("# PhotoShare Demo Log File - Education Purpose Only\n")
        try:
            os.chmod('demo_logs.txt', 0o600)
        except:
            pass

    # Uygulamayı çalıştır
    app.run(debug=True, host='127.0.0.1', port=5000)
