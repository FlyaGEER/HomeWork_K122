from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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

# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    await message.answer(
        "👋 Привет! Я бот для отслеживания домашних заданий.\n\n"
        "Что я умею:\n"
        "📝 Добавлять домашние задания по датам (автоматическая нумерация)\n"
        "📋 Показывать весь список заданий\n"
        "🗑️ Очищать задания (все или по дате)\n"
        "❓ Помощь по командам\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )

# Команда помощь
@router.message(lambda message: message.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📚 *Команды бота:*\n\n"
        "/start - Запустить бота\n"
        "/list - Показать весь список ДЗ\n"
        "/clear - Очистить задания\n"
        "/help - Показать это сообщение\n\n"
        "*Как пользоваться:*\n"
        "1️⃣ Нажмите '📝 Добавить ДЗ'\n"
        "2️⃣ Введите дату (например: 26.02.2026)\n"
        "3️⃣ Вводите задания по одному. Нумерация проставится автоматически!\n"
        "   Просто пишите предмет и задание, например:\n"
        "   Математика: стр. 45, №123\n"
        "   УПС та ПНШВ: прочитать параграф 5\n"
        "4️⃣ После каждого задания нажимайте Enter\n"
        "5️⃣ Когда закончите, нажмите '⛔ Стоп' для сохранения\n\n"
        "*Очистка заданий:*\n"
        "• Нажмите '🗑️ Очистить' для выбора типа очистки\n"
        "• Можно удалить все задания сразу\n"
        "• Или удалить задания за конкретную дату"
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

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
            "📌 *Важно:* Нумерация проставится автоматически!\n\n"
            "Просто пишите предмет и задание, например:\n"
            "Математика: стр. 45, №123\n"
            "УПС та ПНШВ: прочитать параграф 5\n"
            "Физика: задачи 1-3\n\n"
            "После каждого задания нажимайте Enter\n"
            "Когда закончите, нажмите '⛔ Стоп' для сохранения",
            parse_mode="Markdown",
            reply_markup=get_stop_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 26.02.2026"
        )

# Обработка списка ДЗ с автоматической нумерацией
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
            
            # Загружаем существующие данные
            all_homework = load_data()
            
            # Сохраняем новое ДЗ
            all_homework[date] = numbered_list.strip()
            save_data(all_homework)
            
            # Показываем предварительный просмотр
            preview = f"📅 *{date}:*\n\n{numbered_list}"
            
            await message.answer(
                f"✅ Домашнее задание на {date} сохранено!\n\n"
                f"*Предварительный просмотр:*\n{preview}",
                parse_mode="Markdown",
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
    
    # Добавляем новое задание (без номера)
    homework_items.append(message.text)
    
    # Обновляем состояние
    await state.update_data(homework_items=homework_items)
    
    # Показываем текущий список с автоматической нумерацией
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
    all_homework = load_data()
    
    if not all_homework:
        await message.answer(
            "📭 Список домашних заданий пуст",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формируем сообщение со всем списком
    response = "📚 *ВСЕ ДОМАШНИЕ ЗАДАНИЯ*\n\n"
    
    # Сортируем по дате (от новых к старым)
    sorted_dates = sorted(all_homework.keys(), key=lambda x: datetime.strptime(x, "%d.%m.%Y"), reverse=True)
    
    for date in sorted_dates:
        response += f"📅 *{date}:*\n"
        response += f"{all_homework[date]}\n\n"
    
    # Разбиваем на несколько сообщений, если слишком длинное
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for i, part in enumerate(parts, 1):
            await message.answer(part, parse_mode="Markdown")
    else:
        await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Начало очистки
@router.message(lambda message: message.text == "🗑️ Очистить")
@router.message(Command("clear"))
async def clear_menu(message: types.Message, state: FSMContext):
    await message.answer(
        "🗑️ *Выберите тип очистки:*\n\n"
        "• '🧹 Очистить всё' - удалит ВСЕ домашние задания\n"
        "• '📅 Удалить по дате' - удалит задания за конкретную дату",
        parse_mode="Markdown",
        reply_markup=get_clear_keyboard()
    )

# Обработка выбора типа очистки
@router.message(lambda message: message.text == "🧹 Очистить всё")
async def clear_all(message: types.Message, state: FSMContext):
    # Сохраняем пустой словарь
    save_data({})
    await message.answer(
        "✅ Все домашние задания успешно удалены!",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "📅 Удалить по дате")
async def clear_by_date_start(message: types.Message, state: FSMContext):
    all_homework = load_data()
    
    if not all_homework:
        await message.answer(
            "📭 Список домашних заданий пуст. Нечего удалять.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем доступные даты
    response = "📅 *Доступные даты:*\n\n"
    sorted_dates = sorted(all_homework.keys(), key=lambda x: datetime.strptime(x, "%d.%m.%Y"), reverse=True)
    
    for date in sorted_dates:
        response += f"• {date}\n"
    
    response += "\n✏️ Введите дату, которую хотите удалить (в формате ДД.ММ.ГГГГ):"
    
    await state.set_state(HomeworkStates.waiting_for_delete_date)
    await message.answer(response, parse_mode="Markdown", reply_markup=get_stop_keyboard())

# Обработка удаления по дате
@router.message(HomeworkStates.waiting_for_delete_date)
async def process_delete_by_date(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        await state.clear()
        await message.answer("❌ Удаление отменено", reply_markup=get_main_keyboard())
        return
    
    try:
        # Проверка формата даты
        date_to_delete = datetime.strptime(message.text, "%d.%m.%Y").date()
        date_str = message.text
        
        # Загружаем данные
        all_homework = load_data()
        
        if date_str in all_homework:
            # Удаляем запись
            deleted_item = all_homework.pop(date_str)
            save_data(all_homework)
            
            await message.answer(
                f"✅ Задания за {date_str} успешно удалены!\n\n"
                f"*Удалено:*\n{deleted_item}",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                f"❌ Заданий за {date_str} не найдено",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 26.02.2026"
        )

# Обработка кнопки стоп в любом состоянии
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
        "Используйте /start или /help для списка команд",
        reply_markup=get_main_keyboard()
    )