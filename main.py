import os
from datetime import datetime
import requests
import telebot
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

# tg bot
bot = telebot.TeleBot("7927124560:AAEH8Np2jp5e3cvL_VNE_Zk-H6Y1DQtDImA")
# yandex api
access_key = "4f377d0d-fd02-4681-9b1f-5a51ac58217a"
# user city
user_coordinates = {}
# city finder
geolocator = Nominatim(user_agent="weather_bot")


# log
def log_message(user_id, message, is_bot=False):
    log_file = f"{user_id}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sender = "Bot" if is_bot else f"User {user_id}"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")


# get cords
def get_user_coordinates(message):
    user_id = message.from_user.id
    if user_coordinates:
        return user_coordinates[user_id]
    else:
        bot.send_message(message.chat.id, "Вы не задали положение, показывается погода для Кемерово.", )
        return '55.3333', '86.0833', 'Кемерово'


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


def transliterate(text):
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
        'э': 'e', 'ю': 'yu', 'я': 'ya', '-': '-', ' ': '-'
    }

    result = []
    for char in text.lower():
        if char in translit_map:
            result.append(translit_map[char])
        else:
            result.append(char)

    return ''.join(result).replace('--', '-').strip('-')


# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    welcome_text = (
        "Привет! Я бот для прогноза погоды.\n"
        "По умолчанию показывается погода для кемерово.\n"
        "Доступные команды:\n"
        "/current - Текущая погода\n"
        "/forecast - Прогноз погоды на неделю\n"
        "Осторожно, длинное сообщение!\n"
        "/scrape - скрапинг погоды\n"
        "/position - указать новую позицию\n"
        "/history - История ваших запросов"
    )
    bot.reply_to(message, welcome_text)
    log_message(user_id, "/start")
    log_message(user_id, welcome_text, is_bot=True)


# weather now
@bot.message_handler(commands=['current'])
def get_current_weather(message):
    user_id = message.from_user.id
    log_message(user_id, "/current")

    try:
        lat, lon, city = get_user_coordinates(message)

        headers = {
            "X-Yandex-Weather-Key": access_key
        }

        query = '''{
            weatherByPoint(request: { lat: ''' + str(lat) + ''', lon: ''' + str(lon) + ''' }) {
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
        }'''

        response = requests.post('https://api.weather.yandex.ru/graphql/query', headers=headers, json={'query': query})
        data = response.json()
        now = data['data']['weatherByPoint']['now']

        weather_info = (
            f"Текущая погода в {city}:\n"
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


# on week
@bot.message_handler(commands=['forecast'])
def get_weather_forecast(message):
    user_id = message.from_user.id
    log_message(user_id, "/forecast")

    try:
        lat, lon, city = get_user_coordinates(message)

        headers = {
            "X-Yandex-Weather-Key": access_key
        }

        query = '''{                    
                    weatherByPoint(request: { lat: ''' + str(lat) + ''', lon: ''' + str(lon) + ''' }) {
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
                }'''

        response = requests.post('https://api.weather.yandex.ru/graphql/query', headers=headers, json={'query': query})
        data = response.json()
        days = data['data']['weatherByPoint']['forecast']['days']

        forecast_info = f"Прогноз погоды на неделю  в {city}:\n"

        for day in days:
            forecast_info += "-------------------------------------\n"

            date = day['time'][0:10]

            times = [
                day['parts']['morning'],
                day['parts']['day'],
                day['parts']['evening'],
                day['parts']['night']
            ]

            times_ru = ['утро', 'день', 'вечер', 'ночь']

            for time, time_ru in zip(times, times_ru):
                forecast_info += (
                    f"\n📅 {date} {time_ru}:\n"
                    f"🌡 Температура: {time['temperature']}°C\n"
                    f"🌬 Ветер: {time['windSpeed']} м/с, {translate_windir(time['windDirection'])}\n"
                    f"☁️ Осадки: {translate_condition(time['precType'])}, сила: {translate_prec(time['precStrength'])}\n\n"
                )

        bot.reply_to(message, forecast_info)
        log_message(user_id, forecast_info, is_bot=True)
    except Exception as e:
        error_msg = f"Ошибка при запросе прогноза: {str(e)}"
        bot.reply_to(message, error_msg)
        log_message(user_id, error_msg, is_bot=True)


@bot.message_handler(commands=['scrape'])
def parse_weather(message):
    try:
        scraped_info = parse_meteoservice_weather(message)
        bot.reply_to(message, scraped_info)
        log_message(message.from_user.id, scraped_info, is_bot=True)
    except Exception as e:
        print(e)


def parse_meteoservice_weather(message):
    user_id = message.from_user.id
    log_message(user_id, "/scrape")

    *_, city = get_user_coordinates(message)

    # запрос
    url = f"https://www.meteoservice.ru/weather/now/{transliterate(city.lower())}"
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    })

    soup = BeautifulSoup(response.text, 'html.parser')

    # температура
    temp_section = soup.find('div', class_='temperature')
    temp = temp_section.get_text(strip=True)

    # температура по ощущениям
    feels_like_temp_section = soup.find('div', class_='h5 feeled-temperature')
    feels_like_temp = feels_like_temp_section.find_next('span', class_='value colorize-server-side').get_text(
        strip=True)

    # облачность
    condition_row = soup.find('div', class_='small-12 columns text-center padding-top-2')
    condition = condition_row.find_next('p', class_='margin-bottom-0').get_text(strip=True)

    return (f"🌤 В {city} сейчас {temp}C\n"
            f"Ощущается как {feels_like_temp}C\n"
            f"Облачность: {condition}\n")


# /position
@bot.message_handler(commands=['position'])
def handle_position(message):
    user_id = message.from_user.id
    log_message(user_id, "/position")

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("Отправить местоположение", request_location=True))

    bot.send_message(
        message.chat.id,
        "Нажмите на кнопку, чтобы отправить своё местоположение или введите свой город вручную:",
        reply_markup=markup
    )

    bot.register_next_step_handler(message, process_position_input)


def process_position_input(message):
    user_id = message.from_user.id

    try:
        if message.location:
            lat = message.location.latitude
            lon = message.location.longitude
            location = geolocator.reverse(f"{lat}, {lon}")
            city = location.raw.get('address', {}).get('city', 'вашем местоположении')

            response = (
                f"Координаты вашего местоположения:\n"
                f"Широта: {lat}\n"
                f"Долгота: {lon}\n"
                f"Город: {city}"
            )

            user_coordinates[user_id] = (lat, lon, city)

        elif message.text:
            city = message.text
            location = geolocator.geocode(city)

            if location:
                lat = location.latitude
                lon = location.longitude

                response = (
                    f"Координаты для города {city}:\n"
                    f"Широта: {lat}\n"
                    f"Долгота: {lon}\n"
                    f"Адрес: {location.address}"
                )

                user_coordinates[user_id] = (lat, lon, city)
            else:
                response = f"Не удалось найти город '{city}'. Попробуйте ещё раз."
                bot.register_next_step_handler(message, process_position_input)
                return
        else:
            response = "Ошибка. Введите название города."
            bot.register_next_step_handler(message, process_position_input)
            return

        bot.send_message(message.chat.id, response, reply_markup=telebot.types.ReplyKeyboardRemove())
        log_message(user_id, response, is_bot=True)

    except Exception as e:
        error_msg = f"Произошла ошибка: {str(e)}"
        bot.send_message(message.chat.id, error_msg)
        log_message(user_id, error_msg, is_bot=True)


# /history
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


# Обработка всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_id = message.from_user.id
    log_message(user_id, message.text)

    reply_text = "Извините, я не понимаю. Используйте одну из команд: /start, /current, /forecast, /scrape, /position, /history"
    bot.reply_to(message, reply_text)
    log_message(user_id, reply_text, is_bot=True)


# Запуск бота
print("started")
bot.infinity_polling()
