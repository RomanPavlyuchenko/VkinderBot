import re
import time
from random import randrange
from datetime import datetime, timedelta

import vk_api
from vk_api.exceptions import ApiError
from vk_api.longpoll import VkLongPoll


def _get_link(id):
    return f'vk.com/id{id}'


class VkinderBot:
    vk_session = None
    vk = None
    longpoll = None
    vk_user_token = None
    group_id = None

    def __init__(self, group_token, user_token):
        self.vk_session = vk_api.VkApi(token=group_token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session)
        self.vk_user_token = vk_api.VkApi(token=user_token).get_api()
        self.group_id = self.vk.groups.getById()[0]['id']

    def send_msg(self, user_id, message='.', keyboard=None, attachment=''):
        self.vk_session.method('messages.send',
                               {'user_id': user_id,
                                'message': message,
                                'keyboard': keyboard,
                                'attachment': attachment,
                                'random_id': randrange(10 ** 7), })

    def get_user_info(self, user_id) -> dict:
        info = self.vk.users.get(user_ids=(user_id),
                                 fields=('first_name', 'last_name', 'bdate', 'city', 'relation', 'sex'))
        return info[0]

    def get_city_id(self, city_name):
        response = self.vk_user_token.database.getCities(country_id=1, q=city_name)
        if len(response['items']) >= 0:
            return response['items'][0]['id']
        else:
            return None

    # def _search_users(self, params, count=500, offset=0, b_month=0, b_day=0):
    #     result = self.vk_user_token.users.search(
    #         sex=params['gender'],
    #         status=params['status'],
    #         birth_year=params['b_year'],
    #         city=params['city'],
    #         # sort=0,
    #         offset=offset,
    #         birth_month=b_month,
    #         birth_day=b_day,
    #         count=count,
    #         fields=('last_seen')
    #     )
    #     return result


    def search_all_users(self, params, count=500):

        def _search_users(vk, params, count=500, offset=0, b_month=0, b_day=0):
            result = vk.users.search(
                sex=params['gender'],
                status=params['status'],
                birth_year=params['b_year'],
                city=params['city'],
                # sort=0,
                offset=offset,
                birth_month=b_month,
                birth_day=b_day,
                count=count,
                fields=('last_seen')
            )
            return result

        def _search_cycle(vk, params, month=0, day=0, count=500):
            response = _search_users(vk, params, count=count, offset=0)
            searched_users_set = set()
            offset = 0
            while response['items']:
                for item in response['items']:
                    if 'last_seen' in item and item['last_seen']['time'] >= last_online:
                        searched_users_set.add(item['id'])
                offset += offset_incr
                response = _search_users(vk, params, count=count, offset=offset, b_day=day, b_month=month)
            return searched_users_set



        offset_incr = count
        last_online = time.mktime((datetime.now() - timedelta(days=7)).timetuple())

        searched_users_set = set()
        response = _search_users(self.vk_user_token, params=params, count=count, offset=0)

        if response['count'] <= 1000:
            searched_users_set = _search_cycle(self.vk_user_token, params)
        else:

            for month in range(1, 13):
                response = _search_users(self.vk_user_token, params, count=count, b_month=month)
                if response['count'] <= 1000:
                    searched_users_set = searched_users_set.union(_search_cycle(self.vk_user_token, params=params, month=month))
                else:

                    for day in range(1, 32):
                        searched_users_set = searched_users_set.union(_search_cycle(self.vk_user_token, params=params, month=month, day=day))

        return searched_users_set

    def _get_photos(self, user_id, album_id=-6, offset=0):
        response = self.vk_user_token.photos.get(
            owner_id=user_id,
            extended=1,
            count=100,
            offset=offset,
            album_id=album_id
        )
        return response

    def get_most_popular_photo(self, user_id):
        response = self._get_photos(user_id)
        photos = []
        counter = 0
        offset = 0
        while response['items']:
            for photo in response['items']:
                cur_photo = {
                    'id': photo['id'],
                    'owner_id': photo['owner_id'],
                }

                count_comment = 0
                try:
                    count_comment = self.vk_user_token.photos.getComments(
                        owner_id=photo['owner_id'],
                        photo_id=photo['id']
                    )['count']
                    counter += 1
                except ApiError as msg:
                    print(msg)

                cur_photo['popularity'] = photo['likes']['count'] + count_comment
                photos.append(cur_photo)
            offset += 100
            response = self._get_photos(user_id, offset=offset)
        photos = sorted(photos, key=lambda i: i['popularity'])
        return photos[-3:]

    def get_photos_msg(self, user_id, searched_id):
        message = f'{_get_link(searched_id)}'
        attach = ''
        try:
            photos = self.get_most_popular_photo(searched_id)
            for photo in photos:
                attach += f'photo{photo["owner_id"]}_{photo["id"]},'

        except ApiError as msg:
            print(msg)

        return {'msg': message, 'attach': attach}

    def get_last_searched_from_msg(self, user_id):
        msg_history = self.vk.messages.getHistory(user_id=user_id, count=200)
        for msg in msg_history['items']:
            if msg['from_id'] == -self.group_id:
                if re.search('vk\.com\/id[0-9]{1-9}', msg['text']):
                    id = re.search('[0-9]{1-9}', msg['text'])[0]
                    return id
        return None
