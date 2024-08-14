import aiogram
from aiogram import types, Router, F
from message import Message
from aiogram.fsm.context import FSMContext
from utils.database.database import database as db_manager
from utils.database.models import Review, User
from utils.forms import ReviewData
from utils.support_method import create_pagination_keyboard
from utils.kb import main_review, review_vision, cancel
from utils.custom_filter import IsUserAddOrder

router = Router()

review_name = "review"
review_left = review_name + "|left_"
review_right = review_name + "|right_"

@router.callback_query(F.data == "see_reviews")
async def see_reviews(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_review=1, message_id=callback_query.message.message_id, what_reviews="all")
    await display_review_page(callback_query, state)

@router.callback_query(F.data == "my_review")
async def my_review(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    await state.update_data(page_review=1, message_id=callback_query.message.message_id, what_reviews="my")
    await display_review_page(callback_query, state)

@router.callback_query(F.data.startswith(review_left) | F.data.startswith(review_right))
async def handle_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("page_review", 1)
    action, _ = callback_query.data.split("_")

    if action + "_" == review_left:
        current_page -= 1
    elif action + "_" == review_right:
        current_page += 1

    if current_page == 0:
        message_id = data.get("message_id")
        await callback_query.bot.edit_message_reply_markup(
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_review.as_markup()
            )
        await callback_query.message.answer(Message.END_LIST)
        await state.clear()
        return

    await state.update_data(page_review=current_page)
    await display_review_page(callback_query, state)

async def display_review_page(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("page_review", 1)
    message_id = data.get("message_id")
    what_reviews = data.get("what_reviews")

    async for session in db_manager.get_session():
        user_review = ""
        if what_reviews == "all":
            review, user_review  = await Review.get_reviews_paginated(session, page)
        else:
            review: Review = await Review.get_reviews_paginated(session, page, what_reviews=["my", callback_query.from_user.id])
        if review:
            date = review.review_date.date()
            if user_review == "":
                text = (
                    f"📅 *{date}*\n"
                    f"🏷 **{review.title}**\n"
                    f"📝 {review.review_text}\n"
                    f"⭐ Рейтинг: {int(review.rating) * '⭐'}\n"
                    f"🎯 Дата: {date}"
                )
            else:
                username = user_review.username if user_review.username else "Ананим"
                if review.vision_review is True:
                    text = (
                        f"📅 *{date}*\n"
                        f"🏷 **{review.title}**\n"
                        f"📝 {review.review_text}\n"
                        f"⭐ Рейтинг: {int(review.rating) * '⭐'}\n"
                        f"🎯 Дата: {date}\n"
                        f"👤 Оставил: {username}"
                    )
                else:
                    text = (
                        f"📅 *{date}*\n"
                        f"🏷 **{review.title}**\n"
                        f"📝 {review.review_text}\n"
                        f"⭐ Рейтинг: {int(review.rating) * '⭐'}\n"
                        f"🎯 Дата: {date}\n"
                        f"👤 Оставил: Ананим"
                    )
            if message_id:
                try:
                    await callback_query.bot.edit_message_text(
                        chat_id=callback_query.message.chat.id,
                        message_id=message_id,
                        text=text,
                        parse_mode="Markdown",
                        reply_markup=create_pagination_keyboard(page, review_left, review_right).as_markup()
                    )
                except aiogram.exceptions.TelegramBadRequest:
                    await callback_query.bot.edit_message_reply_markup(
                        chat_id=callback_query.message.chat.id,
                        message_id=message_id,
                        reply_markup=None
                    )
                    new_message = await callback_query.message.answer(text, reply_markup=create_pagination_keyboard(page, review_left, review_right).as_markup(), parse_mode="Markdown")
                    await state.update_data(message_id=new_message.message_id)
            else:
                new_message = await callback_query.message.answer(text, reply_markup=create_pagination_keyboard(page, review_left, review_right).as_markup(), parse_mode="Markdown")
                await state.update_data(message_id=new_message.message_id)
        else:
            if message_id:
                await callback_query.bot.edit_message_text(
                    text=Message.ACTION_DIST,
                    chat_id=callback_query.message.chat.id,
                    message_id=message_id,
                    reply_markup=main_review.as_markup()
                )
            await callback_query.message.answer(Message.END_REVIEW)
            await state.clear()
        await session.commit()

@router.callback_query(F.data == "add_review", IsUserAddOrder())
async def process_add_review(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.answer(Message.REVIEW_SET_TITLE, reply_markup=cancel.as_markup())
    await state.set_state(ReviewData.title)

@router.callback_query(F.data.startswith("review_stars_"))
async def process_add_review_rating(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await state.update_data(rating=int(callback_query.data.split("_")[-1]))
    await callback_query.message.answer(Message.REVIEW_SET_VISION, reply_markup=review_vision.as_markup())

@router.callback_query(F.data.startswith("review_vision_"))
async def process_add_review_vision(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    data = await state.get_data()
    title = data.get("title")
    description = data.get("description")
    rating = data.get("rating")
    vision = True if callback_query.data.split("_")[-1] == "yes" else False
    async for session in db_manager.get_session():
        user = await User.find_user_by_telegram_id(session, callback_query.from_user.id)
        await Review.add_review(session, user.id, title, description, rating, vision)
        await session.commit()
    
    await callback_query.message.answer(Message.THANKS_ADD_REVIEW, reply_markup=main_review.as_markup())
    await state.clear()

