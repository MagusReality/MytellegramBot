import os
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import datetime
import requests
import random
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токены берутся из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

user_history = {}

# Список предсказаний (50 событий + 50 да/нет)
PREDICTIONS_EVENTS = [
    "Тебя ждёт уютный вечер с близкими.",
    "Тебя ожидает день полный сюрпризов.",
    "Тебя ждёт спокойное и приятное время.",
    "Тебя ждёт неожиданная встреча.",
    "Тебя ждут новые возможности.",
    "Время будет полным вдохновения.",
    "Ты найдёшь ответ на важный вопрос.",
    "Тебя ждёт тихий и расслабляющий день.",
    "Тебя ожидает весёлое время с друзьями.",
    "Ты сделаешь что-то необычное.",
    "Тебя ждёт приятный сюрприз дома.",
    "Ты проведёшь время в хорошей компании.",
    "Тебя ждёт успех в начинаниях.",
    "Ты почувствуешь себя особенным.",
    "Тебя ждёт романтическая атмосфера.",
    "Время будет ярким и запоминающимся.",
    "Тебя ожидает неожиданный звонок.",
    "Ты откроешь для себя что-то новое.",
    "Тебя ждёт душевное тепло.",
    "Ты проведёшь время в приятной беседе.",
    "Тебя ждёт момент радости и смеха.",
    "Время будет полным событий.",
    "Тебя ждёт отдых после долгого дня.",
    "Ты сделаешь шаг к своей мечте.",
    "Тебя ждёт чувство свободы.",
    "Тебя ожидает подарок судьбы.",
    "Ты будешь в центре внимания.",
    "Тебя ждёт гармония и покой.",
    "Время будет полным творчества.",
    "Тебя ждёт встреча, меняющая планы.",
    "Ты почувствуешь себя счастливым.",
    "Тебя ждёт ясность в мыслях.",
    "Ты найдёшь что-то приятное.",
    "Тебя ждёт время вдохновения.",
    "Тебя ожидает успех в делах.",
    "Тебя ждёт тёплое и уютное время.",
    "Ты отправишься в небольшое приключение.",
    "Ты получишь хорошие новости.",
    "Время пройдёт легко и беззаботно.",
    "Тебя ждёт момент уединения.",
    "Тебя ждёт неожиданная помощь.",
    "Ты найдёшь новые идеи.",
    "Тебя ждёт время полное смеха.",
    "Ты испытаешь чувство гордости.",
    "Ты проведёшь время в разговорах.",
    "Ты сделаешь что-то важное.",
    "Тебя ждёт сюрприз от судьбы.",
    "Ты испятаешь яркие эмоции.",
    "Ты найдёшь потерянное.",
    "Тебя ждёт вечер с книгой."
]

PREDICTIONS_YES_NO = [
    "Да, всё пройдёт удачно.",
    "Нет, удачи не жди.",
    "Да, день будет успешным.",
    "Нет, лучше отложить планы.",
    "Да, ты будешь доволен.",
    "Нет, время будет сложным.",
    "Да, удача улыбнётся тебе.",
    "Нет, жди трудностей.",
    "Да, всё сложится хорошо.",
    "Нет, возможны сюрпризы.",
    "Да, день будет лёгким.",
    "Нет, будь осторожен.",
    "Да, ты достигнешь цели.",
    "Нет, пока не получится.",
    "Да, время будет приятным.",
    "Нет, жди напряжения.",
    "Да, всё будет в порядке.",
    "Нет, планы изменятся.",
    "Да, удача на твоей стороне.",
    "Нет, день будет обычным.",
    "Да, ты сделаешь успех.",
    "Нет, жди неожиданностей.",
    "Да, всё пройдёт гладко.",
    "Нет, возможны задержки.",
    "Да, день будет ярким.",
    "Нет, удачи не предвидится.",
    "Да, ты будешь счастлив.",
    "Нет, жди разочарований.",
    "Да, всё получится.",
    "Нет, будь готов к проблемам.",
    "Да, время будет тёплым.",
    "Нет, жди холодного дня.",
    "Да, ты найдёшь радость.",
    "Нет, день будет серым.",
    "Да, удача ждёт тебя.",
    "Нет, планы сорвутся.",
    "Да, всё будет легко.",
    "Нет, жди испытаний.",
    "Да, ты будешь в гармонии.",
    "Нет, жди хаоса.",
    "Да, день будет хорошим.",
    "Нет, возможны споры.",
    "Да, ты сделаешь шаг вперёд.",
    "Нет, жди застоя.",
    "Да, время будет удачным.",
    "Нет, жди неприятностей.",
    "Да, ты найдёшь покой.",
    "Нет, жди беспокойства.",
    "Да, всё будет отлично.",
    "Нет, день будет трудным."
]

async def start(update, context):
    logger.info("Received /start command")
    await update.message.reply_text('Привет! Я бот предсказаний. Задавай вопросы для предсказаний!')

def get_prediction(user_id, message):
    logger.info(f"Generating prediction for user {user_id}: {message}")
    past_context = user_history.get(user_id, [])
    context_str = f"Прошлые запросы: {', '.join(past_context)}" if past_context else ""
    
    # Определяем тип вопроса (да/нет или событие)
    message_lower = message.lower()
    is_yes_no = any(word in message_lower for word in ["будет ли", "можно ли", "да или нет", "сбудется ли", "получится ли"])
    
    # Первая попытка: sberbank-ai/rugpt3medium_based_on_gpt2
    try:
        response = requests.post(
            'https://api-inference.huggingface.co/models/sberbank-ai/rugpt3medium_based_on_gpt2',
            headers={'Authorization': f'Bearer {HUGGINGFACE_API_KEY}'},
            json={
                'inputs': f"На вопрос '{message}' дай одно короткое предсказание:\n",
                'parameters': {'max_length': 50, 'min_length': 10, 'temperature': 0.7, 'top_p': 0.9}
            },
            timeout=5
        )
        logger.info(f"Primary API (rugpt3medium) response status: {response.status_code}")
        logger.info(f"Primary API (rugpt3medium) response content: {response.text}")
        
        if response.status_code == 200:
            response_json = response.json()
            if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
                full_prediction = response_json[0]['generated_text'].strip()
                prediction = full_prediction.replace(f"На вопрос '{message}' дай одно короткое предсказание:\n", "").strip()
                prediction = prediction.split('\n')[0].split('.')[0] + '.' if '.' in prediction.split('\n')[0] else prediction.split('\n')[0]
                if prediction and len(prediction) > 5:
                    user_history.setdefault(user_id, []).append(message)
                    return prediction
                else:
                    logger.info("Primary API returned empty or invalid prediction, trying secondary API")
            else:
                logger.info("Primary API returned unexpected format, trying secondary API")
        else:
            logger.info("Primary API failed (non-200 status), trying secondary API")
    except (requests.exceptions.Timeout, requests.exceptions.JSONDecodeError, Exception) as e:
        logger.info(f"Primary API failed: {str(e)}, trying secondary API")

    # Вторая попытка: facebook/xglm-564M
    try:
        response = requests.post(
            'https://api-inference.huggingface.co/models/facebook/xglm-564M',
            headers={'Authorization': f'Bearer {HUGGINGFACE_API_KEY}'},
            json={
                'inputs': f"На вопрос '{message}' дай одно короткое предсказание:\n",
                'parameters': {'max_length': 50, 'min_length': 10, 'temperature': 0.7, 'top_p': 0.9}
            },
            timeout=5
        )
        logger.info(f"Secondary API (xglm-564M) response status: {response.status_code}")
        logger.info(f"Secondary API (xglm-564M) response content: {response.text}")
        
        if response.status_code == 200:
            response_json = response.json()
            if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
                full_prediction = response_json[0]['generated_text'].strip()
                prediction = full_prediction.replace(f"На вопрос '{message}' дай одно короткое предсказание:\n", "").strip()
                prediction = prediction.split('\n')[0].split('.')[0] + '.' if '.' in prediction.split('\n')[0] else prediction.split('\n')[0]
                if prediction and len(prediction) > 5:
                    user_history.setdefault(user_id, []).append(message)
                    return prediction
                else:
                    logger.info("Secondary API returned empty or invalid prediction, using fallback")
            else:
                logger.info("Secondary API returned unexpected format, using fallback")
        else:
            logger.info("Secondary API failed (non-200 status), using fallback")
    except (requests.exceptions.Timeout, requests.exceptions.JSONDecodeError, Exception) as e:
        logger.info(f"Secondary API failed: {str(e)}, using fallback")

    # Если оба API не дали корректный ответ, используем заглушку
    logger.info("Both APIs unavailable or invalid, using fallback prediction")
    if is_yes_no:
        prediction = random.choice(PREDICTIONS_YES_NO)
    else:
        prediction = random.choice(PREDICTIONS_EVENTS)
    user_history.setdefault(user_id, []).append(message)
    return prediction

async def handle_message(update, context):
    logger.info("Handling message")
    user_id = update.message.from_user.id
    message = update.message.text
    
    prediction = get_prediction(user_id, message)
    await update.message.reply_text(prediction)

async def test_message(update, context):
    logger.info("Received /test command")
    await update.message.reply_text('Тестовое сообщение. Бот работает!')

def main():
    logger.info("Starting bot")
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set. Please provide a valid token.")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("test", test_message))

    logger.info("Bot is polling")
    app.run_polling()

if __name__ == '__main__':
    main()