from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

from text_button import TextButton

# Главное окно
main_kb = InlineKeyboardBuilder()
main_kb.row(types.InlineKeyboardButton(text=TextButton.DISTREBUT, callback_data="distributor"))
main_kb.row(types.InlineKeyboardButton(text=TextButton.USER, callback_data="user"))

# Дистребьютер
generate_promo = InlineKeyboardBuilder()
generate_promo.add(types.InlineKeyboardButton(text=TextButton.PROMO, callback_data="gen_promo"))

main_dist = InlineKeyboardBuilder()
main_dist.add(types.InlineKeyboardButton(text=TextButton.STATISTIC_DIST, callback_data="statistic_dist"))
main_dist.add(types.InlineKeyboardButton(text=TextButton.BALANCE, callback_data="balance_dist"))
main_dist.add(types.InlineKeyboardButton(text=TextButton.MY_PROMO, callback_data="get_promo"))

output_money = InlineKeyboardBuilder()
output_money.add(types.InlineKeyboardButton(text=TextButton.OUTPUT_MANY, callback_data="output_money"),
                 types.InlineKeyboardButton(text=TextButton.CANCLE, callback_data="cancel"))

# Пользователь
no_promo = InlineKeyboardBuilder()
no_promo.add(types.InlineKeyboardButton(text=TextButton.PROMO_NO_INPUT_USER, callback_data="no_promo"))

main_user = InlineKeyboardBuilder()
main_user.row(types.InlineKeyboardButton(text=TextButton.HISTORY_USER, callback_data="history"),
              types.InlineKeyboardButton(text=TextButton.ORDER_USER, callback_data="order"),
              types.InlineKeyboardButton(text=TextButton.HELP, callback_data="help"))
main_user.row(types.InlineKeyboardButton(text=TextButton.ADD_REVIEW, callback_data="add_review"))
greet_kb = InlineKeyboardBuilder()
greet_kb.row(types.InlineKeyboardButton(text=TextButton.NO_FILE, callback_data="no_file"),
             types.InlineKeyboardButton(text=TextButton.HELP, callback_data="help"),
             types.InlineKeyboardButton(text=TextButton.CANCLE, callback_data="cancel")
            )

cancel = InlineKeyboardBuilder()
cancel.add(types.InlineKeyboardButton(text=TextButton.CANCLE, callback_data="cancel"))

# Админ
main_admin = InlineKeyboardBuilder()

main_admin.row(
    types.InlineKeyboardButton(text=TextButton.IN_POCESSING, callback_data="in_processing_order"),
    types.InlineKeyboardButton(text=TextButton.ACTIVE, callback_data="active_order")
)
main_admin.row(
    types.InlineKeyboardButton(text=TextButton.ACCESS, callback_data="access_order"),
    types.InlineKeyboardButton(text=TextButton.CANCLE, callback_data="cancel_order"),
    types.InlineKeyboardButton(text=TextButton.FAIL, callback_data="fail_order")
)
main_admin.row(
    types.InlineKeyboardButton(text=TextButton.ADD_ADMIN, callback_data="add_admin"),
    types.InlineKeyboardButton(text=TextButton.BAN_USER, callback_data="ban_user"),
)

# Отзывы
main_review = InlineKeyboardBuilder()
main_review.row(
    types.InlineKeyboardButton(text=TextButton.ADD_REVIEW, callback_data="add_review")
)
main_review.row(
    types.InlineKeyboardButton(text=TextButton.MY_REVIEWS, callback_data="my_review")
)
main_review.row(
    types.InlineKeyboardButton(text=TextButton.SEE_REVIEWS, callback_data="see_reviews")
)
main_rating_review = InlineKeyboardBuilder()
main_rating_review.row(
    types.InlineKeyboardButton(text=TextButton.RATING_ONE_STAR, callback_data="review_stars_1"),
    types.InlineKeyboardButton(text=TextButton.RATING_TWO_STARS, callback_data="review_stars_2"),
    types.InlineKeyboardButton(text=TextButton.RATING_THREE_STARS, callback_data="review_stars_3")
)
main_rating_review.row(
    types.InlineKeyboardButton(text=TextButton.RATING_FOUR_STARS, callback_data="review_stars_4"),
    types.InlineKeyboardButton(text=TextButton.RATING_FIVE_STARS, callback_data="review_stars_5")
)

review_vision = InlineKeyboardBuilder()
review_vision.row(
    types.InlineKeyboardButton(text=TextButton.VISION_REVIEW, callback_data="review_vision_yes"),
    types.InlineKeyboardButton(text=TextButton.NO_VISION_REVIEW, callback_data="review_vision_no")
)
review_vision.row(types.InlineKeyboardButton(text=TextButton.CANCLE, callback_data="cancel"))

