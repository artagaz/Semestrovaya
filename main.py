import os
import requests
from bs4 import BeautifulSoup
import telebot
from datetime import datetime

# Инициализация бота
bot = telebot.TeleBot("7927124560:AAEH8Np2jp5e3cvL_VNE_Zk-H6Y1DQtDImA")

# API ключ для Яндекс.Погоды v3
YANDEX_WEATHER_API_KEY = "4f377d0d-fd02-4681-9b1f-5a51ac58217a"

access_key = "4f377d0d-fd02-4681-9b1f-5a51ac58217a"


# Функция для логирования диалога
def log_message(user_id, message, is_bot=False):
    log_file = f"{user_id}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sender = "Bot" if is_bot else f"User {user_id}"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")


# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    welcome_text = (
        "Привет! Я бот для прогноза погоды.\n"
        "Доступные команды:\n"
        "/current - Текущая погода\n"
        "/forecast - Прогноз погоды на неделю\n Осторожно, очень длинное сообщение!\n"
        "/scrape - скрапинг погоды\n"
        "/hourly - Почасовой прогноз на 24 часа\n"
        "/history - История ваших запросов"
    )
    bot.reply_to(message, welcome_text)
    log_message(user_id, "/start")
    log_message(user_id, welcome_text, is_bot=True)


# функция для получения координат !!!!
def get_moscow_coordinates():
    return "55.7558", "37.6173"


# текущая погода
@bot.message_handler(commands=['current'])
def get_current_weather(message):
    user_id = message.from_user.id
    log_message(user_id, "/current")

    try:
        headers = {
            "X-Yandex-Weather-Key": access_key
        }

        query = """{
            weatherByPoint(request: { lat: 52.37125, lon: 4.89388 }) {
                now {
                    temperature
                    humidity
                    pressure
                    windSpeed
                    windDirection          
                    cloudiness
                    precType
                    precStrength
                }
            }
        }"""

        response = requests.post('https://api.weather.yandex.ru/graphql/query', headers=headers, json={'query': query})
        data = response.json()
        now = data['data']['weatherByPoint']['now']

        weather_info = (
            f"Текущая погода:\n"
            f"🌡 Температура: {now['temperature']}°C\n"
            f"💧 Влажность: {now['humidity']}%\n"
            f"📊 Давление: {now['pressure']} мм рт.ст.\n"
            f"🌬 Ветер: {now['windSpeed']} м/с, {translate_windir(now['windDirection'])}\n"
            f"☁️ Осадки: {translate_condition(now['precType'])}, сила: {translate_prec(now['precStrength'])}\n"
        )

        bot.reply_to(message, weather_info)
        log_message(user_id, weather_info, is_bot=True)
    except Exception as e:
        error_msg = f"Ошибка при запросе погоды: {str(e)}"
        bot.reply_to(message, error_msg)
        log_message(user_id, error_msg, is_bot=True)


# Команда /forecast - прогноз на неделю через Яндекс.Погоды API v3
@bot.message_handler(commands=['forecast'])
def get_weather_forecast(message):
    user_id = message.from_user.id
    log_message(user_id, "/forecast")

    try:
        headers = {
            "X-Yandex-Weather-Key": access_key
        }

        query = """{                    
                    weatherByPoint(request: { lat: 52.37125, lon: 4.89388 }) {
                        forecast {
                          days(limit: 7) {
                             time
                             parts {
                                morning {
                                    temperature
                                    humidity
                                    pressure
                                    windSpeed
                                    windDirection          
                                    cloudiness
                                    precType
                                    precStrength
                                }
                                day {
                                    temperature
                                    humidity
                                    pressure
                                    windSpeed
                                    windDirection          
                                    cloudiness
                                    precType
                                    precStrength
                                }
                                evening {
                                    temperature
                                    humidity
                                    pressure
                                    windSpeed
                                    windDirection          
                                    cloudiness
                                    precType
                                    precStrength
                                }
                                night {
                                    temperature
                                    humidity
                                    pressure
                                    windSpeed
                                    windDirection          
                                    cloudiness
                                    precType
                                    precStrength
                                }
                                }
                            }
                        }
                    }
                }"""

        response = requests.post('https://api.weather.yandex.ru/graphql/query', headers=headers, json={'query': query})
        data = response.json()

        days = data['data']['weatherByPoint']['forecast']['days']

        forecast_info = "Прогноз погоды на неделю:\n"

        for day in days:
            date = day['time'][0:10]
            morning = day['parts']['morning']
            day_time = day['parts']['day']
            evening = day['parts']['evening']
            night = day['parts']['night']

            forecast_info += (
                "------------------------------------------------------"
                f"\n📅 {date} утро:\n"
                f"🌡 Температура: {morning['temperature']}°C\n"
                f"🌬 Ветер: {morning['windSpeed']} м/с, {translate_windir(morning['windDirection'])}\n"
                f"☁️ Осадки: {translate_condition(morning['precType'])}, сила: {translate_prec(morning['precStrength'])}\n\n"

                f"\n📅 {date} день:\n"
                f"🌡 Температура: {day_time['temperature']}°C\n"
                f"🌬 Ветер: {day_time['windSpeed']} м/с, {translate_windir(day_time['windDirection'])}\n"
                f"☁️ Осадки: {translate_condition(day_time['precType'])}, сила: {translate_prec(day_time['precStrength'])}\n\n"

                f"\n📅 {date} вечер:\n"
                f"🌡 Температура: {evening['temperature']}°C\n"
                f"🌬 Ветер: {evening['windSpeed']} м/с, {translate_windir(evening['windDirection'])}\n"
                f"☁️ Осадки: {translate_condition(evening['precType'])}, сила: {translate_prec(evening['precStrength'])}\n\n"

                f"\n📅 {date} ночь:\n"
                f"🌡 Температура: {night['temperature']}°C\n"
                f"🌬 Ветер: {night['windSpeed']} м/с, {translate_windir(night['windDirection'])}\n"
                f"☁️ Осадки: {translate_condition(night['precType'])}, сила: {translate_prec(night['precStrength'])}\n\n"
            )

        bot.reply_to(message, forecast_info)
        log_message(user_id, forecast_info, is_bot=True)
    except Exception as e:
        error_msg = f"Ошибка при запросе прогноза: {str(e)}"
        bot.reply_to(message, error_msg)
        log_message(user_id, error_msg, is_bot=True)


# Команда /hourly - почасовой прогноз на 24 часа
@bot.message_handler(commands=['hourly'])
def get_hourly_forecast(message):
    user_id = message.from_user.id
    log_message(user_id, "/hourly")

    try:
        lat, lon = get_moscow_coordinates()

        # Запрос к API Яндекс.Погоды v3
        url = f"https://api.weather.yandex.ru/v3/forecast?lat={lat}&lon={lon}&limit=1&hours=true"
        headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()

        hourly_info = "Почасовой прогноз на 24 часа в Москве:\n"

        for hour in data['forecasts'][0]['hours']:
            if hour['hour'] in ['6', '12', '18', '21']:  # Показываем ключевые часы
                hourly_info += (
                    f"\n⏰ {hour['hour']}:00:\n"
                    f"🌡 {hour['temp']}°C, {translate_condition(hour['condition'])}\n"
                    f"🌬 Ветер: {hour['wind_speed']} м/с\n"
                )

        bot.reply_to(message, hourly_info)
        log_message(user_id, hourly_info, is_bot=True)
    except Exception as e:
        error_msg = f"Ошибка при запросе почасового прогноза: {str(e)}"
        bot.reply_to(message, error_msg)
        log_message(user_id, error_msg, is_bot=True)


# Команда /scrape - получение погоды методом скрапинга
@bot.message_handler(commands=['scrape'])
def scrape_weather(message):
    user_id = message.from_user.id
    log_message(user_id, "/scrape")

    try:
        # Скрапинг с сайта Яндекс.Погоды
        url = "https://yandex.ru/pogoda/moscow/details"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Поиск нужных элементов
        current_temp = soup.find('div', class_='temp fact__temp fact__temp_size_s').find('span',
                                                                                         class_='temp__value').text
        condition = soup.find('div', class_='link__condition day-anchor i-bem').text.strip()
        feels_like = soup.find('div', class_='term term_orient_h fact__feels-like').find('span',
                                                                                         class_='temp__value').text

        scraped_info = (
            "Данные получены методом скрапинга с Яндекс.Погоды:\n"
            f"🌡 Текущая температура: {current_temp}°C\n"
            f"🌡 Ощущается как: {feels_like}°C\n"
            f"☁ Погодные условия: {condition}"
        )

        bot.reply_to(message, scraped_info)
        log_message(user_id, scraped_info, is_bot=True)
    except Exception as e:
        error_msg = f"Ошибка при скрапинге: {str(e)}"
        bot.reply_to(message, error_msg)
        log_message(user_id, error_msg, is_bot=True)


# Команда /history - показ истории запросов
@bot.message_handler(commands=['history'])
def show_history(message):
    user_id = message.from_user.id
    log_message(user_id, "/history")

    log_file = f"{user_id}.log"

    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                history = f.read()

            # Отправляем последние 10 строк истории
            last_lines = "\n".join(history.split("\n")[-10:])
            bot.reply_to(message, f"Последние записи в истории:\n{last_lines}")
            log_message(user_id, "Показана история запросов", is_bot=True)
        except Exception as e:
            error_msg = f"Ошибка при чтении истории: {str(e)}"
            bot.reply_to(message, error_msg)
            log_message(user_id, error_msg, is_bot=True)
    else:
        no_history_msg = "История запросов пока пуста."
        bot.reply_to(message, no_history_msg)
        log_message(user_id, no_history_msg, is_bot=True)


# Функции для перевода значений из API
def translate_condition(condition):
    conditions = {
        'NO_TYPE': 'нет осадков',
        'RAIN': 'дождь',
        'SLEET': 'слякоть',
        'SNOW': 'снег',
        'HAIL': 'град'
    }
    return conditions.get(condition, condition)


def translate_windir(wind_dir):
    directions = {
        'NORTH_WEST': 'северо-западный',
        'NORTH': 'северный',
        'NORTH_EAST': 'северо-восточный',
        'EAST': 'восточный',
        'SOUTH_EAST': 'юго-восточный',
        'SOUTH': 'южный',
        'SOUTH_WEST': 'юго-западный',
        'WEST': 'западный',
        'CALM': 'штиль'
    }
    return directions.get(wind_dir, wind_dir)


def translate_prec(prec_strength):
    prec = {
        'ZERO': 'без осадков',
        'WEAK': 'слабые осадки',
        'AVERAGE': 'умеренные осадки',
        'STRONG': 'сильные осадки',
        'VERY_STRONG': 'очень сильные осадки'
    }
    return prec.get(prec_strength, 'неизвестная интенсивность')


# Обработка всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_id = message.from_user.id
    log_message(user_id, message.text)

    reply_text = "Извините, я не понимаю. Используйте одну из команд: /start, /current, /forecast, /hourly, /scrape, /history"
    bot.reply_to(message, reply_text)
    log_message(user_id, reply_text, is_bot=True)


# Запуск бота
print("Бот запущен...")
bot.infinity_polling()
