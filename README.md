# Telegram Moderation Bot

ระบบ:
- Ban ถาวร / Unban
- Mute / Unmute
- Anti-Link
- Anti-Forward/Share
- ยกเว้นผู้ดูแล Telegram
- Owner/Admin/Mod สำหรับคำสั่งบอท
- Panel ปุ่มเปิด/ปิด Anti-Link และ Anti-Share
- SQLite เก็บ ban, roles, settings และ logs

## ติดตั้ง

```bash
python -m pip install -r requirements.txt
```

ตั้ง environment:

```bash
export BOT_TOKEN="TOKEN จาก BotFather"
export OWNER_ID="Telegram user ID ของเจ้าของบอท"
python bot.py
```

Windows PowerShell:

```powershell
$env:BOT_TOKEN="TOKEN จาก BotFather"
$env:OWNER_ID="123456789"
python bot.py
```

## สำคัญ

เพิ่มบอทเข้า Group/Supergroup และให้เป็น Administrator พร้อมสิทธิ์:
- Delete messages
- Ban users
- Restrict members

ระบบ Auto-Share ใช้ `forward_origin` ของ Telegram Bot API จึงตรวจจับข้อความที่ Telegram ระบุว่าเป็น forwarded message ได้ แต่ไม่สามารถรู้ได้ทุกกรณีว่าข้อความที่ผู้ใช้คัดลอกเองมาจากกลุ่มอื่นหรือไม่

`/role` เป็นยศภายในบอท ไม่ได้เปลี่ยน Telegram administrator status:
- Reply แล้ว `/role admin`
- Reply แล้ว `/role mod`
- Reply แล้ว `/role remove`

หมายเหตุ: โค้ดชุดนี้ยกเว้นผู้ที่เป็น Telegram administrator/creator จาก Auto-ban โดยตรง ส่วนยศ `admin/mod` ในฐานข้อมูลใช้สำหรับขยายระบบต่อได้ หากต้องการให้ยศบอทเองได้รับสิทธิ์เต็มแบบเดียวกับ Telegram admin ให้เพิ่มการตรวจ roles ใน `privileged()`.
