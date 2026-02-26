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

# Загрузка данных для конкретного пользователя
def load_user_data(user_id):
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():  # Проверяем, не пустой ли файл
                    all_data = json.loads(content)
                    return all_data.get(str(user_id), {})
                else:
                    return {}
        return {}
    except json.JSONDecodeError:
        # Если файл поврежден, создаем новый
        return {}
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return {}

# Сохранение данных для конкретного пользователя
def save_user_data(user_id, user_data):
    try:
        # Загружаем все данные
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    all_data = json.loads(content)
                else:
                    all_data = {}
        else:
            all_data = {}
        
        # Обновляем данные для пользователя
        all_data[str(user_id)] = user_data
        
        # Сохраняем все данные
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        return False

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
        f"👋 Привет, {user_name}!\n\n"
        "📝 *У каждого пользователя свой личный список ДЗ*\n\n"
        "Что я умею:\n"
        "• 📝 Добавлять домашние задания\n"
        "• 📋 Показывать ваш список\n"
        "• 🗑️ Очищать ваши задания\n"
        "• ❓ Помощь\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# Команда помощь
@router.message(lambda message: message.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "📚 *Как пользоваться ботом:*\n\n"
        "1️⃣ Нажмите '📝 Добавить ДЗ'\n"
        "2️⃣ Введите дату (например: 26.02.2026)\n"
        "3️⃣ Вводите задания по одному\n"
        "4️⃣ Нажмите '⛔ Стоп' для сохранения\n\n"
        "📋 *Другие команды:*\n"
        "• /list - показать ваш список\n"
        "• /clear - очистить задания\n"
        "• /help - эта помощь\n\n"
        "🔒 *Важно:* Каждый видит только свои задания!"
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
        datetime.strptime(message.text, "%d.%m.%Y")
        
        # Сохраняем дату
        await state.update_data(date=message.text, homework_items=[])
        await state.set_state(HomeworkStates.waiting_for_homework)
        
        await message.answer(
            f"📝 Вводите задания для {message.text}\n\n"
            "Пример:\n"
            "Математика: стр. 45, №123\n"
            "УПС та ПНШВ: прочитать параграф 5\n\n"
            "Когда закончите, нажмите '⛔ Стоп'",
            reply_markup=get_stop_keyboard()
        )
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Введите дату в формате ДД.ММ.ГГГГ\n"
            "Например: 26.02.2026"
        )

# Обработка заданий
@router.message(HomeworkStates.waiting_for_homework)
async def process_homework(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        # Получаем данные
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
            
            # Сохраняем
            user_homework[date] = numbered_list.strip()
            
            if save_user_data(user_id, user_homework):
                await message.answer(
                    f"✅ Задания на {date} сохранены!",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer(
                    "❌ Ошибка при сохранении",
                    reply_markup=get_main_keyboard()
                )
        else:
            await message.answer(
                "❌ Нет заданий для сохранения",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        return
    
    # Добавляем задание
    data = await state.get_data()
    homework_items = data.get('homework_items', [])
    homework_items.append(message.text)
    await state.update_data(homework_items=homework_items)
    
    # Показываем текущий список
    current_list = ""
    for i, item in enumerate(homework_items, 1):
        current_list += f"{i}. {item}\n"
    
    await message.answer(
        f"✅ Добавлено!\n\nТекущий список:\n{current_list}",
        reply_markup=get_stop_keyboard()
    )

# Показать список пользователя
@router.message(lambda message: message.text == "📋 Показать весь список")
@router.message(Command("list"))
async def show_user_homework(message: types.Message):
    user_id = message.from_user.id
    user_homework = load_user_data(user_id)
    
    if not user_homework:
        await message.answer(
            "📭 Ваш список пуст",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формируем ответ
    response = "📚 *ВАШИ ЗАДАНИЯ*\n\n"
    
    # Сортируем по дате
    try:
        sorted_dates = sorted(user_homework.keys(), 
                            key=lambda x: datetime.strptime(x, "%d.%m.%Y"), 
                            reverse=True)
    except:
        sorted_dates = user_homework.keys()
    
    for date in sorted_dates:
        response += f"📅 *{date}:*\n{user_homework[date]}\n\n"
    
    # Отправляем
    await message.answer(response, parse_mode="Markdown", reply_markup=get_main_keyboard())

# Очистка
@router.message(lambda message: message.text == "🗑️ Очистить")
@router.message(Command("clear"))
async def clear_menu(message: types.Message, state: FSMContext):
    await message.answer(
        "🗑️ *Очистка ваших заданий:*\n\n"
        "🧹 Очистить всё - удалить все\n"
        "📅 Удалить по дате - удалить за конкретную дату",
        parse_mode="Markdown",
        reply_markup=get_clear_keyboard()
    )

@router.message(lambda message: message.text == "🧹 Очистить всё")
async def clear_all(message: types.Message):
    user_id = message.from_user.id
    if save_user_data(user_id, {}):
        await message.answer(
            "✅ Все ваши задания удалены!",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❌ Ошибка при удалении",
            reply_markup=get_main_keyboard()
        )

@router.message(lambda message: message.text == "📅 Удалить по дате")
async def clear_by_date_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_homework = load_user_data(user_id)
    
    if not user_homework:
        await message.answer(
            "📭 Ваш список пуст",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Показываем даты
    response = "📅 *Ваши даты:*\n\n"
    for date in user_homework.keys():
        response += f"• {date}\n"
    
    response += "\n✏️ Введите дату для удаления:"
    
    await state.set_state(HomeworkStates.waiting_for_delete_date)
    await message.answer(response, parse_mode="Markdown", reply_markup=get_stop_keyboard())

@router.message(HomeworkStates.waiting_for_delete_date)
async def process_delete_by_date(message: types.Message, state: FSMContext):
    if message.text == "⛔ Стоп":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_keyboard())
        return
    
    try:
        date_str = message.text
        datetime.strptime(date_str, "%d.%m.%Y")
        
        user_id = message.from_user.id
        user_homework = load_user_data(user_id)
        
        if date_str in user_homework:
            del user_homework[date_str]
            if save_user_data(user_id, user_homework):
                await message.answer(
                    f"✅ Задания за {date_str} удалены!",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer(
                    "❌ Ошибка при удалении",
                    reply_markup=get_main_keyboard()
                )
        else:
            await message.answer(
                f"❌ Даты {date_str} нет в вашем списке",
                reply_markup=get_main_keyboard()
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Используйте ДД.ММ.ГГГГ"
        )

# Кнопка стоп
@router.message(lambda message: message.text == "⛔ Стоп")
async def stop_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("⏹️ Действие отменено", reply_markup=get_main_keyboard())

# Все остальное
@router.message()
async def unknown_message(message: types.Message):
    await message.answer(
        "Используйте кнопки меню",
        reply_markup=get_main_keyboard()
    )