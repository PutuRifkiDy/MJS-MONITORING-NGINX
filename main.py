import telebot
import requests
import os
import psutil
import time
import threading
import re
import requests

API_URL = "http://ip-api.com/json/?fields=country"  # API untuk geolokasi berdasarkan IP pada access logs

CHAT_ID = "1061302127"  # Ganti sama chat id tele kalian
TOKEN = "8170415782:AAGSWU5EwE1cdXHJO6LBVIqvHU9TNMoIPJk" # Ganti sama token kalian
CPU_THRESHOLD = 10.0
RAM_THRESHOLD = 10.0
ROOT_OPTIONS = {
    "1": "/var/www/html/portfolio-tridarma",
    "2": "/var/www/html/mjs-grafik-server",
    "3": "/var/www/html/portfolio-devasya",
    "4": "/var/www/html/portfolio-candra",
    "5": "/var/www/html/portfolio-rifki",
}
bot = telebot.TeleBot(TOKEN)

# Fungsi Cek Status Nginx
def check_nginx_status():
    status = os.system("systemctl is-active --quiet nginx")
    return "✅ Nginx is running" if status == 0 else "❌ Nginx is stopped"

# Fungsi Monitoring Resource Nginx
def nginx_resources():
    nginx_processes = [p for p in psutil.process_iter(['name']) if 'nginx' in p.info['name']]
    if nginx_processes:
        total_memory = sum(p.memory_info().rss for p in nginx_processes) / (1024 * 1024)
        return f"📊 Nginx Memory Usage: {total_memory:.2f} MB"
    return "❌ Nginx is not running"

# Perintah /status
@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, check_nginx_status())

# Perintah /start_nginx
@bot.message_handler(commands=['start_nginx'])
def start_nginx(message):
    os.system("sudo systemctl start nginx")
    bot.reply_to(message, "✅ Nginx started successfully!")

# Perintah /stop_nginx
@bot.message_handler(commands=['stop_nginx'])
def stop_nginx(message):
    os.system("sudo systemctl stop nginx")
    bot.reply_to(message, "🛑 Nginx stopped successfully!")

# Perintah /restart_nginx
@bot.message_handler(commands=['restart_nginx'])
def restart_nginx(message):
    os.system("sudo systemctl restart nginx")
    bot.reply_to(message, "🔄 Nginx restarted successfully!")

# Perintah /nginx_logs
@bot.message_handler(commands=['nginx_logs'])
def nginx_logs(message):
    try:
        with open('/var/log/nginx/error.log', 'r') as log_file:
            logs = log_file.readlines()[-10:]  # Ambil 10 baris terakhir
        if logs:
            bot.send_message(message.chat.id, ''.join(logs))
        else:
            bot.send_message(message.chat.id, 'Tidak ada error.')
    except Exception as e:
        bot.send_message(message.chat.id, f'Error reading log file: {e}')

# Perintah /monitor
@bot.message_handler(commands=['monitor'])
def monitor(message):
    bot.reply_to(message, nginx_resources())

# Fungsi untuk mengganti direktif 'root' dalam file konfigurasi
def update_nginx_root(new_root, config_path="/etc/nginx/sites-available/default"):
    try:
        # Baca file konfigurasi
        with open(config_path, "r") as file:
            lines = file.readlines()

        # Cari baris yang mengandung 'root' dan ganti
        with open(config_path, "w") as file:
            for line in lines:
                if line.strip().startswith("root"):
                    file.write(f"    root {new_root};\n")
                else:
                    file.write(line)

        # Restart Nginx untuk menerapkan perubahan
        os.system("sudo systemctl restart nginx")
        return "Nginx root path updated and Nginx restarted successfully!"
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk memproses pilihan user
@bot.message_handler(func=lambda message: message.text.isdigit())
def handle_option_choice(message):
    choice = message.text.strip()
    if choice in ROOT_OPTIONS:
        new_root = ROOT_OPTIONS[choice]
        result = update_nginx_root(new_root)  # Update konfigurasi Nginx
        bot.reply_to(message, f"✅ {result}")
    else:
        bot.reply_to(message, "❌ Invalid choice! Please select a valid option (1-5).")

# Command utama untuk memulai perubahan root
@bot.message_handler(commands=['change_base'])
def change_base(message):
    option_change = """
Pilih direktori root yang akan digunakan:

1. Portfolio TriDarma
2. MJS Grafik Server
3. Portfolio Devasya
4. Portfolio Candra
5. Portfolio Rifki

Ketik angka pilihan (1-5) untuk melanjutkan.
"""
    bot.reply_to(message, option_change)

# Status awal kondisi (digunakan untuk menghindari spam pesan)
cpu_alert_sent = False
ram_alert_sent = False

def monitor_resources():
    while True:
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        if cpu_usage > CPU_THRESHOLD:
            bot.send_message(CHAT_ID, f"⚠ Warning! CPU usage is high: {cpu_usage}%")

        if ram_usage > RAM_THRESHOLD:
            bot.send_message(CHAT_ID, f"⚠ Warning! RAM usage is high: {ram_usage}%")

        time.sleep(10)

@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_message = (
        "🎉 Selamat datang di Nginx Monitoring Bot! 🎉\n\n"
        "🔍 Saya di sini untuk membantu Anda memantau kesehatan dan performa server Nginx Anda.\n"
        "🆘 Tekan /help kapan saja untuk melihat semua perintah yang tersedia.\n\n"
        "🚀 Mari kita mulai! Pantau server Anda dengan mudah dan efektif bersama saya!"
    )
    bot.send_message(message.chat.id, welcome_message)

def start_monitoring():
    monitoring_thread = threading.Thread(target=monitor_resources)
    monitoring_thread.daemon = True  # Thread akan otomatis berhenti ketika program utama berhenti
    monitoring_thread.start()

@bot.message_handler(commands=['help'])
def help_command(message):
    print("Command /help received")  # Debugging untuk memastikan fungsi dipanggil
    help_text = """
🤖 Nginx Management Bot Commands:

/status - Cek status Nginx (running/stopped)
/start_nginx - Menjalankan Nginx
/stop_nginx - Menghentikan Nginx
/restart_nginx - Restart Nginx
/monitor - Monitoring penggunaan resource Nginx
/help - Menampilkan informasi perintah bot
/nginx_logs - Menampilkan error pada server nginx
/uptime - Menampilkan uptime server
/response_time - Menampilkan response time server
/access_logs - Menampilkan 10 baris terakhir dari log akses Nginx

⚠ Pastikan bot memiliki izin sudo untuk kontrol Nginx.
"""
    try:
        bot.reply_to(message, help_text)
    except Exception as e:
        print(f"Error in /help command: {e}")
        bot.reply_to(message, "⚠ Terjadi kesalahan saat menampilkan /help.")

# Path ke file access log Nginx
ACCESS_LOG_PATH = '/var/log/nginx/access.log'

# Fungsi untuk mendapatkan Uptime Server
def get_uptime():
    # Menggunakan perintah uptime untuk mendapatkan waktu aktif server
    uptime = os.popen("uptime -p").read().strip()
    return f"🕒 Server Uptime: {uptime}"

# Fungsi untuk mengukur Response Time
def get_response_time():
    try:
        start_time = time.time()  # Waktu sebelum melakukan request

        # Mengirim permintaan HTTP ke server Nginx (misalnya localhost)
        response = requests.get("http://localhost")

        # Waktu setelah request selesai
        end_time = time.time()

        # Menghitung response time dalam milidetik
        response_time_ms = (end_time - start_time) * 1000  # Mengonversi ke milidetik

        # Memeriksa status kode HTTP dan menampilkan response time
        if response.status_code == 200:
            return f"⏱ Response Time: {response_time_ms:.2f} ms"
        else:
            return f"❌ Server Nginx tidak merespon dengan status OK. Status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return f"❌ Gagal mengukur response time: {e}"

# Fungsi untuk mengirimkan pesan ke Telegram
def send_message_to_telegram(message):
    bot.send_message(CHAT_ID, message)

@bot.message_handler(commands=['access_logs'])
def access_logs(message):
    try:
        with open(ACCESS_LOG_PATH, 'r') as log_file:
            logs = log_file.readlines()[-10:]  # Ambil 10 baris terakhir
        
        if not logs:
            bot.reply_to(message, "📂 Tidak ada log akses terbaru.")
            return

        formatted_logs = []
        for log in logs:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+) - - \[(.*?)\] "(.*?)" (\d+) (\d+) "(.*?)" "(.*?)"', log)
            if match:
                ip, timestamp, request, status, size, referer, user_agent = match.groups()

                # Dapatkan lokasi negara dari API geolokasi
                try:
                    response = requests.get(f"{API_URL}{ip}")
                    geo_data = response.json()
                    country = geo_data.get('country', 'Unknown')
                except Exception as e:
                    country = "Unknown"

                formatted_logs.append(
                    f"📍 IP: {ip} ({country})\n"
                    f"⏰ Time: {timestamp}\n"
                    f"📄 Request: {request}\n"
                    f"🔗 Referer: {referer}\n"
                    f"---------------------------------"
                )

        if formatted_logs:
            bot.send_message(message.chat.id, '\n'.join(formatted_logs))
        else:
            bot.reply_to(message, "⚠ Tidak ada log akses dengan format yang sesuai.")
    except Exception as e:
        bot.reply_to(message, f'Error saat membaca log: {e}')

# Perintah /uptime
@bot.message_handler(commands=['uptime'])
def uptime(message):
    bot.reply_to(message, get_uptime())

# Perintah /response_time
@bot.message_handler(commands=['response_time'])
def response_time(message):
    bot.reply_to(message, get_response_time())

def run_bot():
    thread = threading.Thread(target=monitor_resources)
    thread.daemon = True
    thread.start()

    bot.infinity_polling()
# Start bot
if __name__ == "__main__":
    print("Bot is running...")
    run_bot()