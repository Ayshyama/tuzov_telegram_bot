from aiogram import types, executor, Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

import sqlite_db
from keyboards import *
from aiogram.dispatcher.filters.state import State, StatesGroup


API_TOKEN = '6789479098:AAGDJRFWirWgpu24pi6C0RK_9Hr7f3G_oLM'

ADMIN_IDS = {318488850, 101343916}

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class ProductStatesGroup(StatesGroup):
    title = State()
    media = State()
    category = State()
    edit_title = State()


class UserEditStatesGroup(StatesGroup):
    user_id = State()
    is_subscribed = State()
    has_premium = State()


async def on_startup(_):
    await sqlite_db.db_connect()
    print('Bot started, connected to db')


async def show_all_products(callback: types.CallbackQuery, products: list) -> None:
    for product in products:
        await bot.send_animation(chat_id=callback.message.chat.id,
                                 animation=product[2],
                                 caption=f'<b>{product[1]}</b> id: {product[0]}',
                                 parse_mode='HTML',
                                 reply_markup=get_edit_ikb(product[0]))


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Check if user is already in the database
    if not sqlite_db.user_exists(user_id):
        sqlite_db.add_new_user(user_id, username, first_name, last_name)

    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id,
                               f"Юзер {message.from_user.first_name} (ID: {message.from_user.id}, Username: @{message.from_user.username}) щойно запустив бота!")

    await bot.send_message(chat_id=message.from_user.id,
                           text='HELLO WORLD!',
                           reply_markup=get_start_kb(user_id))


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if state is None:
        return

    await state.finish()
    await message.answer('Canceled',
                         reply_markup=get_start_kb(user_id))


@dp.message_handler(commands=['products'], user_id=ADMIN_IDS)
async def cmd_products(message: types.Message):
    await message.delete()
    await message.answer('Products menu',
                         reply_markup=get_products_ikb())


@dp.message_handler(commands=['products'])
async def cmd_products_non_admin(message: types.Message):
    await message.reply("You don't have permission to use this command.")


@dp.message_handler(commands=['users'], user_id=ADMIN_IDS)
async def cmd_users(message: types.Message):
    await message.delete()
    await message.answer('Users menu', reply_markup=get_users_ikb())


@dp.message_handler(commands=['users'])
async def cmd_users_non_admin(message: types.Message):
    await message.reply("You don't have permission to use this command.")


@dp.callback_query_handler(users_cb.filter(action='show_all'))
async def cb_show_all_users(callback: types.CallbackQuery):
    users = sqlite_db.get_all_users()
    for user in users:
        await bot.send_message(callback.from_user.id, f"ID: {user[0]}\nUsername: {user[1]}\nFirst Name: {user[2]}\nLast Name: {user[3]}\nSubscribed: {user[4]}\nHas Premium: {user[5]}")
    await callback.answer()


@dp.callback_query_handler(users_cb.filter(action='edit'))
async def cb_edit_users(callback: types.CallbackQuery):
    await callback.message.answer('Please enter the user ID (9 digits) you want to edit (Example: 333448855):', reply_markup=get_cancel_kb())
    await UserEditStatesGroup.user_id.set()


@dp.message_handler(lambda message: len(message.text) == 9 and message.text.isdigit(), state=UserEditStatesGroup.user_id)
async def handle_user_id_input(message: types.Message, state: FSMContext):
    user_id = message.text
    await state.update_data(user_id=user_id)
    await message.answer('Enter the value for is_subscribed (0 or 1):')
    await UserEditStatesGroup.next()


@dp.message_handler(lambda message: not (len(message.text) == 9 and message.text.isdigit()), state=UserEditStatesGroup.user_id)
async def handle_invalid_user_id_input(message: types.Message):
    await message.answer('Invalid user ID. Please enter a 9 digit user ID:')


@dp.message_handler(lambda message: message.text in ["0", "1"], state=UserEditStatesGroup.is_subscribed)
async def handle_is_subscribed_input(message: types.Message, state: FSMContext):
    is_subscribed = int(message.text)
    await state.update_data(is_subscribed=is_subscribed)
    await message.answer('Enter the value for has_premium (0 or 1):')
    await UserEditStatesGroup.next()


@dp.message_handler(lambda message: message.text not in ["0", "1"], state=UserEditStatesGroup.is_subscribed)
async def handle_invalid_is_subscribed_input(message: types.Message):
    await message.answer('Invalid input. Please enter 0 or 1 for is_subscribed:')


@dp.message_handler(lambda message: message.text in ["0", "1"], state=UserEditStatesGroup.has_premium)
async def handle_has_premium_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    is_subscribed = data.get("is_subscribed")
    has_premium = int(message.text)

    sqlite_db.set_subscription_status(user_id, is_subscribed)
    sqlite_db.set_premium_status(user_id, has_premium)

    if has_premium == 1:
        await bot.send_message(user_id, "Оплата перевірена, ви отримали доступ до Преміум рамок!")

    await message.reply(f"User {user_id} details updated!",
                        reply_markup=get_start_kb(message.from_user.id))
    await state.finish()


@dp.message_handler(lambda message: message.text not in ["0", "1"], state=UserEditStatesGroup.has_premium)
async def handle_invalid_has_premium_input(message: types.Message):
    await message.answer('Invalid input. Please enter 0 or 1 for has_premium:')


@dp.callback_query_handler(text='get_all_products')
async def cb_get_all_products(callback: types.CallbackQuery):
    products = await sqlite_db.get_all_products()

    if not products:
        print('No products yet')
        await callback.message.delete()
        await callback.message.answer('No products yet')
        return await callback.answer()

    await callback.message.delete()
    await show_all_products(callback, products)
    await callback.answer()


@dp.callback_query_handler(text='add_new_product')
async def cb_add_new_product(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    await callback.message.answer('Send me title of product',
                                  reply_markup=get_cancel_kb())

    await ProductStatesGroup.title.set()


@dp.message_handler(state=ProductStatesGroup.title)
async def handle_title(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['title'] = message.text
    print(state)
    await  message.reply('Now send me photo of product')
    await ProductStatesGroup.next()


@dp.message_handler(content_types=['animation'], state=ProductStatesGroup.media)
async def handle_media(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['media'] = message.animation.file_id

    await message.reply("""What"s the category for this product? (Reply with "free" or "paid")""")
    await ProductStatesGroup.next()


@dp.message_handler(lambda message: message.text in ['free', 'paid'], state=ProductStatesGroup.category)
async def handle_category(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    print("Before setting category:", data)  # Debug
    data['category'] = message.text

    # Save product to the database
    product_id = await sqlite_db.create_new_product(data)
    print(f"Product with ID {product_id} added to the database.")  # Debug

    await state.set_data(data)
    await message.reply(f"Product '{data['title']}' with ID {product_id} added to the database in '{data['category']}' category.",
                        reply_markup=get_start_kb(message.from_user.id))
    await state.finish()


@dp.message_handler(lambda message: message.text not in ['free', 'paid'], state=ProductStatesGroup.category)
async def handle_invalid_category(message: types.Message) -> None:
    await message.reply('Invalid category. Please reply with "free" or "paid".')


@dp.message_handler(lambda message: not message.animation, state=ProductStatesGroup.media)
async def check_photo(message: types.Message) -> None:
    await message.reply("It's not a GIF, send me a GIF")


@dp.callback_query_handler(products_cb.filter(action='delete'))
async def cb_delete_product(callback: types.CallbackQuery, callback_data: dict):
    await sqlite_db.delete_product(callback_data['id'])
    await callback.message.delete()
    await callback.message.answer('Product deleted successfully')
    await callback.answer()


@dp.callback_query_handler(products_cb.filter(action='edit'))
async def cb_edit_product(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await callback.message.answer('Send me new title',
                                  reply_markup=get_cancel_kb())
    await ProductStatesGroup.edit_title.set()

    async with state.proxy() as data:
        data['product_id'] = callback_data['id']

    await callback.answer()


@dp.message_handler(state=ProductStatesGroup.edit_title)
async def handle_edit_title(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        await sqlite_db.edit_product(data['product_id'], message.text)

    await message.reply('Product edited successfully',
                        reply_markup=get_start_kb(message.from_user.id))
    await state.finish()


@dp.message_handler(lambda message: message.text == 'Безкоштовні Рамки')
async def handle_free_products(message: types.Message):
    user_id = message.from_user.id
    is_subscribed, _ = sqlite_db.get_user_status(user_id)

    if not is_subscribed:
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton('Subscribed', callback_data='user_subscribed')]
        ])

        await bot.send_message(user_id,
                               "Підпишись на наші соціальні мережи:\n\n[HOKO: Instagram](https://instagram.com/hokoarthoko?igshid=OGQ5ZDc2ODk2ZA==)"
                               "\n[HOKO: YouTube](https://www.youtube.com/@HOKO-HOKO)"
                               "\n[Tuzov Gallery: Instagram](https://www.instagram.com/tuzovgallery?igshid=OGQ5ZDc2ODk2ZA%3D%3D)",
                               reply_markup=ikb, parse_mode='Markdown')
    else:
        # Display the free products to the user
        free_products = sqlite_db.get_products_by_category("free")
        ikb = get_products_list_ikb(free_products)
        await bot.send_message(user_id, "Оберіть рамку:", reply_markup=ikb)


@dp.callback_query_handler(products_list_cb.filter())
async def send_product_details(callback: types.CallbackQuery, callback_data: dict):
    product_id = callback_data['product_id']
    product = sqlite_db.get_product_by_id(product_id)
    if product:
        await bot.send_animation(chat_id=callback.from_user.id,
                                 animation=product[2],
                                 caption=f"<b>{product[1]}</b>",
                                 parse_mode='HTML')
    await callback.answer()


@dp.callback_query_handler(text='user_subscribed')
async def user_subscribed(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    sqlite_db.set_user_subscribed(user_id)

    await callback.answer("Дякуємо за підписку!")
    await bot.send_message(user_id, "Дякуємо за підписку! Тепер у вас є доступ до безкоштовних рамок")


@dp.message_handler(lambda message: message.text == 'Преміум Рамки')
async def handle_paid_products(message: types.Message):
    user_id = message.from_user.id
    _, has_premium = sqlite_db.get_user_status(user_id)

    if not has_premium:
        # Send an offer message for premium
        await bot.send_message(user_id,
                               "Щоб отримати доступ до преміум оплатіть 50 грн на карту 1234 5678 9012 3456. Після оплати натисніть кнопку 'Я оплатив'",
                               reply_markup=get_payment_keyboard())
    else:
        paid_products = sqlite_db.get_products_by_category("paid")
        ikb = get_products_list_ikb(paid_products)
        await bot.send_message(user_id, "Оберіть преміум рамку:", reply_markup=ikb)


@dp.callback_query_handler(text='user_paid')
async def user_paid(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_info = callback.from_user

    await bot.delete_message(chat_id=user_id, message_id=callback.message.message_id)

    for admin_id in ADMIN_IDS:
        await bot.send_message(admin_id,
                               f"Користувач {user_info.first_name} (ID: {user_id}, Username: @{user_info.username}) нажав кнопку 'Я оплатив'!")

    await bot.send_message(user_id, "Дякуємо! Ваша оплата буде перевірена найближчим часом. Ви отримаєте повідомлення про активацію преміум доступу.")


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
