from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import json
import os

router = Router()

# Класс состояний
class HomeworkStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_homework = State()
    waiting_for_delete_date = State()

# Файл для хранения данных
DATA_FILE = 'homework_data.json'

# Загрузка данных с фильтром по пользователю
def load_user_data(user_id):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
            # Возвращаем данные только для конкретного пользователя
            return all_data.get(str(user_id), {})
    return {}

# Сохранение данных для конкретного пользователя
def save_user_data(user_id, user_data):
    # Загружаем все данные
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
    else:
        all_data = {}
    
    # Обновляем данные для пользователя
    all_data[str(user_id)] = user_data
    
    # Сохраняем все данные
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)

# Клавиатура с кнопкой стоп
def get_stop_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⛔ Стоп")]],
        resize_keyboard=True
    )
    return keyboard

# Основная клавиатура
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Добавить ДЗ")],
            [KeyboardButton(text="📋 Показать весь список")],
            [KeyboardButton(text="🗑️ Очистить"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Клавиатура для выбора типа очистки
def get_clear_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧹 Очистить всё")],
            [KeyboardButton(text="📅 Удалить по дате")],
            [KeyboardButton(text="⛔ Стоп")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Команда старт
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    await message.answer(
        f"👋 Привет, {user_name}! (ID: {user_id})\n\n"
        "Я бот для отслеживания домашних заданий.\n"
        "📝 *Важно:* У каждого пользователя свой личный список ДЗ!\n\n"
        "Что я умею:\n"
        "📝 Добавлять домашние задания по датам\n"
        "📋 Показывать ваш личный список заданий\n"
        "🗑️ Очищать ваши задания\n"
        "❓ Помощь по командам\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# Команда помощь
@router.message(lambda message: message.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📚 *Команды бота:*\n\n"
        "/start - Запустить бота\n"
        "/list - Показать ваш список ДЗ\n"
        "/clear - Очистить ваши задания\n"
        "/help - Показать это сообщение\n"
        "/myid - Показать ваш ID\n\n"
        "*Как пользоваться:*\n"
        "1️⃣ Нажмите '📝 Добавить ДЗ'\n"
        "2️⃣ Введите дату (например: 26.02.2026)\n"
        "3️⃣ Вводите задания по одному\n"
        "4️⃣ Когда закончите, нажмите '⛔ Стоп'\n\n"
        "*Важно:* У каждого пользователя свой личный список!"
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Показать свой ID
@router.message(lambda message: message.text == "/myid")
@router.message(Command("myid"))
async def show_my_id(message: types.Message):
    await message.answer(
        f"🆔 *Ваш ID:* `{message.from_user.id}`\n\n"
        "Этот ID используется для разделения данных между пользователями.",
        parse_mode="Markdown"
    )

# Начало добавления ДЗ
@router.message(lambda message: message.text == "📝 Добавить ДЗ")
async def add_homework_start(message: types.Message, state: FSMContext):
    await state.set_state(HomeworkStates.waiting_for_date)
    await message.answer(
        "📅 Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: 26.02.2026\n\n"
        "Или нажмите '⛔ Стоп' для отмены",
        reply_markup=get_stop_keyboard()
    )

# Обработка даты
@router.message(HomeworkStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_main_keyboard())
        return
    
    try:
        # Проверка формата даты
        date = datetime.strptime(message.text, "%d.%m.%Y").date()
        
        # Сохраняем дату в состояние и инициализируем список заданий
        await state.update_data(date=message.text, homework_items=[])
        await state.set_state(HomeworkStates.waiting_for_homework)
        
        await message.answer(
            f"📝 Вводите домашние задания для {message.text}\n\n"
            "Просто пишите предмет и задание, например:\n"
            "Математика: стр. 45, №123\n"
            "УПС та ПНШВ: прочитать параграф 5\n\n"
            "Когда закончите, нажмите '⛔ Стоп' для сохранения",
            reply_markup=get_stop_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 26.02.2026"
        )

# Обработка списка ДЗ
@router.message(HomeworkStates.waiting_for_homework)
async def process_homework(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        # Сохраняем данные
        data = await state.get_data()
        date = data.get('date')
        homework_items = data.get('homework_items', [])
        
        if homework_items:
            # Формируем нумерованный список
            numbered_list = ""
            for i, item in enumerate(homework_items, 1):
                numbered_list += f"{i}. {item}\n"
            
            # Загружаем данные пользователя
            user_id = message.from_user.id
            user_homework = load_user_data(user_id)
            
            # Сохраняем новое ДЗ
            user_homework[date] = numbered_list.strip()
            save_user_data(user_id, user_homework)
            
            await message.answer(
                f"✅ Домашнее задание на {date} сохранено в ваш личный список!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Нет данных для сохранения",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        return
    
    # Получаем текущие данные из состояния
    data = await state.get_data()
    homework_items = data.get('homework_items', [])
    
    # Добавляем новое задание
    homework_items.append(message.text)
    await state.update_data(homework_items=homework_items)
    
    # Показываем текущий список
    current_list = ""
    for i, item in enumerate(homework_items, 1):
        current_list += f"{i}. {item}\n"
    
    await message.answer(
        f"✅ Задание добавлено!\n\n"
        f"*Текущий список:*\n{current_list}\n"
        f"Продолжайте или нажмите '⛔ Стоп' для сохранения",
        parse_mode="Markdown",
        reply_markup=get_stop_keyboard()
    )

# Показать весь список
@router.message(lambda message: message.text == "📋 Показать весь список")
@router.message(Command("list"))
async def show_all_homework(message: types.Message):
    user_id = message.from_user.id
    user_homework = load_user_data(user_id)
    
    if not user_homework:
        await message.answer(
            "📭 Ваш список домашних заданий пуст",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формируем сообщение
    response = f"📚 *ВАШИ ДОМАШНИЕ ЗАДАНИЯ*\n\n"
    
    # Сортируем по дате
    sorted_dates = sorted(user_homework.keys(), 
                         key=lambda x: datetime.strptime(x, "%d.%m.%Y"), 
                         reverse=True)
    
    for date in sorted_dates:
        response += f"📅 *{date}:*\n"
        response += f"{user_homework[date]}\n\n"
    
    # Отправляем
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="Markdown")
    else:
        await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Очистка (аналогично обновить для работы с user_id)
@router.message(lambda message: message.text == "🗑️ Очистить")
@router.message(Command("clear"))
async def clear_menu(message: types.Message, state: FSMContext):
    await message.answer(
        "🗑️ *Выберите тип очистки ВАШИХ заданий:*\n\n"
        "• '🧹 Очистить всё' - удалит ВСЕ ваши задания\n"
        "• '📅 Удалить по дате' - удалит задания за конкретную дату",
        parse_mode="Markdown",
        reply_markup=get_clear_keyboard()
    )

@router.message(lambda message: message.text == "🧹 Очистить всё")
async def clear_all(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user_data(user_id, {})
    await message.answer(
        "✅ Все ваши домашние задания успешно удалены!",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "📅 Удалить по дате")
async def clear_by_date_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_homework = load_user_data(user_id)
    
    if not user_homework:
        await message.answer(
            "📭 Ваш список домашних заданий пуст. Нечего удалять.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем доступные даты
    response = "📅 *Ваши доступные даты:*\n\n"
    sorted_dates = sorted(user_homework.keys(), 
                         key=lambda x: datetime.strptime(x, "%d.%m.%Y"), 
                         reverse=True)
    
    for date in sorted_dates:
        response += f"• {date}\n"
    
    response += "\n✏️ Введите дату, которую хотите удалить:"
    
    await state.set_state(HomeworkStates.waiting_for_delete_date)
    await message.answer(response, parse_mode="Markdown", reply_markup=get_stop_keyboard())

@router.message(HomeworkStates.waiting_for_delete_date)
async def process_delete_by_date(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        await state.clear()
        await message.answer("❌ Удаление отменено", reply_markup=get_main_keyboard())
        return
    
    try:
        date_str = message.text
        datetime.strptime(date_str, "%d.%m.%Y")  # Проверка формата
        
        user_id = message.from_user.id
        user_homework = load_user_data(user_id)
        
        if date_str in user_homework:
            deleted_item = user_homework.pop(date_str)
            save_user_data(user_id, user_homework)
            
            await message.answer(
                f"✅ Задания за {date_str} удалены из вашего списка!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ Заданий за {date_str} не найдено в вашем списке",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате ДД.ММ.ГГГГ"
        )

# Обработка кнопки стоп
@router.message(lambda message: message.text == "⛔ Стоп")
async def stop_action(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer("⏹️ Действие отменено", reply_markup=get_main_keyboard())
    else:
        await message.answer("Нет активных действий", reply_markup=get_main_keyboard())

# Обработка неизвестных команд
@router.message()
async def unknown_message(message: types.Message):
    await message.answer(
        "Я не понимаю эту команду.\n"
        "Используйте /start или /help",
        reply_markup=get_main_keyboard()
    )