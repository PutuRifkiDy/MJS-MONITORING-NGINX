import telebot
import requests
import os
import psutil
import time
import threading
import re
import requests
import subprocess

API_URL = "http://ip-api.com/json/?fields=country"  # API untuk geolokasi berdasarkan IP pada access logs

CHAT_ID = "1061302127"  # Ganti sama chat id tele kalian
TOKEN = "8170415782:AAGSWU5EwE1cdXHJO6LBVIqvHU9TNMoIPJk" # Ganti sama token kalian
CPU_THRESHOLD = 10.0
RAM_THRESHOLD = 25.0
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
    status_cpu = False
    status_ram = False
    while True:
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        if cpu_usage > CPU_THRESHOLD and status_cpu == False:
            bot.send_message(CHAT_ID, f"⚠ Warning! CPU usage is high: {cpu_usage}%")
            status_cpu = True
        elif cpu_usage < CPU_THRESHOLD and status_cpu == True:
            bot.send_message(CHAT_ID, f"⚠ SAFE! CPU usage is normal: {cpu_usage}%")
            status_cpu = False
            

        if ram_usage > RAM_THRESHOLD and status_ram == False:
            bot.send_message(CHAT_ID, f"⚠ Warning! RAM usage is high: {ram_usage}%")
            status_ram = True
        elif ram_usage < RAM_THRESHOLD and status_ram == True:
            bot.send_message(CHAT_ID, f"⚠ SAFE! RAM usage is normal: {ram_usage}%")
            status_ram = False

        time.sleep(60)

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
/list_virtual_hosts - Menampilkan Virtual Host
/enable_vhost - Akftikan Virtual host
/disable_vhost - Menonaftikan Virtual host
/add_vhost - Menambahkan Virtual Host
/remove_vhost - Menghapuskan Virtual Host
/set_upload_limit - Memberi Upload Size Limit Server Web

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
                    if ip.startswith("192.168.") or ip.startswith("10.") or ip == "127.0.0.1":
                        country = "Private Network"
                    else:
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
                    f"🖥 User-Agent: {user_agent}\n"
                    f"🔢 Status: {status}, Size: {size} bytes\n"
                    f"---------------------------------"
                )

        if formatted_logs:
            bot.send_message(message.chat.id, '\n'.join(formatted_logs))
        else:
            bot.reply_to(message, "⚠ Tidak ada log akses dengan format yang sesuai.")
    except Exception as e:
        bot.reply_to(message, f'Error saat membaca log: {e}')

# view virtual host apa aja ada yang aktif
@bot.message_handler(commands=['list_virtual_hosts'])
def virtual_hosts(message):
    try:
        available_path = '/etc/nginx/sites-available/'
        enabled_path = '/etc/nginx/sites-enabled/'

        # Ambil daftar semua Virtual Hosts yang tersedia dan aktif
        available_sites = set(os.listdir(available_path))
        enabled_sites = set(os.listdir(enabled_path))

        # Buat daftar dengan status aktif atau tidak aktif
        status_list = []
        for site in available_sites:
            if site in enabled_sites:
                status_list.append(f"✅ {site} (Aktif)")
            else:
                status_list.append(f"❌ {site} (Tidak Aktif)")

        # Kirim daftar ke user
        if status_list:
            bot.reply_to(message, "📁 Daftar Virtual Hosts:\n" + '\n'.join(status_list))
        else:
            bot.reply_to(message, "📂 Tidak ada Virtual Hosts yang ditemukan.")
    except Exception as e:
        bot.reply_to(message, f"⚠ Error membaca Virtual Hosts: {e}")


# Enable Virtual Host
@bot.message_handler(commands=['enable_vhost'])
def enable_vhost(message):
    try:
        bot.reply_to(message, "Silakan masukkan nama Virtual Host yang ingin diaktifkan (misalnya: `app1`):")
        bot.register_next_step_handler(message, process_enable_vhost)  # Lanjut ke fungsi proses
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")

def process_enable_vhost(message):
    try:
        domain = message.text.strip()  # Ambil nama Virtual Host dari input user
        available_path = f"/etc/nginx/sites-available/{domain}"
        enabled_path = f"/etc/nginx/sites-enabled/{domain}"

        if not os.path.exists(enabled_path):  # Jika belum diaktifkan
            if os.path.exists(available_path):  # Pastikan file ada di sites-available
                os.symlink(available_path, enabled_path)  # Buat symlink
                os.system("sudo systemctl reload nginx")  # Reload Nginx
                bot.reply_to(message, f"✅ Virtual Host `{domain}` berhasil diaktifkan!")
            else:
                bot.reply_to(message, f"⚠ Konfigurasi Virtual Host `{domain}` tidak ditemukan di `/etc/nginx/sites-available/`.")
        else:
            bot.reply_to(message, f"⚠ Virtual Host `{domain}` sudah aktif.")
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")

# Disable Virtual Host
@bot.message_handler(commands=['disable_vhost'])
def disable_vhost(message):
    try:
        bot.reply_to(message, "Silakan masukkan nama Virtual Host yang ingin dinonaktifkan (misalnya: `app2`):")
        bot.register_next_step_handler(message, process_disable_vhost)  # Lanjut ke fungsi proses
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")

def process_disable_vhost(message):
    try:
        domain = message.text.strip()  # Ambil nama Virtual Host dari input user
        available_path = f"/etc/nginx/sites-available/{domain}"
        enabled_path = f"/etc/nginx/sites-enabled/{domain}"

        if os.path.exists(enabled_path):  # Jika symlink ada
            os.unlink(enabled_path)  # Hapus symlink
            os.system("sudo systemctl reload nginx")  # Reload Nginx
            bot.reply_to(message, f"✅ Virtual Host `{domain}` berhasil dinonaktifkan!")
        else:
            bot.reply_to(message, f"⚠ Virtual Host `{domain}` sudah tidak aktif.")
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")
 

# Menambahkan Virtual Host ke site-available
@bot.message_handler(commands=['add_vhost'])
def add_vhost(message):
    try:
        bot.reply_to(message, "Silakan masukkan subdomain yang ingin ditambahkan (contoh: `app1`):", parse_mode="Markdown")
        bot.register_next_step_handler(message, process_add_vhost)  # Lanjut ke proses penambahan
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")

def process_add_vhost(message):
    try:
        # Ambil subdomain dari input user
        domain = message.text.strip()
        if not domain.isalnum():
            bot.reply_to(message, "⚠ Subdomain hanya boleh mengandung huruf dan angka (tanpa spasi atau simbol).")
            return

        available_path = f"/etc/nginx/sites-available/{domain}"
        root_path = f"/var/www/{domain}"

        # Periksa apakah file Virtual Host sudah ada
        if os.path.exists(available_path):
            bot.reply_to(message, f"⚠ Virtual Host `{domain}` sudah ada.")
            return

        # Periksa apakah direktori root ada
        if not os.path.exists(root_path):
            os.makedirs(root_path, exist_ok=True)  # Buat direktori root jika belum ada
            with open(f"{root_path}/index.html", "w") as index_file:
                index_file.write(f"<h1>Welcome to {domain}.example.com</h1>")  # Buat file index default

        # Template konfigurasi Nginx untuk Virtual Host
        config_content = f"""
server {{
    listen 80;
    server_name {domain}.example.com;

    root {root_path};
    index index.html;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""
        # Tulis file konfigurasi ke sites-available
        with open(available_path, 'w') as config_file:
            config_file.write(config_content)

        bot.reply_to(message, f"✅ File konfigurasi untuk Virtual Host `{domain}` berhasil dibuat di `/etc/nginx/sites-available/`.")
        bot.reply_to(message, f"Apakah Anda ingin mengaktifkan Virtual Host `{domain}` sekarang? Gunakan perintah: `enable_vhost`.", parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan saat menambahkan Virtual Host: {e}")


# Hapus Virtual Host
@bot.message_handler(commands=['remove_vhost'])
def remove_vhost(message):
    try:
        bot.reply_to(message, "Silakan masukkan nama Virtual Host yang ingin dihapus (misalnya: `app1`):", parse_mode="Markdown")
        bot.register_next_step_handler(message, process_remove_vhost)  # Lanjutkan ke proses penghapusan
    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan: {e}")

def process_remove_vhost(message):
    try:
        # Ambil nama Virtual Host dari input user
        vhost_name = message.text.strip()
        if not vhost_name.isalnum():
            bot.reply_to(message, "⚠ Nama Virtual Host hanya boleh mengandung huruf dan angka.")
            return

        available_path = f"/etc/nginx/sites-available/{vhost_name}"
        enabled_path = f"/etc/nginx/sites-enabled/{vhost_name}"

        # Cek apakah file Virtual Host tersedia
        if not os.path.exists(available_path):
            bot.reply_to(message, f"⚠ File Virtual Host `{vhost_name}` tidak ditemukan di `/etc/nginx/sites-available/`.")
            return

        # Jika Virtual Host aktif, hapus symlink dari sites-enabled
        if os.path.exists(enabled_path):
            os.unlink(enabled_path)
            bot.reply_to(message, f"🔗 Virtual Host `{vhost_name}` dinonaktifkan (symlink dihapus).")

        # Hapus file konfigurasi di sites-available
        os.remove(available_path)
        bot.reply_to(message, f"✅ File konfigurasi Virtual Host `{vhost_name}` berhasil dihapus dari `/etc/nginx/sites-available/`.")

        # Reload Nginx untuk menerapkan perubahan
        result = os.system("sudo systemctl reload nginx")
        if result == 0:
            bot.reply_to(message, "🔄 Nginx berhasil direload untuk menerapkan perubahan.")
        else:
            bot.reply_to(message, "⚠ Gagal me-reload Nginx. Periksa konfigurasi Nginx secara manual.")

    except Exception as e:
        bot.reply_to(message, f"⚠ Terjadi kesalahan saat menghapus Virtual Host: {e}")

# Fungsi untuk mendapatkan daftar Virtual Host
def list_virtual_hosts():
    try:
        available_path = '/etc/nginx/sites-available/'
        vhosts = os.listdir(available_path)
        return vhosts if vhosts else None
    except Exception as e:
        return None

# Fungsi untuk mengubah batas ukuran upload
def set_upload_limit(size, config_path):
    try:
        with open(config_path, 'r') as file:
            lines = file.readlines()

        with open(config_path, 'w') as file:
            directive_updated = False
            for line in lines:
                if line.strip().startswith("client_max_body_size"):
                    file.write(f"    client_max_body_size {size};\n")
                    directive_updated = True
                else:
                    file.write(line)

            if not directive_updated:  # Jika tidak ada, tambahkan
                file.write(f"\n    client_max_body_size {size};\n")

        # Restart Nginx untuk menerapkan perubahan
        os.system("sudo systemctl restart nginx")
        return f"✅ Batas ukuran file upload diatur ke {size} pada {config_path}!"
    except Exception as e:
        return f"❌ Error: {e}"

# Handler Telegram untuk perintah /set_upload_limit
@bot.message_handler(commands=['set_upload_limit'])
def change_upload_limit(message):
    bot.reply_to(message, "Apakah Anda ingin mengatur batas upload secara global atau untuk Virtual Host tertentu? (Ketik: `global` atau `vhost`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, process_upload_choice)

# Proses input pilihan (global atau vhost)
def process_upload_choice(message):
    choice = message.text.strip().lower()
    if choice == "global":
        bot.reply_to(message, "Masukkan batas ukuran file upload (contoh: 10M untuk 10 MB):")
        bot.register_next_step_handler(message, process_global_upload_limit)
    elif choice == "vhost":
        vhosts = list_virtual_hosts()
        if vhosts:
            vhosts_list = "\n".join([f"- {vhost}" for vhost in vhosts])
            bot.reply_to(message, f"Virtual Host yang tersedia:\n{vhosts_list}\n\nKetik nama Virtual Host yang ingin diubah:")
            bot.register_next_step_handler(message, process_vhost_selection)
        else:
            bot.reply_to(message, "❌ Tidak ada Virtual Host yang ditemukan.")
    else:
        bot.reply_to(message, "⚠ Pilihan tidak valid. Ketik `global` atau `vhost`.")

# Proses input batas upload untuk global
def process_global_upload_limit(message):
    size = message.text.strip()
    if not re.match(r"^\d+[KMG]$", size):
        bot.reply_to(message, "⚠ Format tidak valid. Gunakan format seperti '10M', '5G', atau '512K'.")
        return

    config_path = "/etc/nginx/nginx.conf"
    result = set_upload_limit(size, config_path)
    bot.reply_to(message, result)

# Proses input nama Virtual Host
def process_vhost_selection(message):
    vhost_name = message.text.strip()
    config_path = f"/etc/nginx/sites-available/{vhost_name}"

    if not os.path.exists(config_path):
        bot.reply_to(message, f"⚠ Virtual Host `{vhost_name}` tidak ditemukan di `/etc/nginx/sites-available/`.")
        return

    bot.reply_to(message, f"Masukkan batas ukuran file upload untuk Virtual Host `{vhost_name}` (contoh: 10M):")
    bot.register_next_step_handler(message, lambda msg: process_vhost_upload_limit(msg, config_path))

# Proses input batas upload untuk Virtual Host tertentu
def process_vhost_upload_limit(message, config_path):
    size = message.text.strip()
    if not re.match(r"^\d+[KMG]$", size):
        bot.reply_to(message, "⚠ Format tidak valid. Gunakan format seperti '10M', '5G', atau '512K'.")
        return

    result = set_upload_limit(size, config_path)
    bot.reply_to(message, result)

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