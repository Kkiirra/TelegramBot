import sqlite3
from typing import Union


def read_data_base(command: str) -> Union[str, list]:
    """A function to read the database from the data and pass it as a list of tuples,
    where command selected table column"""
    try:
        sqlite_connection = sqlite3.connect('db/database.db')
        cursor = sqlite_connection.cursor()

        sqlite_select_query = f"""{command}"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()

        cursor.close()
        sqlite_connection.close()
        return records
    except sqlite3.Error:
        return False


def db_table_commands(hotel_name: str, price: float, hotel_id: int, street: str, center_distance: float,
                      citi_name: str, hotels_url: str) -> None:
    """ A function that connects to the database and passes arguments to the table columns of them:
    hotel_name - Hotel name
    price - Hotel price
    hotel_id - hotel ID for the subsequent display of photos
    street - hotel street
    center - Distance to city center """

    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO users_data (hotel_name, price, hotel_id, street, center_distance, '
                   'citi_name, hotels_url) '
                   'VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (hotel_name, price, hotel_id, street, center_distance, citi_name, hotels_url))
    conn.commit()


def db_table_history(user_id: int, command_name: str, user_request: str, date: str, citi_name: str) -> None:
    """ A function that connects to the database and passes arguments to the table columns of them:
    user_id - Hotel ID
    command_name - Command name
    user_request - User request
    date - Date
    city_name - City name """

    conn = sqlite3.connect('db/database.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('INSERT INTO history_table (user_id, command_name, user_request, date, citi_name) '
                   'VALUES (?, ?, ?, ?, ?)',
                   (user_id, command_name, user_request, date, citi_name))
    conn.commit()


def hotels_without_photos(users_data: dict, user_id: int) -> Union[bool, tuple]:
    """A function that queries the database to display information about the hotel without photos
    users_data - Dictionary with local information
    user_id - User ID"""
    maximum_hotels, citi_name, sorted_funct = users_data[user_id]['hotels_max'], \
                                              users_data[user_id]['citi_name'],  \
                                              users_data[user_id]['sorted_funct']
    sql_response = read_data_base(f'SELECT hotel_name, price, street, center_distance, hotel_id FROM users_data '
                                  f'WHERE citi_name="{citi_name}" '
                                  f'ORDER BY price {sorted_funct} LIMIT "{maximum_hotels}"')

    return sql_response


def hotels_with_photos(users_data: dict, user_id: int) -> Union[bool, tuple]:
    """A function that makes a query to the database to display information about hotels with photos
    users_data - Dictionary with information
    user_id - User ID"""
    maximum_hotels, citi_name, sorted_funct = users_data[user_id]['hotels_max'], \
                                              users_data[user_id]['citi_name'],  \
                                              users_data[user_id]['sorted_funct']
    sql_response = read_data_base(f'SELECT hotel_name, price, street, center_distance, hotels_url, hotel_id '
                                  f'FROM users_data '
                                  f'WHERE citi_name="{citi_name}" '
                                  f'ORDER BY price {sorted_funct} LIMIT "{maximum_hotels}"')

    return sql_response


def bestdeal_with_photos(users_data: dict, user_id: int) -> Union[bool, tuple]:
    """A function that makes a query to the database to display information about the hotel with photos
    and with data set by the user
    users_data - Dictionary with local information
    user_id - User ID"""
    first_price, second_price = \
        users_data[user_id]['prices'][0], users_data[user_id]['prices'][1]

    first_distance, second_distance = \
        users_data[user_id]['distance'][0], users_data[user_id]['distance'][1]

    maximum_hotels, citi_name, sorted_funct = users_data[user_id]['hotels_max'], \
                                              users_data[user_id]['citi_name'],  \
                                              users_data[user_id]['sorted_funct']

    sql_response = read_data_base(f'SELECT hotel_name, price, street, center_distance, hotels_url, hotel_id '
                                  f'FROM users_data '
                                  f'WHERE citi_name="{citi_name}" '
                                  f'and price >= "{first_price}" and price <= "{second_price}"'
                                  f'and center_distance >= "{first_distance}" and '
                                  f'center_distance <= "{second_distance}" LIMIT "{maximum_hotels}"')

    return sql_response


def bestdeal_without_photos(users_data: dict, user_id: int) -> Union[bool, tuple]:
    """A function that queries the database to display information about the hotel without photos
    and with data set by the user
    users_data - Dictionary with local information
    user_id - User ID"""
    first_price, second_price = \
        users_data[user_id]['prices'][0], users_data[user_id]['prices'][1]
    first_distance, second_distance = \
        users_data[user_id]['distance'][0], users_data[user_id]['distance'][1]
    citi_name = users_data[user_id]['citi_name']
    maximum_hotels = users_data[user_id]['hotels_max']
    sql_response = read_data_base(f'SELECT hotel_name, price, street, center_distance, hotel_id FROM users_data '
                                  f'WHERE citi_name="{citi_name}" '
                                  f'and price >= "{first_price}" and price <= "{second_price}"'
                                  f'and center_distance >= "{first_distance}" and '
                                  f'center_distance <= "{second_distance}" LIMIT "{maximum_hotels}"')
    return sql_response
