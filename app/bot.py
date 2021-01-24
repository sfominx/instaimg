"""
Telegram bot
"""
import io
import logging
from pathlib import Path

from PIL import ImageFont
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

from text_to_image import TextToImages

DEFAULT_FONT_FAMILY = 'roboto'
DEFAULT_FONT_SIZE = 40
DEFAULT_FONT_COLOR = (0, 0, 0)
DEFAULT_BACKGROUND_COLOR = (255, 255, 255)
DEFAULT_ORIENTATION = 'square'

DEFAULT_IMG_WIDTH = 720

FONTS = {'roboto': 'Roboto-Regular.ttf',
         'raleway': 'Raleway-Regular.ttf',
         'playfair': 'PlayfairDisplay-Regular.ttf'}

ORIENTATION = {'square': (DEFAULT_IMG_WIDTH, DEFAULT_IMG_WIDTH),
               'vertical': (DEFAULT_IMG_WIDTH, DEFAULT_IMG_WIDTH // 4 * 5),
               'horizontal': (DEFAULT_IMG_WIDTH, DEFAULT_IMG_WIDTH // 16 * 9)}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

client = MongoClient('mongodb://mongo:27017')
db = client['instaimg']
configs = db.configs


def start(update: Update, context: CallbackContext) -> None:
    """Welcome message"""
    update.message.reply_text('Добро пожаловать в Text2Image бот.\n'
                              'Пришли мне текст и я переведу его в изображения.\n\n'
                              'Так же можно настроить шрифт и его размер:\n'
                              '/font — выбор шрифта\n'
                              '/size — выбор размера шрифта')


def button(update: Update, context: CallbackContext) -> None:
    """Button press"""
    query = update.callback_query
    query.answer()

    user_query = {'user_id': update.effective_chat.id}

    if query.data.startswith('font'):
        if query.data == 'font_roboto':
            set_query = {'$set': {'font-family': 'roboto'}}
            selected_font = 'Roboto'
        elif query.data == 'font_raleway':
            set_query = {'$set': {'font-family': 'raleway'}}
            selected_font = 'Raleway'
        elif query.data == 'font_playfair':
            set_query = {'$set': {'font-family': 'playfair'}}
            selected_font = 'Playfair'
        else:
            set_query = {'$set': {'font-family': DEFAULT_FONT_FAMILY}}
            selected_font = DEFAULT_FONT_FAMILY.title()

        configs.update_one(user_query, set_query)
        query.edit_message_text(text=f'Выбранный шрифт: {selected_font}')

    if query.data.startswith('size'):
        if query.data == 'size_smallest':
            set_query = {'$set': {'font-size': 20}}
            selected_size = 'XS'
        elif query.data == 'size_small':
            set_query = {'$set': {'font-size': 30}}
            selected_size = 'S'
        elif query.data == 'size_medium':
            set_query = {'$set': {'font-size': 40}}
            selected_size = 'M'
        elif query.data == 'size_big':
            set_query = {'$set': {'font-size': 50}}
            selected_size = 'L'
        elif query.data == 'size_biggest':
            set_query = {'$set': {'font-size': 60}}
            selected_size = 'XL'
        else:
            set_query = {'$set': {'font-size': DEFAULT_FONT_SIZE}}
            selected_size = DEFAULT_FONT_SIZE

        configs.update_one(user_query, set_query)
        query.edit_message_text(text=f'Выбранный размер шрифта: {selected_size}')


def help_command(update: Update, context: CallbackContext) -> None:
    """/help command"""
    update.message.reply_text('/font — выбор шрифта\n'
                              '/size — выбор размера шрифта')


def font_command(update: Update, context: CallbackContext) -> None:
    """/font command"""
    font_list = [[InlineKeyboardButton(text='Roboto', callback_data='font_roboto'),
                  InlineKeyboardButton(text='Raleway', callback_data='font_raleway'),
                  InlineKeyboardButton(text='Playfair', callback_data='font_playfair')
                  ],
                 ]
    keyboard = InlineKeyboardMarkup(font_list)

    update.message.reply_text('Выберите шрифт', reply_markup=keyboard)


def size_command(update: Update, context: CallbackContext) -> None:
    """/size command"""
    font_list = [[InlineKeyboardButton(text='XS', callback_data='size_smallest'),
                  InlineKeyboardButton(text='S', callback_data='size_small'),
                  InlineKeyboardButton(text='M', callback_data='size_medium'),
                  InlineKeyboardButton(text='L', callback_data='size_big'),
                  InlineKeyboardButton(text='XL', callback_data='size_biggest')
                  ],
                 ]
    keyboard = InlineKeyboardMarkup(font_list)

    update.message.reply_text('Выберите размер шрифта', reply_markup=keyboard)


def response(update: Update, context: CallbackContext) -> None:
    """Response with images"""
    user_config = configs.find_one({'user_id': update.effective_chat.id})
    if not user_config:
        default_user_config = {'user_id': update.effective_chat.id,
                               'font-family': DEFAULT_FONT_FAMILY,
                               'font-size': DEFAULT_FONT_SIZE,
                               'font-color': DEFAULT_FONT_COLOR,
                               'background-color': DEFAULT_BACKGROUND_COLOR,
                               'orientation': DEFAULT_ORIENTATION}
        user_config = configs.find_one({'_id': configs.insert_one(default_user_config).inserted_id})

    user_font = FONTS.get(user_config['font-family'], FONTS[DEFAULT_FONT_FAMILY])
    font = ImageFont.truetype(str(Path('.') / 'fonts' / user_font), user_config['font-size'])

    img_width, img_height = ORIENTATION.get(user_config['orientation'], 'square')
    tti = TextToImages(img_width, img_height, font, tuple(user_config['background-color']))

    images = []
    for part in range(len(tti.split_text(update.message.text, True))):
        image = tti.render(update.message.text, True, part)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, optimize=True, format='PNG')
        img_byte_arr.seek(0)
        images.append(InputMediaPhoto(img_byte_arr))

    update.message.reply_media_group(images)


def main() -> None:
    """Main Telegram Bot function"""
    updater = Updater(Path('telegram_bot_token').read_text().strip(), use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('font', font_command))
    dispatcher.add_handler(CommandHandler('size', size_command))
    response_handler = MessageHandler(Filters.text & (~Filters.command), response)
    dispatcher.add_handler(response_handler)

    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
