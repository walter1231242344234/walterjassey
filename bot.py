import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Токен и ID из переменных окружения
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Логирование
logging.basicConfig(level=logging.INFO)

# FSM для вопросов
class Form(StatesGroup):
    name = State()
    contact = State()

# Инициализация
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Кнопка "Подать заявку"
apply_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("📩 Подать заявку", callback_data="apply"))

# Старт
@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    photo_url = "https://via.placeholder.com/600x400.png?text=Добро+пожаловать"
    await bot.send_photo(message.chat.id, photo_url,
        caption="👋 Привет! Я бот для подачи заявок.\nНажми на кнопку ниже, чтобы начать:",
        reply_markup=apply_btn)

# Нажал кнопку
@dp.callback_query_handler(lambda c: c.data == 'apply')
async def process_callback_apply(callback_query: types.CallbackQuery):
    # Проверка, не в процессе ли уже пользователь
    user_id = callback_query.from_user.id
    if await dp.current_state(user=user_id).get_state() is not None:
        await callback_query.answer("❌ Ты уже в процессе подачи заявки!")
        return

    await Form.name.set()
    await bot.send_message(callback_query.from_user.id, "📝 Как тебя зовут?")

# Получаем имя
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Form.next()
    await message.answer("📞 Оставь контакт (телеграм, телефон или email):")

# Получаем контакт и отправляем админу
@dp.message_handler(state=Form.contact)
async def process_contact(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data['name']
    contact = message.text

    text = f"📥 Новая заявка:\n\n👤 Имя: {name}\n📞 Контакт: {contact}\n🆔 @{message.from_user.username}"
    await bot.send_message(ADMIN_ID, text)

    await message.answer("✅ Заявка отправлена! Менеджер скоро с тобой свяжется.")
    await state.finish()

# Запуск бота
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
