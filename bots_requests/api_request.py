import requests
import json
import logging
from decouple import config
from typing import Union
from db.database_sql import db_table_commands


class Request:
    """A class that takes the name of the city as input and then sorts the API request"""

    def __init__(self, citi_name: str, user_id: int) -> None:
        self.citi = citi_name
        self.user_id = user_id
        self.headers = {
            'x-rapidapi-host': 'hotels4.p.rapidapi.com',
            'x-rapidapi-key': config('RAPIDAPI_KEY')
        }

    """ A function that makes a request to the server based on the name of the city, as well as
    simultaneously checks if the DestinationID dictionary exists for the given city for further sorting """

    def search_dict(self) -> Union[bool, str]:
        url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
        querystring = {'query': self.citi}
        response = requests.request('GET', url, headers=self.headers, params=querystring)
        data = json.loads(response.text)
        if data['suggestions'][0]['entities']:
            return data['suggestions'][0]['entities'][0]['destinationId']
        else:
            logging.info(f'function: search_dict(Request)'
                         f'\nuser: {self.user_id}'
                         f'\ncommand: get request for rapidapi')
            return False

    def take_dict_with_hotels(self) -> Union[bool, list]:
        """A function that, in the case of a positive response from the search_dict function, adds Destination_id to
        a dictionary for a GET properties/list request for subsequent sorting of the hotels themselves """
        properties_url = 'https://hotels4.p.rapidapi.com/properties/list'
        try:
            dest_ID = self.search_dict()
            property_querystring = {
                'destinationId': dest_ID,
                'pageNumber': '1',
                'pageSize': '25',
                'checkIn': '2020-01-08',
                'checkOut': '2020-01-15',
                'adults1': '1',
                'locale': 'ru_RU'
            }
            response = requests.request('GET', properties_url, headers=self.headers, params=property_querystring)
            property_dats = json.loads(response.text)
            return property_dats['data']['body']['searchResults']['results']
        except Exception as e:
            logging.info(f'function: take_dict_with_hotels(Request)'
                         f'\nuser: {self.user_id}'
                         f'\ncommand: take dict with hotels {e}')

    def sort_dict_hotels(self) -> Union[bool, list]:
        """ A function that checks whether the result sub dictionary contains the ratePlan and address
        sub dictionaries, because that not all dictionaries have these parameters """
        sort_api_list = list()
        try:
            dict_with_hotels = self.take_dict_with_hotels()
            for index in dict_with_hotels:
                if 'ratePlan' in index and 'streetAddress' in index['address']:
                    sort_api_list.append(index)
            return sort_api_list

        except Exception as e:
            logging.info(f'function: sort_dict_hotels(Request)'
                         f'\nuser: {self.user_id}'
                         f'\ncommand: sorting dict with hotels {e}')

    def sorted_hotels(self) -> bool:
        """ A function that already comes with an unsorted dictionary with the parameters we need.
        And also generates a list of links for users in video photos and names of travel hotels. Maximum photo
        this is 5, because this is more than enough for familiarization and does not overload the API, set for the test
        one"""
        try:
            sort_dict_hotels = self.sort_dict_hotels()
            hotels_names = str()
            for index in sort_dict_hotels:
                hotel_name, price, hotel_id, street, center_distance = index['name'], \
                   index['ratePlan']['price'][
                           'exactCurrent'], \
                   index['id'], index['address'][
                       'streetAddress'], \
                   index['landmarks'][0]['distance'].split()[0]
                hotels_names += hotel_name + ' '
                url_for_hotel = str()
                for hotels_images in self.photo_req(hotel_id)[:5]:
                    url_for_hotel += hotels_images['baseUrl'].replace('{size}', 'b') + ' '

                db_table_commands(hotel_name, price, hotel_id, street, center_distance,
                                  self.citi, url_for_hotel)
            return sort_dict_hotels
        except Exception as e:
            logging.info(f'function: sorted_hotels(Request)'
                         f'\nuser: {self.user_id}'
                         f'\ncommand: write the hotel information in database {e}')
            return False

    def photo_req(self, hotel_id) -> Union[list, bool]:
        """ A function that takes a hotel_id from the database as input and makes a request for a photo in
        properties/get-hotel-photos, then returns a link as a string. """
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring_photo = {'id': f'{hotel_id}'}
        response = requests.request("GET", url, headers=self.headers, params=querystring_photo)
        property_dats = json.loads(response.text)
        if 'hotelImages' in property_dats:
            return property_dats['hotelImages']
