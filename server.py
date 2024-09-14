import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from utils import JSONLoader, ChannelParser


class TelegramBot:
    def __init__(self, token, channels):
        self.application = Application.builder().token(token).build()
        self.channels = channels
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_button_click))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self._delete_previous_message(update, context)
        keyboard = self._build_channel_keyboard()
        message = await update.effective_chat.send_message('Оберіть канал:', reply_markup=keyboard)
        context.user_data['previous_message_id'] = message.message_id

    async def handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        handler_map = {
            'channel_': self._handle_channel_selection,
            'day_': self._handle_day_selection,
            'back_to_start': self.start,
            'back_to_channel': self._handle_back_to_channel,
        }

        for prefix, handler in handler_map.items():
            if query.data.startswith(prefix):
                await handler(update, context)
                break

    async def _handle_channel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        channel = query.data.split('_')[1]

        context.user_data['channel'] = channel
        website = self.channels[channel]
        context.user_data['tv_schedule'] = {}

        await query.edit_message_text(text="Завантаження даних...")

        parser = ChannelParser(website)
        program_days = parser.get_available_days()
        context.user_data['program_days'] = program_days

        keyboard = self._build_day_keyboard(program_days)
        await query.edit_message_text(text="Оберіть день:", reply_markup=keyboard)

    async def _handle_day_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        day = query.data.split('_')[1]

        if context.user_data.get('channel') is None:
            await self.start(update, context)
            return

        await query.edit_message_text(text="Завантаження даних...")

        if 'tv_schedule' not in context.user_data:
            context.user_data['tv_schedule'] = {}

        if day not in context.user_data['tv_schedule']:
            channel = context.user_data.get('channel')
            website = self.channels[channel]

            parser = ChannelParser(website)
            context.user_data['tv_schedule'] = parser.get_tv_schedule(context.user_data['program_days'])

        schedule = context.user_data['tv_schedule'][day]
        keyboard = self._build_navigation_keyboard(day, context)
        await query.edit_message_text(text=f"Телепрограма на {day}:\n{schedule}", reply_markup=keyboard)

    async def _handle_back_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        program_days = context.user_data['program_days']
        keyboard = self._build_day_keyboard(program_days)
        await query.edit_message_text(text="Оберіть день:", reply_markup=keyboard)

    async def _delete_previous_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if 'previous_message_id' in context.user_data:
            await context.bot.delete_message(chat_id=update.effective_chat.id,
                                             message_id=context.user_data['previous_message_id'])

    def _build_channel_keyboard(self):
        keyboard = []
        row = []
        for index, channel in enumerate(self.channels.keys(), start=1):
            row.append(InlineKeyboardButton(channel, callback_data=f'channel_{channel}'))
            if index % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)

    def _build_day_keyboard(self, program_days):
        keyboard = [[InlineKeyboardButton(day, callback_data=f'day_{day}')] for day in program_days]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_start')])
        return InlineKeyboardMarkup(keyboard)

    def _build_navigation_keyboard(self, current_day, context):
        keyboard = []
        program_days = context.user_data['program_days']
        current_index = program_days.index(current_day)

        if current_index > 0:
            prev_day = program_days[current_index - 1]
            keyboard.append([InlineKeyboardButton("Повернутись до попереднього дня", callback_data=f'day_{prev_day}')])
        if current_index < len(program_days) - 1:
            next_day = program_days[current_index + 1]
            keyboard.append([InlineKeyboardButton("Перейти на наступний день", callback_data=f'day_{next_day}')])
        keyboard.append([InlineKeyboardButton("Назад до списку днів", callback_data='back_to_channel')])
        keyboard.append([InlineKeyboardButton("Назад до списку каналів", callback_data='back_to_start')])
        return InlineKeyboardMarkup(keyboard)

    def run(self):
        self.application.run_polling()


class BotInitializer:
    @staticmethod
    def initialize_bot():
        load_dotenv()
        json_file_path = 'channels.json'
        channels = JSONLoader.load(json_file_path)
        token = os.getenv('TELEGRAM_TOKEN')

        if channels:
            bot = TelegramBot(token, channels)
            bot.run()


if __name__ == '__main__':
    BotInitializer.initialize_bot()
