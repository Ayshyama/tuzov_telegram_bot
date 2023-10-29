from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

products_cb = CallbackData('products', 'id', 'action')

ADMIN_IDS = {318488850}


def get_products_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Show all products', callback_data='get_all_products')],
        [InlineKeyboardButton('Add new product', callback_data='add_new_product')]
    ], resize_keyboard=True)

    return ikb


def get_edit_ikb(product_id: int) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Edit Product', callback_data=products_cb.new(product_id, 'edit'))],
        [InlineKeyboardButton('Delete Product', callback_data=products_cb.new(product_id, 'delete'))]
    ], resize_keyboard=True)

    return ikb


def get_start_kb(user_id: int) -> ReplyKeyboardMarkup:
    buttons = []

    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton('/products'), KeyboardButton('/users')])

    buttons.extend([
        [KeyboardButton('Безкоштовні Рамки')],
        [KeyboardButton('Преміум Рамки')]
    ])

    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return kb


def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)

    return kb


products_list_cb = CallbackData('prodlist', 'product_id')


def get_products_list_ikb(products: list) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup()
    for product in products:
        btn = InlineKeyboardButton(product[1], callback_data=products_list_cb.new(product_id=product[0]))
        ikb.add(btn)
    return ikb


users_cb = CallbackData('users', 'action')


def get_users_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Show All Users', callback_data=users_cb.new(action='show_all'))],
        [InlineKeyboardButton('Edit User by ID', callback_data=users_cb.new(action='edit'))]
    ], resize_keyboard=True)
    return ikb


def create_payment_button(payment_link):
    ikb = InlineKeyboardMarkup()
    ikb.add(InlineKeyboardButton(text="Придбати Преміум", url=payment_link))
    return ikb


def get_payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Я оплатив', callback_data='user_paid')]
    ])