import asyncio, os, datetime
from aiogram import Bot, Dispatcher, types, executor
from hunter_engine import ContractorHunterCore

API_TOKEN = 'ТВОЙ_ТОКЕН_ЗДЕСЬ'
ADMIN_IDS = [12345678]  # Твой ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("🦾 **Contractor Hunter v10.3**\nПришли домен или .txt файл.")

@dp.message_handler(content_types=['text', 'document'])
async def handle_scan(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return

    # Список для хранения ID сообщений, которые нужно удалить
    temp_messages = []
    
    targets = []
    if message.document:
        await message.document.download(destination_file="temp_list.txt")
        with open("temp_list.txt", "r") as f:
            targets = [l.strip() for l in f if l.strip()]
    else:
        targets = [message.text.strip()]

    # Основной статус-бар (его мы оставим до конца)
    status_msg = await message.answer("🚀 **Запуск комбайна...**")
    
    hunter = ContractorHunterCore()

    for idx, t in enumerate(targets):
        await status_msg.edit_text(f"📡 **Прогресс:** `[{idx+1}/{len(targets)}]` \n🔍 **Цель:** `{t}`", parse_mode="Markdown")
        
        res = hunter.scan_target(t)
        
        if res:
            log_text = (
                f"✅ <b>{res['domain']}</b>\n"
                f"└ CMS: <code>{res['cms']}</code> | Dev: <code>{res['contractor']}</code>"
            )
            # Отправляем лог и сохраняем его ID для удаления
            msg = await message.answer(log_text, parse_mode="HTML")
            temp_messages.append(msg.message_id)
        
        await asyncio.sleep(1) 

    # Генерация и отправка отчета
    report_path = hunter.generate_html()
    with open(report_path, 'rb') as file:
        await message.answer_document(file, caption=f"🏁 **Разведка завершена!**\nСайтов: {len(targets)}")

    # --- БЛОК ОЧИСТКИ ---
    await status_msg.answer("🧹 **Очистка временных логов...**")
    
    # Удаляем все промежуточные сообщения с результатами
    for msg_id in temp_messages:
        try:
            await bot.delete_message(message.chat.id, msg_id)
        except: pass
    
    # Удаляем само сообщение о запуске и сообщение об очистке
    try:
        await bot.delete_message(message.chat.id, status_msg.message_id)
    except: pass

    # Удаляем физические файлы
    if os.path.exists(report_path): os.remove(report_path)
    if os.path.exists("temp_list.txt"): os.remove("temp_list.txt")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
