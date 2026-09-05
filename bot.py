import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from database import (
    init_db, is_banned, add_ban, remove_ban, get_settings,
    set_setting, get_roles, set_role, add_log
)

TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

URL_RE = re.compile(r"(https?://\S+|www\.\S+|t\.me/\S+)", re.I)

async def tg_admin(update, user_id=None):
    if not update.effective_chat:
        return False
    user_id = user_id or update.effective_user.id
    try:
        m = await update.effective_chat.get_member(user_id)
        return m.status in ("administrator", "creator")
    except Exception:
        return False

async def privileged(update, user_id=None):
    user_id = user_id or update.effective_user.id
    if user_id == OWNER_ID:
        return True
    return await tg_admin(update, user_id)

def target_from_reply(update):
    msg = update.effective_message
    return msg.reply_to_message.from_user if msg and msg.reply_to_message else None

async def ban(update, context):
    if not await privileged(update):
        return
    target = target_from_reply(update)
    if not target:
        return await update.message.reply_text("❌ ใช้คำสั่งโดย Reply ข้อความของคนที่ต้องการแบน")
    if await privileged(update, target.id):
        return await update.message.reply_text("❌ ไม่สามารถแบนผู้ดูแลได้")
    try:
        await update.effective_chat.ban_member(target.id)
        add_ban(update.effective_chat.id, target.id, update.effective_user.id, "manual")
        add_log(update.effective_chat.id, update.effective_user.id, "BAN", target.id)
        await update.message.reply_text(f"🔨 แบนถาวรแล้ว: {target.full_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ แบนไม่สำเร็จ: {e}")

async def unban(update, context):
    if not await privileged(update):
        return
    target = target_from_reply(update)
    if not target:
        return await update.message.reply_text("❌ Reply ข้อความของผู้ใช้ที่ต้องการปลดแบน")
    try:
        await update.effective_chat.unban_member(target.id, only_if_banned=True)
        remove_ban(update.effective_chat.id, target.id)
        add_log(update.effective_chat.id, update.effective_user.id, "UNBAN", target.id)
        await update.message.reply_text(f"✅ ปลดแบนแล้ว: {target.full_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ ปลดแบนไม่สำเร็จ: {e}")

async def mute(update, context):
    if not await privileged(update):
        return
    target = target_from_reply(update)
    if not target:
        return await update.message.reply_text("❌ Reply ข้อความของผู้ใช้ที่ต้องการปิดพิมพ์")
    if await privileged(update, target.id):
        return await update.message.reply_text("❌ ไม่สามารถปิดพิมพ์ผู้ดูแลได้")
    try:
        await update.effective_chat.restrict_member(
            target.id, ChatPermissions(can_send_messages=False)
        )
        add_log(update.effective_chat.id, update.effective_user.id, "MUTE", target.id)
        await update.message.reply_text(f"🔇 ปิดพิมพ์แล้ว: {target.full_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ Mute ไม่สำเร็จ: {e}")

async def unmute(update, context):
    if not await privileged(update):
        return
    target = target_from_reply(update)
    if not target:
        return await update.message.reply_text("❌ Reply ข้อความของผู้ใช้ที่ต้องการเปิดพิมพ์")
    p = ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    try:
        await update.effective_chat.restrict_member(target.id, p)
        add_log(update.effective_chat.id, update.effective_user.id, "UNMUTE", target.id)
        await update.message.reply_text(f"🔊 เปิดพิมพ์แล้ว: {target.full_name}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute ไม่สำเร็จ: {e}")

async def role(update, context):
    if not await privileged(update):
        return
    target = target_from_reply(update)
    if not target or not context.args or context.args[0].lower() not in ("admin", "mod", "remove"):
        return await update.message.reply_text("ใช้: Reply แล้ว /role admin | /role mod | /role remove")
    r = context.args[0].lower()
    set_role(update.effective_chat.id, target.id, "" if r == "remove" else r)
    await update.message.reply_text(f"✅ ตั้งยศ {('สมาชิก' if r=='remove' else r.upper())} ให้ {target.full_name}")

async def panel(update, context):
    if not await privileged(update):
        return
    chat_id = update.effective_chat.id
    link, share = get_settings(chat_id)
    kb = [
        [InlineKeyboardButton(f"🔗 Anti-Link: {'ON' if link else 'OFF'}", callback_data="toggle_link")],
        [InlineKeyboardButton(f"📤 Anti-Share: {'ON' if share else 'OFF'}", callback_data="toggle_share")],
    ]
    await update.message.reply_text("🎛️ แผงควบคุม Moderation", reply_markup=InlineKeyboardMarkup(kb))

async def button(update, context):
    q = update.callback_query
    await q.answer()
    if not await privileged(update, q.from_user.id):
        return await q.answer("ไม่มีสิทธิ์", show_alert=True)
    chat_id = update.effective_chat.id
    link, share = get_settings(chat_id)
    if q.data == "toggle_link":
        set_setting(chat_id, "antilink", 0 if link else 1)
    elif q.data == "toggle_share":
        set_setting(chat_id, "antishare", 0 if share else 1)
    link, share = get_settings(chat_id)
    kb = [
        [InlineKeyboardButton(f"🔗 Anti-Link: {'ON' if link else 'OFF'}", callback_data="toggle_link")],
        [InlineKeyboardButton(f"📤 Anti-Share: {'ON' if share else 'OFF'}", callback_data="toggle_share")],
    ]
    await q.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))

async def start(update, context):
    await update.message.reply_text(
        "🤖 Moderation Bot พร้อมใช้งาน\n\n"
        "/panel - แผงควบคุม\n"
        "/ban - แบนถาวร (Reply)\n"
        "/unban - ปลดแบน (Reply)\n"
        "/mute - ปิดพิมพ์ (Reply)\n"
        "/unmute - เปิดพิมพ์ (Reply)\n"
        "/role admin|mod|remove - ตั้งยศบอท"
    )

async def moderation(update, context):
    msg = update.effective_message
    user = msg.from_user if msg else None
    if not msg or not user or not update.effective_chat:
        return
    if await privileged(update, user.id):
        return

    link, share = get_settings(update.effective_chat.id)

    # Forward/share detection: Telegram exposes forward_origin for forwarded messages.
    if share and getattr(msg, "forward_origin", None):
        try:
            await msg.delete()
            await update.effective_chat.ban_member(user.id)
            add_ban(update.effective_chat.id, user.id, 0, "auto-share")
            add_log(update.effective_chat.id, 0, "AUTO_BAN_SHARE", user.id)
        except Exception as e:
            print("auto-share:", e)
        return

    text = msg.text or msg.caption or ""
    if link and URL_RE.search(text):
        try:
            await msg.delete()
            await update.effective_chat.ban_member(user.id)
            add_ban(update.effective_chat.id, user.id, 0, "auto-link")
            add_log(update.effective_chat.id, 0, "AUTO_BAN_LINK", user.id)
        except Exception as e:
            print("auto-link:", e)

def main():
    init_db()
    if not TOKEN or TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit("ตั้ง BOT_TOKEN ก่อนรัน")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("role", role))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, moderation))
    print("BOT STARTED")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
