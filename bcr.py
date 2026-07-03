import telebot
from telebot import types
import urllib.parse
import random
import string
import sqlite3
import requests
import threading
import time
import os
from flask import Flask
from datetime import datetime, timedelta

# =====================================================================
# 1. CẤU HÌNH HỆ THỐNG VÀ CYBER-SECURITY VIP
# =====================================================================
API_TOKEN = '8722833362:AAHJT2UDN4E0KDCxJdtVv6lvJKWDVIcsbzE'
ADMIN_ID = 7338417401

bot = telebot.TeleBot(API_TOKEN)

CHU_TAI_KHOAN = "NGUYEN CANH HOANG SON"
SO_TAI_KHOAN = "8885010104"
NGAN_HANG_MA = "MB"

def init_db():
    conn = sqlite3.connect('bcr_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            key_code TEXT PRIMARY KEY,
            duration_days INTEGER,
            is_used INTEGER DEFAULT 0,
            used_by INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            expire_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Bộ nhớ tạm kiểm soát trạng thái đa luồng bảo mật
user_transactions = {}
user_auto_tables = {}

DANH_SACH_NUT_BAN = [
    "🎰 Bàn 1", "🎰 Bàn 2", "🎰 Bàn 3", "🎰 Bàn 4", "🎰 Bàn 5",
    "🎰 Bàn C01", "🎰 Bàn C02", "🎰 Bàn C03", "🎰 Bàn C04", "🎰 Bàn C05"
]

def generate_random_code(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_vip_key():
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choice(chars) for _ in range(4))
    part2 = ''.join(random.choice(chars) for _ in range(4))
    return f"VIP-{part1}-{part2}"


# =====================================================================
# KHU VỰC ĐỊNH NGHĨA GIAO DIỆN BÀN PHÍM (REPLY KEYBOARD)
# =====================================================================

# Menu chính: Mua/Nhập Key lên trên, Chọn Bàn xuống dưới dùng icon 💻
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    hang_1 = [types.KeyboardButton("💳 Mua Key"), types.KeyboardButton("🔑 Nhập Key")]
    hang_2 = [types.KeyboardButton("💻 Chọn Bàn")]
    markup.row(*hang_1)
    markup.row(*hang_2)
    return markup

def tables_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    hang_1 = [types.KeyboardButton("🎰 Bàn 1"), types.KeyboardButton("🎰 Bàn 2"), types.KeyboardButton("🎰 Bàn 3")]
    hang_2 = [types.KeyboardButton("🎰 Bàn 4"), types.KeyboardButton("🎰 Bàn 5"), types.KeyboardButton("🎰 Bàn C01")]
    hang_3 = [types.KeyboardButton("🎰 Bàn C02"), types.KeyboardButton("🎰 Bàn C03"), types.KeyboardButton("🎰 Bàn C04")]
    
    # Gom Bàn C05 và Menu Chính vào chung 1 dòng duy nhất vuông vắn
    hang_4 = [types.KeyboardButton("🎰 Bàn C05"), types.KeyboardButton("🔙 Menu Chính")]
    
    markup.row(*hang_1)
    markup.row(*hang_2)
    markup.row(*hang_3)
    markup.row(*hang_4)
    return markup

def auto_running_keyboard(ten_ban_sach):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton(f"🔴 Tắt Auto Bàn {ten_ban_sach}"), types.KeyboardButton("🔙 Chọn Bàn Khác"))
    return markup

def price_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("⏱ Gói 1 Ngày - 30k"), types.KeyboardButton("⏱ Gói 3 Ngày - 55k"))
    markup.add(types.KeyboardButton("⏱ Gói 7 Ngày - 90k"), types.KeyboardButton("♾ Gói Vĩnh Viễn - 250k"))
    markup.add(types.KeyboardButton("🔙 Menu Chính"))
    return markup


# =====================================================================
# XỬ LÝ LỆNH /START VIP ĐẲNG CẤP CYBER
# =====================================================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    conn = sqlite3.connect('bcr_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT expire_time FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    status_text = "❌ *UNAUTHORIZED* (Vui lòng nhập mã kích hoạt)"
    if row and row[0]:
        if row[0] == "FOREVER":
            status_text = "👑 *PREMIUM LIFETIME ACCESS*"
        else:
            try:
                expire_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                if expire_date > datetime.now():
                    status_text = f"⏱ *VIP CODES ACTIVE* (Hạn: `{expire_date.strftime('%d/%m/%Y %H:%M:%S')}`)"
                else:
                    status_text = "❌ *EXPIRED ACCESS* (Vui lòng nạp thêm key)"
            except Exception:
                pass
    
    welcome_text = (
        "⚡ **CENTRAL PROTOCOL CONTROL CENTER v3.8** ⚡\n"
        "📡 *Hệ thống phân tích dữ liệu Realtime đã khởi động*\n"
        "◽◽◽────────────────◽◽◽\n"
        f"👤 **USER ID:** `{user_id}`\n"
        f"🛡 **SECURITY PRIVILEGE:** {status_text}\n"
        "◽◽◽────────────────◽◽◽\n"
        "💻 *Mã hóa kết nối thành công. Vui lòng chọn tác vụ điều khiển từ bảng Terminal bên dưới.*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())


# =====================================================================
# LOGIC ĐIỀU HƯỚNG VÀ XỬ LÝ SỰ KIỆN CLICK CHỮ
# =====================================================================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_menu_click(message):
    text = message.text
    user_id = message.from_user.id

    # 5.1. XỬ LÝ BẢO MẬT NẠP KEY VIP (Chặn khai thác, chống spam trạng thái)
    if user_id in user_transactions and user_transactions[user_id].get("step") == "ENTERING_KEY":
        input_key = text.strip()
        
        if input_key in ["💻 Chọn Bàn", "💳 Mua Key", "🔑 Nhập Key", "🔙 Menu Chính", "🔙 Chọn Bàn Khác"]:
            del user_transactions[user_id]
        else:
            conn = sqlite3.connect('bcr_database.db')
            cursor = conn.cursor()
            cursor.execute('SELECT duration_days, is_used FROM keys WHERE key_code = ?', (input_key,))
            key_data = cursor.fetchone()
            
            if not key_data:
                bot.reply_to(message, "❌ *Mã giải mã bản quyền (Key) không tồn tại trên Mainframe!*", parse_mode="Markdown")
                conn.close()
                return
                
            duration_days, is_used = key_data
            if is_used == 1:
                bot.reply_to(message, "❌ *Mã Key bản quyền này đã được đồng bộ bởi một Node khác!*", parse_mode="Markdown")
                conn.close()
                return
                
            cursor.execute('UPDATE keys SET is_used = 1, used_by = ? WHERE key_code = ?', (user_id, input_key))
            cursor.execute('SELECT expire_time FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            now = datetime.now()
            
            if duration_days == 99999:
                new_expire = "FOREVER"
                thong_bao = "🎉 **HỆ THỐNG KÍCH HOẠT THÀNH CÔNG!**\nTài khoản đã được nâng cấp quyền truy cập: **VIP VĨNH VIỄN**."
            else:
                if user_data and user_data[0] != "FOREVER":
                    try:
                        current_expire = datetime.strptime(user_data[0], "%Y-%m-%d %H:%M:%S")
                        base_time = current_expire if current_expire > now else now
                    except Exception:
                        base_time = now
                else:
                    base_time = now
                    
                calculated_expire = base_time + timedelta(days=duration_days)
                new_expire = calculated_expire.strftime("%Y-%m-%d %H:%M:%S")
                thong_bao = f"🎉 **GIA HẠN THÀNH CÔNG!**\nTài khoản của bạn đã được nạp thêm **{duration_days * 24} giờ**.\n⏱ Thời gian hết hạn mới: `{calculated_expire.strftime('%d/%m/%Y %H:%M:%S')}`"
                
            cursor.execute('INSERT OR REPLACE INTO users (user_id, expire_time) VALUES (?, ?)', (user_id, new_expire))
            conn.commit()
            conn.close()
            
            del user_transactions[user_id]
            bot.send_message(message.chat.id, thong_bao, parse_mode="Markdown", reply_markup=main_menu_keyboard())
            return

    # 5.2. ĐIỀU HƯỚNG DANH SÁCH BÀN CHƠI (KIỂM TRA CHẶT CHẼ NÚT 💻)
    if text == "💻 Chọn Bàn" or text == "🔙 Chọn Bàn Khác":
        if user_id in user_auto_tables:
            try: user_auto_tables[user_id]["active"] = False
            except Exception: pass
            del user_auto_tables[user_id]

        conn = sqlite3.connect('bcr_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT expire_time FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        has_access = False
        if row and row[0]:
            if row[0] == "FOREVER":
                has_access = True
            else:
                try:
                    if datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") > datetime.now():
                        has_access = True
                except Exception:
                    pass
                
        if not has_access:
            bot.reply_to(message, "⚠️ **ACCESS DENIED!**\nTài khoản chưa kích hoạt hoặc hết hạn VIP. Hãy dùng chức năng **🔑 Nhập Key** để cấp quyền bẻ khóa phòng.")
            return
            
        bot.send_message(message.chat.id, "🛰 **VUI LÒNG CHỌN NODE DỮ LIỆU BÀN BCR ĐỂ KẾT NỐI AI:**", reply_markup=tables_menu_keyboard())
        
    elif text == "🔑 Nhập Key":
        user_transactions[user_id] = {"step": "ENTERING_KEY"}
        bot.reply_to(message, "🔑 **Vui lòng nhập chuỗi khóa mã hóa VIP của bạn vào đây:**\n*(Format chuẩn: VIP-XXXX-XXXX)*", parse_mode="Markdown")
    elif text == "💳 Mua Key":
        bot.send_message(message.chat.id, "💳 **BẢNG GIÁ ĐĂNG KÝ MỞ CỔNG CHỨC NĂNG VIP:**", reply_markup=price_menu_keyboard())

    # 5.3. KÍCH HOẠT LUỒNG AUTO QUÉT DỮ LIỆU VỚI PHẢN HỒI LẬP TỨC CHO PHIÊN MỚI NHẤT
    elif text in DANH_SACH_NUT_BAN:
        import threading
        import time

        if user_id in user_auto_tables:
            try: user_auto_tables[user_id]["active"] = False
            except Exception: pass
            del user_auto_tables[user_id]
        
        ten_ban_sach = text.replace("🎰 ", "").replace("Bàn ", "").strip()
        
        user_auto_tables[user_id] = {"active": True, "ban": ten_ban_sach, "last_phien": None, "is_first_run": True}
        
        bot.send_message(
            message.chat.id, 
            f"📡 **[ESTABLISHING CONNECTION]**... Kết nối dòng chảy luồng Auto quét **Bàn {ten_ban_sach}** thành công!", 
            reply_markup=auto_running_keyboard(ten_ban_sach)
        )
        
        def auto_fetch_loop(uid, chat_id, t_ban):
            while uid in user_auto_tables and user_auto_tables[uid]["active"]:
                try:
                    response = requests.get("https://apibcrneww.onrender.com/dudoan/sexy/all", timeout=8)
                    if response.status_code == 200:
                        data_list = response.json().get("data", [])
                        table_data = next((item for item in data_list if str(item.get("ban")).strip().upper() == t_ban.upper()), None)
                                
                        if table_data:
                            current_phien = table_data.get("phien_hien_tai")
                            
                            # Nếu là lần chạy đầu tiên HOẶC phiên cược có sự thay đổi mới -> Phát tin nhắn ngay
                            if user_auto_tables[uid]["is_first_run"] or current_phien != user_auto_tables[uid]["last_phien"]:
                                user_auto_tables[uid]["last_phien"] = current_phien
                                user_auto_tables[uid]["is_first_run"] = False
                                
                                du_doan_goc = table_data.get("du_doan", "SKIP")
                                do_tin_cay = table_data.get("do_tin_cay", "0%")
                                ket_qua_chuoi = table_data.get("ket_qua", "")
                                ly_do_ai = table_data.get("ly_do", "Tín hiệu toán học hội tụ")
                                pattern_ai = table_data.get("pattern_hien_tai", "N/A")
                                
                                if du_doan_goc.upper() == "BANKER":
                                    du_doan_tv = "🔴 BANKER (NHÀ CÁI)"
                                    badge = "🚨 TARGET SHOT: CHỌN CỬA ĐỎ"
                                elif du_doan_goc.upper() == "PLAYER":
                                    du_doan_tv = "🔵 PLAYER (NHÀ CON)"
                                    badge = "🚨 TARGET SHOT: CHỌN CỬA XANH"
                                else:
                                    du_doan_tv = "🟡 SKIP (BỎ QUA PHIÊN NÀY)"
                                    badge = "⚠️ THẬN TRỌNG: TÍN HIỆU KHÔNG AN TOÀN"
                                    
                                thoi_gian = datetime.now().strftime("%H:%M:%S")
                                
                                ket_qua_dinh_dang = ket_qua_chuoi.strip()
                                tin_nhan = (
                                    f"🛸 ─── [ BCR PROMAX AI PREDICT ] ─── 🛸\n"
                                    f"📊 NODE KẾT NỐI: `BÀN {t_ban}` | 🌐 ROUND: #{current_phien}\n"
                                    f"🤖 ENGINE STATUS: `ONLINE (Promax AI v3)`\n"
                                    f"───────────────────────────\n"
                                    f"⚡ DỰ ĐOÁN: {du_doan_tv}\n"
                                    f"🎯 ĐỘ TIN CẬY: `{do_tin_cay}`\n"
                                    f"💡 PHÂN TÍCH: _{ly_do_ai}_\n"
                                    f"───────────────────────────\n"
                                    f"📋 DANH SÁCH LỊCH SỬ CẦU CHUỖI:\n"
                                    f"{ket_qua_dinh_dang}\n"
                                )
                                bot.send_message(chat_id, tin_nhan, parse_mode="Markdown", reply_markup=auto_running_keyboard(t_ban))
                except Exception: pass
                time.sleep(5)

        threading.Thread(target=auto_fetch_loop, args=(user_id, message.chat.id, ten_ban_sach), daemon=True).start()

    # 5.4. LỆNH TẮT CHẾ ĐỘ AUTO QUÉT BÀN
    elif text.startswith("🔴 Tắt Auto Bàn"):
        if user_id in user_auto_tables:
            try: user_auto_tables[user_id]["active"] = False
            except Exception: pass
            del user_auto_tables[user_id]
            
        bot.send_message(message.chat.id, "🔴 *Đã ngắt giao thức chạy ngầm. Tắt chế độ Auto thành công.*", parse_mode="Markdown", reply_markup=tables_menu_keyboard())

    # 5.5. QUAY LẠI MENU CHÍNH
    elif text == "🔙 Menu Chính":
        if user_id in user_transactions: del user_transactions[user_id]
        bot.send_message(message.chat.id, "🔙 *Đã quay trở lại Giao thức mạng điều khiển trung tâm.*", parse_mode="Markdown", reply_markup=main_menu_keyboard())

    # 5.6. GIAO DỊCH ĐĂNG KÝ GÓI MUA KEY
    elif text in ["⏱ Gói 1 Ngày - 30k", "⏱ Gói 3 Ngày - 55k", "⏱ Gói 7 Ngày - 90k", "♾ Gói Vĩnh Viễn - 250k"]:
        random_str = generate_random_code(6)
        noi_dung_ck = f"VIP-{random_str}"
        
        user_transactions[user_id] = {"step": "WAITING_PAYMENT", "goi": text, "ma_vip": noi_dung_ck}
        
        if text == "⏱ Gói 1 Ngày - 30k":
            so_tien, days = 30000, 1
        elif text == "⏱ Gói 3 Ngày - 55k":
            so_tien, days = 55000, 3
        elif text == "⏱ Gói 7 Ngày - 90k":
            so_tien, days = 90000, 7
        else:
            so_tien, days = 250000, 99999

        user_transactions[user_id]["days"] = days

        import urllib.parse

        link_qr = (
    "https://img.vietqr.io/image/"
    f"{NGAN_HANG_MA}-{SO_TAI_KHOAN}-compact2.png"
    f"?amount={so_tien}"
    f"&addInfo={urllib.parse.quote(noi_dung_ck)}"
    f"&accountName={urllib.parse.quote(CHU_TAI_KHOAN)}"
)

        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(
            types.InlineKeyboardButton(
                "✅ Đã Chuyển Khoản",
                callback_data=f"da_ck_{user_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Hủy Giao Dịch",
                callback_data=f"huy_ck_{user_id}"
            )
        )

        caption = (
            f"✅ Gói cước đã chọn: {text}\n\n"
            f"🏦 Ngân hàng: MB BANK\n"
            f"💳 Số tài khoản: `{SO_TAI_KHOAN}`\n"
            f"👤 Chủ tài khoản: {CHU_TAI_KHOAN}\n"
            f"💰 Số tiền: `{so_tien:,}đ`\n"
            f"📝 Nội dung chuyển khoản: `{noi_dung_ck}`"
        )

        try:
            bot.send_photo(
                message.chat.id,
                link_qr,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=inline_markup
            )
        except Exception as e:
            print(e)
            bot.send_message(
                message.chat.id,
                str(e)
            )
    else:
        if user_id in user_transactions and user_transactions[user_id].get("step") == "WAITING_BILL":
            bot.reply_to(
                message,
                "⚠️ Hệ thống đang chờ nhận ảnh chụp bill chuyển khoản!"
            )
        else:
            bot.reply_to(
                message,
                "⚠️ Lệnh điều khiển không hợp lệ. Vui lòng bấm các nút của bot."
            )
# =====================================================================
# 6. XỬ LÝ NHẬN VÀ KIỂM TRA ẢNH BILL GIAO DỊCH (LỚP AN TOÀN FILE)
# =====================================================================
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id

    if user_id in user_transactions and user_transactions[user_id].get("step") == "WAITING_BILL":
        trans = user_transactions[user_id]

        bot.send_message(
            message.chat.id,
            "⏳ Hóa đơn của bạn đã được gửi tới Admin. Vui lòng chờ duyệt..."
        )

        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton(
                "✅ Duyệt Cấp Key VIP",
                callback_data=f"admin_duyet_{user_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Từ Chối Hủy Đơn",
                callback_data=f"admin_huy_{user_id}"
            )
        )

        caption_admin = (
            "🔔 YÊU CẦU DUYỆT GIAO DỊCH\n\n"
            f"👤 User: `{user_id}`\n"
            f"📦 Gói: {trans['goi']}\n"
            f"📝 Nội dung CK: `{trans['ma_vip']}`"
        )

        try:
            bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=caption_admin,
                parse_mode="Markdown",
                reply_markup=admin_markup
            )
            user_transactions[user_id]["step"] = "WAITING_ADMIN"

        except Exception as e:
            print(e)
            bot.send_message(
                message.chat.id,
                f"❌ Không thể gửi bill tới Admin.\n{e}"
            )

    else:
        bot.reply_to(
            message,
            "⚠️ Hiện tại hệ thống không yêu cầu bạn gửi ảnh."
        )

# =====================================================================
# 7. XỬ LÝ CỔNG CALLBACK QUERY (KHÁCH & ADMIN KHÓA CHẶT CHẼ)
# =====================================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_buttons(call):
    data = call.data
    clicker_id = call.from_user.id

    if data.startswith("admin_") and clicker_id != ADMIN_ID:
        bot.answer_callback_query(call.id, text="🔒 Cảnh báo bảo mật FireWall: Bạn không có đặc quyền truy cập Node này!", show_alert=True)
        return

    if data.startswith("da_ck_"):
        user_id = int(data.split("_")[-1])
        if user_id in user_transactions and user_transactions[user_id]["step"] == "WAITING_PAYMENT":
            user_transactions[user_id]["step"] = "WAITING_BILL"
            msg = "📸 **XÁC MINH GIAO DỊCH BILL:**\nVui lòng gửi ảnh chụp màn hình Hóa đơn (Bill) chuyển khoản thành công trực tiếp vào cuộc trò chuyện này để đối soát."
            try:
                if call.message.text: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, parse_mode="Markdown")
                else: bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=msg, parse_mode="Markdown")
            except Exception: bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, text="⚠️ Yêu cầu giao dịch hiện tại không còn hiệu lực hoặc đã quá thời gian chờ.", show_alert=True)

    elif data.startswith("huy_ck_"):
        user_id = int(data.split("_")[-1])
        if user_id in user_transactions: del user_transactions[user_id]
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception: pass
        bot.send_message(call.message.chat.id, "❌ Giao dịch mua gói cước hiện tại đã bị hủy bỏ thành công.", reply_markup=main_menu_keyboard())

    elif data.startswith("admin_duyet_"):
        user_id = int(data.split("_")[-1])
        if user_id in user_transactions:
            trans = user_transactions[user_id]
            duration_days, goi_name = trans.get("days", 1), trans['goi']
            del user_transactions[user_id]
        else:
            duration_days, goi_name = 1, "Gói VIP Hệ Thống"

        new_key = generate_vip_key()
        conn = sqlite3.connect('bcr_database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO keys (key_code, duration_days, is_used) VALUES (?, ?, 0)', (new_key, duration_days))
        conn.commit()
        conn.close()

        try:
            bot.send_message(user_id, f"🎉 **ĐƠN ĐĂNG KÝ MUA GÓI VIP ĐÃ ĐƯỢC DUYỆT THÀNH CÔNG!**\n\n🔑 Khóa kích hoạt VIP của bạn là: `{new_key}` (Chạm một lần vào chuỗi để tự động sao chép)\n\n📌 *Hướng dẫn kích hoạt:* Hãy bấm chọn tính năng **🔑 Nhập Key** ở Menu chính của bot, dán mã này gửi lên để kích hoạt thời gian sử dụng hệ thống ngay lập tức.", parse_mode="Markdown")
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + f"\n\n🟢 **TRẠNG THÁI: ĐÃ PHÊ DUYỆT CẤP KEY VIP**\n🔑 Key đã tạo: `{new_key}`")
            bot.answer_callback_query(call.id, text="🟢 Đã duyệt giao dịch và gửi mã thành công!")
        except Exception:
            bot.answer_callback_query(call.id, text="⚠️ Không thể gửi tin nhắn cho khách hàng (Có thể do khách chặn bot).", show_alert=True)

    elif data.startswith("admin_huy_"):
        user_id = int(data.split("_")[-1])
        if user_id in user_transactions: del user_transactions[user_id]
        try:
            bot.send_message(user_id, "❌ **GIAO DỊCH KHÔNG HỢP LỆ (BỊ TỪ CHỐI):**\nHóa đơn giao dịch chuyển khoản đăng ký gói cước VIP của bạn đã bị Admin kiểm tra và từ chối phê duyệt. Vui lòng kiểm tra lại sao kê số dư tài khoản ngân hàng của bạn.")
            bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n🔴 **TRẠNG THÁI: GIAO DỊCH BỊ TỪ CHỐI DUYỆT HỦY BỎ**")
            bot.answer_callback_query(call.id, text="❌ Đã thực hiện từ chối đơn hàng thành công!")
        except Exception:
            bot.answer_callback_query(call.id, text="⚠️ Đơn hàng giao dịch này không khả dụng hoặc đã được xử lý từ trước.", show_alert=True)

app = Flask(__name__)

@app.route("/")
def home():
    return "BCR PROMAX AI BOT ONLINE"

def run_web():
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )

if __name__ == "__main__":
    print("--- BOT BCR PROMAX AI v3 CHẠY CHÍNH THỨC (BẢO MẬT CAO) ---")

    threading.Thread(target=run_web, daemon=True).start()

    bot.infinity_polling()
