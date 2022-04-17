import logging
import datetime
import telebot
from telebot import types
from decouple import config  # you must create .env file
from bots_requests.api_request import Request
from db.database_sql import (read_data_base,
                             db_table_history,
                             hotels_without_photos,
                             bestdeal_without_photos,
                             hotels_with_photos,
                             bestdeal_with_photos)

bot = telebot.TeleBot(config('KEY'))
users_data = dict()
logging.basicConfig(filename='.log', level=logging.INFO, filemode='a')


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """A function that receives requests from the user."""
    user_message = message.text.strip().lower()
    users_data[message.from_user.id] = {'hotels_max': None, 'distance': None, 'prices': None, 'command_name': None,
                                        'citi_name': None, 'sorted_funct': 'ASC'}
    if user_message == "/help" or user_message == '/start':
        bot.send_message(message.from_user.id, 'Please, select one of the commands. '
                                               '\n\n /Lowprice - A command which will help you find '
                                               'hotels with the lowest prices.'
                                               '\n\n /Highprice - A command which will help you to find '
                                               'hotels with the highest prices.'
                                               '\n\n /Bestdeal - Command for finding hotels with '
                                               'your personal parameters. '
                                               '\n\n /History - The command that prints the history of the user.')
        logging.info(f'function: get_text_messages '
                     f'\nuser: {message.from_user.id}'
                     f'\ncommand: help')
    elif user_message == "/lowprice":
        logging.info(f'function: get_text_messages '
                     f'\nuser: {message.from_user.id}'
                     f'\ncommand: lowprice')
        users_data[message.from_user.id]['command_name'] = '/lowprice'
        bot.send_message(message.from_user.id, 'Please, enter your citi')
        bot.register_next_step_handler(message, citi_function)
    elif user_message == '/bestdeal':
        logging.info(f'function: get_text_messages '
                     f'\nuser: {message.from_user.id}'
                     f'\ncommand: bestdeal')
        bot.send_message(message.from_user.id, "Please, enter your price range"
                                               "\n(example 1-100)")
        users_data[message.from_user.id]['command_name'] = '/bestdeal'
        bot.register_next_step_handler(message, best_deal_price)

    elif user_message == "/highprice":
        logging.info(f'function: get_text_messages '
                     f'\nuser: {message.from_user.id}'
                     f'\ncommand: highprice')
        users_data[message.from_user.id]['command_name'] = '/highprice'
        users_data[message.from_user.id]['sorted_funct'] = 'DESC'
        bot.send_message(message.from_user.id, 'Please, enter your citi')
        bot.register_next_step_handler(message, citi_function)
    elif user_message == "/history":
        logging.info(f'function: get_text_messages '
                     f'\nuser: {message.from_user.id}'
                     f'\ncommand: history')
        user_history(message)

    else:
        bot.send_message(message.from_user.id, 'Enter the command /help')


def citi_function(message) -> None:
    """A function that for first checks if our database contains information about a given city and its hotels,
    in order to do not make a request again, if there is no information about the hotel, then an instance of the
    Request class is created, and the record in the database about this City. """
    logging.info(f'function: citi_function '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: check database for user request')
    citi_name = message.text.strip()
    users_data[message.from_user.id]['citi_name'] = citi_name
    my_function = read_data_base(f'SELECT hotel_name FROM users_data'
                                 f' WHERE citi_name="{citi_name}"')
    if my_function:
        bot.send_message(message.from_user.id, f'Enter amount of the hotels \n maximum - {len(my_function)}')
        bot.register_next_step_handler(message, hotels_max)
    else:
        logging.info(f'function: citi_function '
                     f'\nuser: {message.from_user.id}'
                     f'\naction: request for hotel api and create database information')
        bot.send_message(message.from_user.id, 'Already collecting information. \nThanks for waiting.')
        try:
            hotels_request = Request(message.text, message.from_user.id).sorted_hotels()
            if hotels_request:
                bot.send_message(message.from_user.id, f'Enter amount of the hotels'
                                                       f'\n maximum - {len(hotels_request)}:')
                bot.register_next_step_handler(message, hotels_max)
            else:
                bot.send_message(message.from_user.id, 'Maybe there is no such city... \n'
                                                       'Try again')
        except Exception as e:
            logging.info(f'function: citi_function '
                         f'\nuser: {message.from_user.id}'
                         f'\naction: Exception {e}')
            bot.send_message(message.from_user.id, f'Unexpected error, please try again.')


def hotels_max(message) -> None:
    """ A function that checks whether the user entered exactly the numbers, in a negative case, we return
    try again"""
    logging.info(f'function: hotels_max '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: check user request for numbers')
    if message.text.isdigit() and int(message.text) > 0:
        maximum_hotels = int(message.text.strip())
        users_data[message.from_user.id]['hotels_max'] = maximum_hotels
        bot.send_message(message.from_user.id, 'Do you need of photos??')
        bot.register_next_step_handler(message, hotel_photos)
    else:
        bot.send_message(message.from_user.id, 'Please enter the number < 0')
        bot.register_next_step_handler(message, hotels_max)


def hotel_photos(message) -> None:
    """A function that, at the request of the user, either displays photos or information about the hotel."""
    logging.info(f'function: hotel_photos '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: ask user for yes/no')
    user_message = message.text.strip().lower()
    command_name = users_data[message.from_user.id]['command_name']
    citi_name = users_data[message.from_user.id]['citi_name']

    if user_message == 'no':
        if command_name != '/bestdeal':
            sql_response = hotels_without_photos(users_data, message.from_user.id)
        else:
            sql_response = bestdeal_without_photos(users_data, message.from_user.id)

        if sql_response:
            function_for_hotels(sql_response, message.from_user.id, command_name, citi_name)
        else:
            bot.send_message(message.from_user.id, 'Relevant data on absence parameters. '
                                                   '\nTry to enter other parameters.')

    elif user_message == 'yes':

        bot.send_message(message.from_user.id, f'Enter the quantity of the hotels? \n(maximum 5)')
        bot.register_next_step_handler(message, quantity_photos)

    else:
        bot.send_message(message.from_user.id, 'Please enter your answer as yes/no.')
        bot.register_next_step_handler(message, hotel_photos)


def quantity_photos(message) -> None:
    print(message)
    print(type(message))
    """A function that accepts a number of photos from the user."""
    logging.info(f'function: quantity_photos '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: check user message for numbers')
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        maximum_of_photos = int(message.text.strip())
        command_name = users_data[message.from_user.id]['command_name']
        citi_name = users_data[message.from_user.id]['citi_name']
        if command_name != '/bestdeal':
            sql_response = hotels_with_photos(users_data, message.from_user.id)
        else:
            sql_response = bestdeal_with_photos(users_data, message.from_user.id)
        if sql_response:
            function_for_hotels_with_photos(sql_response, message.from_user.id, command_name, citi_name,
                                            maximum_of_photos)
        else:
            bot.send_message(message.from_user.id, 'Relevant data on absence parameters. '
                                                   '\nTry to enter other parameters.')
    else:
        bot.send_message(message.from_user.id, 'Please enter the number from 1 to 5.')
        bot.register_next_step_handler(message, quantity_photos)


def best_deal_price(message) -> None:
    """A function that accepts from the user a price range from the user for the command Bestdeal"""
    logging.info(f'function: best_deal_price '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: try to split user message 1-100.split("-")')
    try:
        price_range = message.text.split('-')
        if price_range[0].isdigit() and price_range[1].isdigit():
            users_data[message.from_user.id]['prices'] = price_range
            bot.send_message(message.from_user.id, 'Enter distance range to center: ')
            bot.register_next_step_handler(message, best_deal_distance)
        else:
            raise ValueError
    except ValueError:
        logging.info(f'function: best_deal_price '
                     f'\nuser: {message.from_user.id}'
                     f'\naction: Exception ValuError')

        bot.send_message(message.from_user.id, 'Please enter numbers as 1-100...')
        bot.register_next_step_handler(message, best_deal_price)


def best_deal_distance(message) -> None:
    """A function that accepts from the user a distance range for the command Bestdeal"""
    logging.info(f'function: best_deal_distance '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: Try to split user message 1-100.split("-")')
    try:
        distance_range = message.text.split('-')
        users_data[message.from_user.id]['distance'] = distance_range
        if distance_range[0].isdigit() and distance_range[1].isdigit():
            bot.send_message(message.from_user.id, 'Please enter your citi')
            bot.register_next_step_handler(message, citi_function)
        else:
            raise Exception
    except Exception as e:
        logging.info(f'function: best_deal_distance '
                     f'\nuser: {message.from_user.id}'
                     f'\naction: Exception {e}')

        bot.send_message(message.from_user.id, 'Please enter numbers as 1-100...')
        bot.register_next_step_handler(message, best_deal_distance)


def user_history(message) -> None:
    """."""
    logging.info(f'function: user_history '
                 f'\nuser: {message.from_user.id}'
                 f'\naction: print user history')
    history_database_request = read_data_base(f'SELECT command_name, date, user_request, citi_name FROM history_table '
                                              f'WHERE user_id = "{message.from_user.id}"')
    if history_database_request:
        for user_data in history_database_request:
            command_name, date, user_request, citi_name = user_data[0], user_data[1], user_data[2], user_data[3]
            bot.send_message(message.from_user.id, f'Command: {command_name}  \n\nCity: {citi_name}'
                                                   f'\n\nDate: {date} \n\nUser Request: \n{user_request}')
    else:
        bot.send_message(message.from_user.id, 'No one request.')


def function_for_hotels(sql_response, user_id, command_name, citi_name) -> None:
    """The function to get information about hotels is based on a database (no photo)"""
    logging.info(f'function: function_for_hotels '
                 f'\nuser: {user_id}'
                 f'\naction: print hotel information from database\n')
    hotels_names = str()
    for sorted_hotels in sql_response:
        hotel_name, price, street, center_distance, hotel_name_url = \
            sorted_hotels[0], sorted_hotels[1], sorted_hotels[2], sorted_hotels[3], sorted_hotels[4]
        hotels_names += sorted_hotels[0] + '\n'
        bot.send_message(user_id, f'[Hotel_name]: {hotel_name} \n[Hotel_price]: {price}'
                                  f'\n[Street]: {street} \n[Center_distance]: {center_distance} '
                                  f'\n[link]: https://ru.hotels.com/ho{hotel_name_url}/',
                         disable_web_page_preview=True)
    db_table_history(user_id, command_name,
                     hotels_names, datetime.datetime.today(), citi_name)


def function_for_hotels_with_photos(sql_response, user_id, command_name, citi_name, maximum_of_photos) -> None:
    """A function that displays information about hotels along with photos comes from a database response"""
    logging.info(f'function: function_for_hotels_with_photos '
                 f'\nuser: {user_id}'
                 f'\naction: print hotel information with photos')
    hotels_names = str()
    for hotel_info in sql_response:
        photos_list = list()
        hotel_name, price, street, center_distance, hotels_urls, hotel_name_url = \
            hotel_info[0], hotel_info[1], hotel_info[2], hotel_info[3], hotel_info[4].split(), hotel_info[5]
        hotels_names += f'\n{hotel_info[0]}'
        bot.send_message(user_id, f'[Hotel_name]: {hotel_name} \n[Hotel_price]: {price}'
                                  f'\n[Street]: {street} \n[Center_distance]: {center_distance}'
                                  f'\n[link]: https://ru.hotels.com/ho{hotel_name_url}/',
                         disable_web_page_preview=True)
        for photo in hotels_urls[0:maximum_of_photos]:
            photos_list.append(types.InputMediaPhoto(photo))
        bot.send_media_group(user_id, photos_list)
    db_table_history(user_id, command_name,
                     hotels_names, datetime.datetime.today(), citi_name)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
