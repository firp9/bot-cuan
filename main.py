import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# 1. KONFIGURASI UTAMA
TOKEN = "8407105351:AAHIkSrljkOdDomPJ_J5UdXq8KkjExsZo50"
ADMIN_ID = 8360556815  # ID Telegram kamu (june)
LINK_SHOPEE = "https://collshp.com/cuangratisnihbos"

# 2. SERVER PANCINGAN (AGAR RENDER TIDAK MATI)
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Cuan Shopee is Running!")

def run_health_server():
    # Render memberikan port secara otomatis
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckServer)
    server.serve_forever()

# 3. DATABASE (UNTUK MENCATAT USER)
def init_db():
    conn = sqlite3.connect('cuan_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            clicks INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# 4. LOGIKA TOMBOL /START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name
    
    # Simpan user ke database
    conn = sqlite3.connect('cuan_data.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    
    text = (
        f"👋 Halo **{first_name}**!\n\n"
        "Selamat datang di **Bot Reward Shopee**.\n"
        "Klik tombol di bawah ini untuk mengklaim promo, diskon, dan reward harian kamu!"
    )
    
    keyboard = [[InlineKeyboardButton("🎁 KLAIM REWARD SEKARANG", callback_data='klik_shopee')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# 5. LOGIKA SAAT TOMBOL DIKLIK
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    # Update jumlah klik di database
    conn = sqlite3.connect('cuan_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET clicks = clicks + 1 WHERE user_id = ?', (user.id,))
    conn.commit()
    conn.close()
    
    await query.answer("Mengarahkan ke halaman reward...")
    
    # Pesan berisi Link Shopee Affiliate
    await query.message.reply_text(
        "✅ **LINK BERHASIL DI-GENERATE!**\n\n"
        "Silahkan akses koleksi reward kamu di sini:\n"
        f"👉 [KLIK DI SINI KE SHOPEE]({LINK_SHOPEE})\n\n"
        "⚠️ *Pastikan selesaikan misi agar reward masuk!*",
        parse_mode='Markdown'
    )

    # Kirim NOTIFIKASI ke kamu (june)
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **NOTIF CUAN!**\nUser: @{user.username or 'NoUser'} ({user.id})\nBaru saja mengklik link Shopee kamu!"
        )
    except:
        pass

# 6. MENJALANKAN BOT
if __name__ == '__main__':
    init_db()
    
    # Jalankan server pancingan di background
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # Inisialisasi Aplikasi Bot
    app = Application.builder().token(TOKEN).build()
    
    # Tambahkan Handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot @CuanRewardbot Aktif...")
    app.run_polling()
