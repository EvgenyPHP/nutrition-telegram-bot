
import asyncio
import io
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from fpdf import FPDF

TOKEN = '8134057692:AAHMq4q3e2RqofrxKXp9Gqp0BRtePdzIh5c'
CHAT_ID = -1001996814306

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())


class NutritionForm(StatesGroup):
    gender = State()
    age = State()
    weight = State()
    activity1 = State()
    activity2 = State()
    goal = State()


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    print("🚀 /start запущен")
    await state.clear()
    await message.answer("👋 Привет! Давай подберём тебе питание.\n\nВыбери пол:", reply_markup=gender_keyboard())
    await state.set_state(NutritionForm.gender)


@dp.message(NutritionForm.gender)
async def process_gender(message: Message, state: FSMContext):
    print("▶️ Ввод пола")
    await state.update_data(gender=message.text)
    await message.answer("Укажи возраст:")
    await state.set_state(NutritionForm.age)


@dp.message(NutritionForm.age)
async def process_age(message: Message, state: FSMContext):
    print("▶️ Ввод возраста")
    await state.update_data(age=int(message.text))
    await message.answer("Укажи вес (в кг):")
    await state.set_state(NutritionForm.weight)


@dp.message(NutritionForm.weight)
async def process_weight(message: Message, state: FSMContext):
    print("▶️ Ввод веса")
    await state.update_data(weight=float(message.text))
    await message.answer("Выбери основную активность:", reply_markup=activity1_keyboard())
    await state.set_state(NutritionForm.activity1)


@dp.message(NutritionForm.activity1)
async def process_activity1(message: Message, state: FSMContext):
    print("▶️ Активность 1")
    await state.update_data(activity1=message.text)
    await message.answer("Выбери дополнительную активность:", reply_markup=activity2_keyboard())
    await state.set_state(NutritionForm.activity2)


@dp.message(NutritionForm.activity2)
async def process_activity2(message: Message, state: FSMContext):
    print("▶️ Активность 2")
    await state.update_data(activity2=message.text)
    await message.answer("Какова твоя цель?", reply_markup=goal_keyboard())
    await state.set_state(NutritionForm.goal)


@dp.message(NutritionForm.goal)
async def process_goal(message: Message, state: FSMContext):
    print("🎯 Обработка цели и финальный расчёт")
    await state.update_data(goal=message.text)
    data = await state.get_data()

    kfa = get_kfa(data["activity1"], data["activity2"])
    calories = calc_calories(data["gender"], data["age"], data["weight"], kfa, data["goal"])
    macros = calc_macros(data["weight"], calories, data["gender"])

    result_text = (
        f"<b>Твой результат:</b>\n"
        f"Калории: <b>{calories} ккал</b>\n"
        f"Белки: {macros['protein']} г\n"
        f"Жиры: {macros['fat']} г\n"
        f"Углеводы: {macros['carbs']} г"
    )

    await message.answer(result_text)

    username = message.from_user.username or "неизвестен"
    await bot.send_message(
        CHAT_ID,
        f"📥 <b>Новая анкета от @{username}</b>\n\n"
        f"Пол: {data['gender']}\n"
        f"Возраст: {data['age']}\n"
        f"Вес: {data['weight']} кг\n"
        f"Активность 1: {data['activity1']}\n"
        f"Активность 2: {data['activity2']}\n"
        f"Цель: {data['goal']}\n\n"
        f"<b>КБЖУ:</b>\n"
        f"{calories} ккал | Б: {macros['protein']} г | Ж: {macros['fat']} г | У: {macros['carbs']} г"
    )

    # Показ кнопок СНАЧАЛА
    await message.answer(
        "Что хочешь сделать дальше?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📄 Сохранить в PDF")],
                [types.KeyboardButton(text="📢 Подписаться на канал")],
                [types.KeyboardButton(text="/start")]
            ],
            resize_keyboard=True
        )
    )

    # Затем сохраняем PDF и очищаем состояние
    await state.update_data(pdf=f"Калории: {calories} ккал\nБелки: {macros['protein']} г\nЖиры: {macros['fat']} г\nУглеводы: {macros['carbs']} г")
    await state.clear()


@dp.message(F.text == "📄 Сохранить в PDF")
async def generate_pdf(message: Message, state: FSMContext):
    print("📄 PDF-запрос")
    data = await state.get_data()
    text = data.get("pdf", "Нет данных для PDF.")
    pdf_bytes = create_pdf(text)
    await message.answer_document(BufferedInputFile(pdf_bytes, filename="ration.pdf"))


@dp.message(F.text == "📢 Подписаться на канал")
async def handle_channel(message: Message):
    await message.answer("Подписывайся на канал 👉 https://t.me/doc_kalinichenko")


def create_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    for line in text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# --- Клавиатуры ---
def gender_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Женщина")], [types.KeyboardButton(text="Мужчина")]],
        resize_keyboard=True
    )


def activity1_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="В офисе")],
            [types.KeyboardButton(text="В офисе, но часто передвигаюсь")],
            [types.KeyboardButton(text="Весь день сижу дома")],
            [types.KeyboardButton(text="Весь день на ногах")],
            [types.KeyboardButton(text="Физический труд")]
        ],
        resize_keyboard=True
    )


def activity2_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Минимум или отсутствие")],
            [types.KeyboardButton(text="Небольшие 1-3 раза в неделю")],
            [types.KeyboardButton(text="3-5 раз в неделю")],
            [types.KeyboardButton(text="Ежедневные прогулки")],
            [types.KeyboardButton(text="Интенсивные каждый день")]
        ],
        resize_keyboard=True
    )


def goal_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Поддержание")],
            [types.KeyboardButton(text="Похудение")],
            [types.KeyboardButton(text="Набор массы")]
        ],
        resize_keyboard=True
    )


# --- Формулы ---
def get_kfa(activity1, activity2):
    scores = {
        "В офисе": 1,
        "В офисе, но часто передвигаюсь": 1.3,
        "Весь день сижу дома": 1,
        "Весь день на ногах": 1.5,
        "Физический труд": 1.5,
        "Минимум или отсутствие": 1,
        "Небольшие 1-3 раза в неделю": 1.3,
        "3-5 раз в неделю": 1.5,
        "Ежедневные прогулки": 1.3,
        "Интенсивные каждый день": 1.5
    }
    avg = (scores.get(activity1, 1) + scores.get(activity2, 1)) / 2
    if avg <= 1.1:
        return 1
    elif avg <= 1.4:
        return 1.3
    return 1.5


def calc_calories(gender, age, weight, kfa, goal):
    base = 0
    if gender.lower().startswith("ж"):
        if age <= 30:
            base = (0.062 * weight + 2.036) * 240
        elif age <= 60:
            base = (0.034 * weight + 3.538) * 240
        else:
            base = (0.038 * weight + 2.755) * 240
    else:
        if age <= 30:
            base = (0.063 * weight + 2.896) * 240
        elif age <= 60:
            base = (0.048 * weight + 3.653) * 240
        else:
            base = (0.049 * weight + 2.459) * 240

    result = base * kfa
    if goal.lower().startswith("пох"):
        result -= 200
    elif goal.lower().startswith("наб"):
        result += 350
    return round(result)


def calc_macros(weight, calories, gender):
    if gender.lower().startswith("ж"):
        protein = round(weight * 1.5)
        fat = round(weight * 1)
    else:
        protein = round(weight * 2)
        fat = round(weight * 1.1)

    protein_kcal = protein * 4
    fat_kcal = fat * 9
    carbs_kcal = calories - protein_kcal - fat_kcal
    carbs = round(carbs_kcal / 4)
    return {"protein": protein, "fat": fat, "carbs": carbs}


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
