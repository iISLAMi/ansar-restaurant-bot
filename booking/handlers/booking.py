from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, ReplyKeyboardRemove,
                           ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton,
                           CallbackQuery, LabeledPrice, PreCheckoutQuery,
                           InlineQuery, InlineQueryResultArticle, InputTextMessageContent)

from database.db import add_booking, get_user_bookings, delete_booking
from states.booking_state import BookingState
from utils.config import PAYMENT_TOKEN

router = Router()


@router.message(Command('book'))
async def cmd_book(message: Message, state: FSMContext):
    await message.answer('Введите дату для бронирования.\n'
                         'Например: 22.06\n')
    await state.set_state(BookingState.waiting_for_date)


@router.message(Command('mybookings'))
async def cmd_mybookings(message: Message):
    user_id = message.from_user.id if message.from_user else 0
    bookings = get_user_bookings(user_id)

    if not bookings:
        await message.answer('У вас пока нет активных бронирований.')
        return

    text = '<b>Ваши активные бронирования:</b>\n\n'
    for index, booking in enumerate(bookings, start=1):
        booking_id, date, time, guests, preference, status = booking

        status_text = 'Ожидает оплаты' if status == 'pending' else 'Подтверждено'

        text += (f'-------------------------{index}--------------------------\n\n'
                 f'<b>Дата:</b> {date}\n'
                 f'<b>Время:</b> {time}\n'
                 f'<b>Количество:</b> {guests} чел.\n'
                 f'<b>У окна:</b> {preference}\n'
                 f'<b>Статус:</b> {status_text}\n\n')

    await message.answer(text, parse_mode='HTML')


@router.message(Command('cancel'))
async def cmd_cancel(message: Message):
    user_id = message.from_user.id if message.from_user else 0
    bookings = get_user_bookings(user_id)

    if not bookings:
        await message.answer('У вас нет активных бронирований для отмены.')
        return

    kb = []
    for booking in bookings:
        booking_id, date, time, guests, preference, status = booking

        btn = InlineKeyboardButton(
            text=f'❌ Отменить бронь на {date} в {time}',
            callback_data=f'del_{booking_id}'
        )
        kb.append([btn])

    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer('Выберите бронирование, которое хотите отменить:',
                         reply_markup=keyboard)


@router.message(BookingState.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text or '', '%d.%m')
    except (ValueError, TypeError):
        await message.answer('Неверный формат!\n'
                             'Пожалуйста, введите дату'
                             'строго в формате ДД.ММ.\n'
                             'Например: 22.06')
        return

    await state.update_data(date=message.text)
    await message.answer('Введите время.\n'
                         'Например: 15:00\n')
    await state.set_state(BookingState.waiting_for_time)


@router.message(BookingState.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text or '', '%H:%M')
    except (ValueError, TypeError):
        await message.answer('Неверный формат!\n'
                             'Пожалуйста, введите время'
                             'строго в формате ЧЧ:ММ.\n'
                             'Например: 15:00')

    await state.update_data(time=message.text)

    kb = [
        [KeyboardButton(text='1'), KeyboardButton(text='2'), KeyboardButton(text='3')],
        [KeyboardButton(text='4'), KeyboardButton(text='5'), KeyboardButton(text='6')]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer('Сколько человек на бронировании?', reply_markup=keyboard)
    await state.set_state(BookingState.waiting_for_guests)


@router.message(BookingState.waiting_for_guests)
async def process_guests(message: Message, state: FSMContext):
    await state.update_data(guests=message.text)

    kb = [
        [KeyboardButton(text='Да'), KeyboardButton(text='Нет')]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.answer('Хотите выбрать место у окна?', reply_markup=keyboard)
    await state.set_state(BookingState.waiting_for_preference)


@router.message(BookingState.waiting_for_preference, F.text)
async def process_preference(message: Message, state: FSMContext):
    await state.update_data(preference=message.text)

    user_data = await state.get_data()

    date = user_data.get('date')
    time = user_data.get('time')
    guests = user_data.get('guests')
    preference = user_data.get('preference')

    summary = (
        f'✅<b>Бронирование успешно создано!</b>\n\n'
        f'📅Дата: {date}\n'
        f'🕰️Время: {time}\n'
        f'👥Количество: {guests}\n'
        f'🪟Место у окна: {preference}\n'
    )

    kb = [
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_booking')],
        [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_booking')]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=kb)

    msg = await message.answer('Формируем заявку...',
                               reply_markup=ReplyKeyboardRemove())
    await msg.delete()

    await message.answer(
        summary,
        reply_markup=keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'confirm_booking')
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()

    if not user_data:
        if isinstance(callback.message, Message):
            await callback.message.answer('Данные устарели. Начните бронирование заново: /book')
            await callback.answer()
            return

    prices = [LabeledPrice(label='Депозит на бронирование',
                           amount=300000)]

    if isinstance(callback.message, Message):
        await callback.message.answer_invoice(
            title='Ресторан ANSAR',
            description=f'Депозит за столик на {user_data.get("date")} в {user_data.get("time")}',
            payload='booking_deposit',
            provider_token=PAYMENT_TOKEN,
            currency='RUB',
            prices=prices,
            start_parameter='booking_deposit'
        )

        await callback.message.delete()

    await callback.answer()


@router.callback_query(F.data == 'cancel_booking')
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    if isinstance(callback.message, Message):
        await callback.message.edit_text('🚫 Бронирование отменено. '
                                         'Чтобы начать заново, нажмите /book')

    await callback.answer()


@router.callback_query(F.data.startswith('del_'))
async def process_delete(callback: CallbackQuery):
    if not callback.data:
        return

    booking_id = int(callback.data.split('_')[1])

    delete_booking(booking_id)

    if isinstance(callback.message, Message):
        await callback.message.edit_text('✅ Бронирование успешно отменено '
                                         'и удалено из базы.')

    await callback.answer('Удалено!')


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    if not message.successful_payment:
        return

    user_data = await state.get_data()

    date = user_data.get('date')
    time = user_data.get('time')
    guests = user_data.get('guests')
    preference = user_data.get('preference')

    user_id = message.from_user.id if message.from_user else 0
    username = message.from_user.username if (message.from_user
                                              and message.from_user.username) else 'Неизвестно'

    add_booking(
        user_id=user_id,
        username=username,
        date=date,
        time=time,
        guests=guests,
        preference=preference
    )

    await message.answer(
        f'<b>Оплата прошла успешно!</b>\n\n'
        f'Ваш депозит в размере '
        f'{message.successful_payment.total_amount // 100} руб. получен.\n'
        f'Бронь на {date} в {time} подтверждена.', parse_mode='HTML'
    )

    await state.clear()


@router.inline_query()
async def process_inline_query(inline_query: InlineQuery):
    user_id = inline_query.from_user.id
    bookings = get_user_bookings(user_id)

    results = []

    if not bookings:
        msg = InputTextMessageContent(
            message_text='У меня пока нет активных бронирований в ресторане <b>ANSAR</b>',
            parse_mode='HTML'
        )
        results.append(
            InlineQueryResultArticle(
                id='no_bookings',
                title='Нет активных бронирований',
                description='Нажмите, чтобы отправить это сообщение',
                input_message_content=msg
            )
        )
    else:
        for booking in bookings:
            booking_id, date, time, guests, preference, status = booking
            status_text = 'Ожидает оплаты' if status == 'pending' else 'Подтверждено'

            text = (
                f'Я забронировал столик в ресторане <b>ANSAR</b>\n\n'
                f'Дата: {date}\n'
                f'Время: {time}\n'
                f'Нас будет: {guests} чел.\n\n'
                f'Увидимся там!'
            )

            msg = InputTextMessageContent(message_text=text, parse_mode='HTML')

            results.append(
                InlineQueryResultArticle(
                    id=f'booking_{booking_id}',
                    title=f'Бронь на {date} в {time}',
                    description=f'Количество: {guests} | Статус: {status_text}',
                    input_message_content=msg
                )
            )

    await inline_query.answer(results, cache_time=1, is_personal=True)










