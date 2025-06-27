
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.markdown import hbold
from fpdf import FPDF
import logging
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN, default=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    goal = State()
    done = State()

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Я помогу рассчитать твою норму КБЖУ. Выбери цель:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Похудение")],
                [KeyboardButton(text="Поддержание")],
                [KeyboardButton(text="Набор массы")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(Form.goal)

@dp.message(Form.goal, F.text.in_(["Похудение", "Поддержание", "Набор массы"]))
async def process_goal(message: Message, state: FSMContext):
    goal = message.text
    # Демоданные (обычно рассчитываются по формулам и анкетным данным)
    result = {
        "Похудение": {"calories": 1424, "protein": 74, "fat": 49, "carbs": 172},
        "Поддержание": {"calories": 1624, "protein": 74, "fat": 49, "carbs": 222},
        "Набор массы": {"calories": 1974, "protein": 74, "fat": 49, "carbs": 309}
    }

    await state.update_data(result=result[goal])

    res = result[goal]
    text = (
        f"""<b>Твой результат:</b>
"
        f"""Калории: <b>{res['calories']} ккал</b>
"
        f"""Белки: {res['protein']} г
"
        f"""Жиры: {res['fat']} г
"
        f"""Углеводы: {res['carbs']} г"
    )
    await message.answer(text)

    await state.set_state(Form.done)

    # Отображаем финальные кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сохранить результаты в PDF", callback_data="save_pdf")],
        [InlineKeyboardButton(text="Подписаться на канал", url="https://t.me/doc_kalinichenko")],
        [InlineKeyboardButton(text="Начать заново", callback_data="restart")]
    ])
    await message.answer("Что хочешь сделать дальше?", reply_markup=keyboard)

@dp.callback_query(F.data == "save_pdf")
async def save_pdf(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    result = data.get("result")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="Твой результат КБЖУ", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Калории: {result['calories']} ккал", ln=True)
    pdf.cell(200, 10, txt=f"Белки: {result['protein']} г", ln=True)
    pdf.cell(200, 10, txt=f"Жиры: {result['fat']} г", ln=True)
    pdf.cell(200, 10, txt=f"Углеводы: {result['carbs']} г", ln=True)

    file_path = "result.pdf"
    pdf.output(file_path)

    await callback.message.answer_document(FSInputFile(file_path))
    os.remove(file_path)
    await callback.answer()

@dp.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message, state)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
