from Aggregators.IAggregator import *
import json
import requests


class ShikimoriItemFilter(IItemFilter):
    """Фильтр аниме (Shikimori)"""

    def __init__(self, genres: list = [], order: str = 'ranked', score: int = 1, rating: str = 'none',
                 censored: str = 'true', name: str = "", page: int = 1, limit: int = 50):
        super().__init__()
        self.genres = genres
        self.order = order
        self.score = score
        self.rating = rating
        self.censored = censored
        self.name = name
        self.page = page
        self.limit = limit


class ShikimoriItem(IItem):
    """Аниме (Shikimori)"""

    def __init__(self, name: str = '', genres: list = [], score: int = 0, description: str = '', image_url: str = ''):
        super().__init__()
        self.name = name
        self.genres = genres
        self.score = score
        self.description = description
        self.image_url = image_url


class ShikimoriAggregator(IAggregator):
    """Агрегатор (Shikimori)"""

    def __init__(self):
        super().__init__()
        self.site = 'https://shikimori.one'
        self.client_id = 'P4VOYDWfWYQlhhFRqS8sONg39LAgHGHLRSTMU_1PMeM'
        self.client_secret = 'wno6Ij5zaplABAMFO1exSBQ2VCEY0pBEMJsQStKpr8M'
        self.authorization_code = 'rPXm12xqS9ygdnO438i4kI9iCBDmdGLLK5IaPKas5Iw'
        with open('resources/ShikiToken.json', 'r') as file:
            data = json.load(file)
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']

    def get_name(self) -> str:
        return "Shikimori"

    def get_items(self, item_filter: ShikimoriItemFilter) -> AbstractItemIterator:
        """Получить итератор"""
        return ShikimoriItemIterator(item_filter)

    def get_new_token(self) -> None:
        new_token = requests.post(url=self.site + '/oauth/token',
                                  headers={
                                      "User-Agent": 'Telegram-Waifu'
                                  },
                                  data={
                                      'grant_type': 'refresh_token',
                                      'client_id': self.client_id,
                                      'client_secret': self.client_secret,
                                      'refresh_token': self.refresh_token
                                  }).json()
        self.access_token = new_token['access_token']
        self.refresh_token = new_token['refresh_token']
        with open('resources/ShikiToken.json', 'w') as file:
            json.dump(new_token, file, indent=2)
        return


class ShikimoriItemIterator(AbstractItemIterator):
    """Итератор (Shikimori)"""

    def __init__(self, item_filter: ShikimoriItemFilter):
        AbstractItemIterator.__init__(self)
        self.item_filter = item_filter
        self.item_ids = []

    def get_item(self, shiki: ShikimoriAggregator, idx: int) -> IItem:
        """Получить анимэ по индексу"""
        if self.item_ids == []:
            self.item_ids = self.get_anime_id_list(self, shiki)
        elif idx // 50 + 1 != self.item_filter.page:
            self.item_filter.page = idx // 50 + 1
            self.item_ids = self.get_anime_id_list(self, shiki)

        anime_info = requests.get(url=shiki.site + '/api/animes/' + str(self.item_ids[idx % 50]),
                                  headers={
                                      "User-Agent": 'Telegram-Waifu',
                                      'Authorization': 'Bearer ' + shiki.access_token
                                  })
        # Если токен невалидный, то получаем новый
        if anime_info.status_code == 401:
            shiki.get_new_token()
            anime_info = requests.get(url=shiki.site + '/api/animes/' + str(self.item_ids[idx % 50]),
                                      headers={
                                          "User-Agent": 'Telegram-Waifu',
                                          'Authorization': 'Bearer ' + shiki.access_token
                                      })
        anime_info = anime_info.json()
        genres = []
        for genre in anime_info['genres']:
            genres.append(genre['russian'])
        return ShikimoriItem(anime_info['russian'], genres, anime_info['score'],
                             anime_info['description'], anime_info['image']['original'])

    def get_anime_id_list(self, shiki: ShikimoriAggregator) -> list:
        animes = requests.get(url=shiki.site + '/api/animes',
                              headers={
                                  "User-Agent": 'Telegram-Waifu',
                                  'Authorization': 'Bearer ' + shiki.access_token
                              },
                              params={
                                  'page': self.item_filter.page,
                                  'limit': self.item_filter.limit,
                                  'order': self.item_filter.order,
                                  'score': self.item_filter.score,
                                  'rating': self.item_filter.rating,
                                  'genre': self.item_filter.genres,
                                  'censored': self.item_filter.censored,
                                  'search': self.item_filter.name
                              })
        # Если токен невалидный, то получаем новый
        if animes.status_code == 401:
            shiki.get_new_token()
            animes = requests.get(url=shiki.site + '/api/animes',
                                  headers={
                                      "User-Agent": 'Telegram-Waifu',
                                      'Authorization': 'Bearer ' + shiki.access_token
                                  },
                                  params={
                                      'page': self.item_filter.page,
                                      'limit': self.item_filter.limit,
                                      'order': self.item_filter.order,
                                      'score': self.item_filter.score,
                                      'rating': self.item_filter.rating,
                                      'genre': self.item_filter.genres,
                                      'censored': self.item_filter.censored,
                                      'search': self.item_filter.name
                                  })
        animes = animes.json()
        # Сохраняем id аниме в список
        animes_id = []
        for anime in animes:
            animes_id.append(anime['id'])
        return animes_id