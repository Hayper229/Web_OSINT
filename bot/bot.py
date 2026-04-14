import asyncio, os, datetime
from aiogram import Bot, Dispatcher, types, executor
from hunter_engine import ContractorHunterCore

API_TOKEN = 'ТВОЙ_ТОКЕН_ЗДЕСЬ'
ADMIN_IDS = [12345678, 87654321]  # ВПИШИ СВОЙ ID (узнай в @userinfobot)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("❌ Доступ запрещен. Это приватный OSINT-бот.")
    await message.answer("🦾 **Contractor Hunter v10.2**\n\nПришли мне **домен** или **.txt файл** со списком целей.")

@dp.message_handler(content_types=['text', 'document'])
async def handle_scan(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return

    targets = []
    if message.document:
        doc = await message.document.download(destination_file="temp_list.txt")
        with open("temp_list.txt", "r") as f:
            targets = [l.strip() for l in f if l.strip()]
    else:
        targets = [message.text.strip()]

    status = await message.answer("🚀 **Запуск комбайна...**")
    hunter = ContractorHunterCore()

    for idx, t in enumerate(targets):
        await status.edit_text(f"📡 **[{idx+1}/{len(targets)}] Сканирую:** `{t}`", parse_mode="Markdown")
        res = hunter.scan_target(t)
        
        if res:
            # Твой стиль логов (Зеленый/Желтый) в ТГ через HTML-теги
            log_text = (
                f"<b>ЦЕЛЬ:</b> {res['domain']}\n"
                f"<b>CMS:</b> <code>{res['cms']}</code>\n"
                f"<b>ПОДРЯДЧИК:</b> <code>{res['contractor']}</code>\n"
                f"<b>НАЙДЕНО:</b> 📧 {len([c for c in res['contacts'] if c[0]=='EMAIL'])} "
                f"📞 {len([c for c in res['contacts'] if c[0]=='PHONE'])}"
            )
            await message.answer(log_text, parse_mode="HTML")
        else:
            await message.answer(f"⚠️ `{t}` недоступен", parse_mode="Markdown")
        
        await asyncio.sleep(1) # Короткая пауза

    # Финал
    report_path = hunter.generate_html()
    with open(report_path, 'rb') as file:
        await message.answer_document(file, caption=f"🏁 **Разведка завершена!**\nСобрано почт: {hunter.stats['EMAIL']}\nТелефонов: {hunter.stats['PHONE']}")
    
    # Чистим мусор
    os.remove(report_path)
    if os.path.exists("temp_list.txt"): os.remove("temp_list.txt")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
