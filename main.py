import telebot
import config
from telebot import types
from PIL import Image
from urllib.request import urlopen
from enum import Enum

from Aggregators.ShikimoriAggregator import ShikimoriItemFilter
from FavoriteItemList import AlreadyExistException
from ServerApplication import ServerApplication

# серверное приложение
app = ServerApplication()

id = 0
bot = telebot.TeleBot(config.CFG['TOKEN'])

curMenu = config.CurMenu

ratingList = config.ratingList
assessmentList = config.assessmentList
typeAnimeList = config.typeAnimeList
typeMangaList = config.typeMangaList
keyGenre = None

listOfSelectedGenres = []
ratingSelected = []
assesmentSelected = []
typeSelected = []


class TypeSearch(Enum):
    Anime = 1
    Manga = 2


# получаем список жанров для аниме и манги из всего списка (находится в config)
def getGenresAnimeOrMangu():
    items = config.genresList
    genresAnime = {}
    genresMangu = {}
    for item in items:
        if item['kind'] == "anime":
            # genresAnime[item['russian']] = item['id']
            genresAnime[str(item['id'])] = item['russian']
        elif item['kind'] == "manga":
            # genresMangu[item['russian']] = item['id']
            genresMangu[str(item['id'])] = item['russian']
    return genresAnime, genresMangu


genresAnime, genresMangu = getGenresAnimeOrMangu()


# получить меню для Фильтра
def getFilterMenu(type):
    key = types.InlineKeyboardMarkup()
    if type is TypeSearch.Anime:
        but_1 = types.InlineKeyboardButton(text="Жанры", callback_data="GenresAnime")
        but_2 = types.InlineKeyboardButton(text="Рейтинг", callback_data="Rating")
        but_3 = types.InlineKeyboardButton(text="Оценка", callback_data="Assesment")
        but_4 = types.InlineKeyboardButton(text="Тип", callback_data="TypeMenu")
        but_5 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="Anime")
        but_6 = types.InlineKeyboardButton(text="Применить фильтр", callback_data="ApplyFilterAnime")
        but_8 = types.InlineKeyboardButton(text="Сбросить фильтр", callback_data="ResetFilter")
        key.row(but_1)
        key.row(but_2)
    elif type is TypeSearch.Manga:
        but_1 = types.InlineKeyboardButton(text="Жанры", callback_data="GenresManga")
        but_3 = types.InlineKeyboardButton(text="Оценка", callback_data="Assesment")
        but_4 = types.InlineKeyboardButton(text="Тип", callback_data="TypeMenu")
        but_5 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="Manga")
        but_6 = types.InlineKeyboardButton(text="Применить фильтр", callback_data="ApplyFilterManga")
        but_8 = types.InlineKeyboardButton(text="Сбросить фильтр", callback_data="ResetFilter")
        key.row(but_1)
    but_7 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
    key.row(but_3)
    key.row(but_4)
    key.row(but_5, but_7)
    key.row(but_6, but_8)
    return key


# получить меню жанров
def getGenresMenu(genresList, type):
    key = types.InlineKeyboardMarkup()
    count_col = 0
    but_row = []
    for id, item in genresList.items():
        if count_col < 2:
            but_row.append(types.InlineKeyboardButton(text=item, callback_data=id))
            count_col += 1
        elif count_col == 2:
            but_row.append(types.InlineKeyboardButton(text=item, callback_data=id))
            count_col = 0
            key.row(but_row[0], but_row[1], but_row[2])
            but_row = []
    if count_col == 1:
        key.add(but_row[0])
    elif count_col == 2:
        key.row(but_row[0], but_row[1])

    if type is TypeSearch.Anime:
        but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterAnime")
    elif type is TypeSearch.Manga:
        but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterManga")
    but_2 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
    key.row(but_1, but_2)
    return key


# сброс фильтра для пользователя при выходе из меню Фильтр
def zeroFilter(user):
    user.cur_menu = curMenu.SearchFalse
    user.cur_filter = ShikimoriItemFilter()
    user.cur_filter.genres = []


# получаем меню Новинок для аниме
def getNovinkiMenuAnime(name, genres, score, description, siteInfo, siteVideo):
    key = types.InlineKeyboardMarkup()
    # если ссылка существует
    if siteVideo is not None:
        but_1 = types.InlineKeyboardButton(text="Смотреть", url=siteVideo)
        key.row(but_1)
    but_2 = types.InlineKeyboardButton(text="Подробнее", url=siteInfo)
    but_3 = types.InlineKeyboardButton(text="В избранное", callback_data="ToFavouritesAnime")
    but_4 = types.InlineKeyboardButton(text="Предыдущее", callback_data="PrevAnime")
    but_5 = types.InlineKeyboardButton(text="Следующее", callback_data="NextAnime")
    but_6 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="Anime")
    but_7 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
    genres_str = ""
    for genre in genres:
        genres_str += genre + " | "
    descript = "*Название:* " + name + "\n*Жанры:* " + genres_str + "\n*Рейтинг:* " + str(
        score) + "\n\n*Описание:* " + description[0:800] + "..."

    key.row(but_2)
    key.row(but_3)
    key.row(but_4, but_5)
    key.row(but_6)
    key.row(but_7)
    return key, descript


# получаем меню Поиска по названию для аниме
def searchNameMenuAnime(user, name, genres, score, description, siteInfo, siteVideo):
    key = types.InlineKeyboardMarkup()
    print(siteVideo)
    # если ссылка существует
    for url in siteVideo:
        if url == '':
            continue
        but_1 = types.InlineKeyboardButton(text="См. на " + url[0], url=url[1])
        key.row(but_1)

    but_3 = types.InlineKeyboardButton(text="В избранное", callback_data="ToFavouritesAnime")
    key.row(but_3)

    if user.cur_iterator.has_prev():
        but_4 = types.InlineKeyboardButton(text="Предыдущее", callback_data="PrevAnime")
        key.row().add(but_4)

    if user.cur_iterator.has_next():
        but_5 = types.InlineKeyboardButton(text="Следующее", callback_data="NextAnime")
        key.row().add(but_5)

    if user.cur_aggregator == app.shikimori_anime_agg:
        if user.cur_menu == curMenu.SearchFilter:
            but_6 = types.InlineKeyboardButton(text="Вернуться к фильтрам", callback_data="FilterAnime")
        else:
            but_6 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="Anime")
    else:
        if user.cur_menu == curMenu.SearchFilter:
            but_6 = types.InlineKeyboardButton(text="Вернуться к фильтрам", callback_data="FilterManga")
        else:
            but_6 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="Manga")

    but_7 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
    genres_str = ""
    for genre in genres:
        genres_str += genre + " | "

    if description is None:
        description = "Нет описания"

    descript = "*Название:* " + name + "\n*Жанры:* " + genres_str + "\n*Рейтинг:* " + str(
        score) + "\n\n*Описание:* " + description[0:800] + "..."

    if siteInfo is not None:
        but_2 = types.InlineKeyboardButton(text="Подробнее", url=siteInfo)
        key.row(but_2)

    key.row(but_6)
    key.row(but_7)
    return key, descript


# получаем изображение с сайта, изменяем его до нужного размера (чтоб в телеграмме красиво смотрелось)
def getImage(image):
    basewidth = 1200
    baseheight = 800
    # image = Image.open(urlopen(url))
    if image.size[1] < baseheight:
        ratio = (baseheight / float(image.size[1]))
        width = int((float(image.size[0]) * float(ratio)))
        image = image.resize((width, baseheight), Image.ANTIALIAS)
    image_fon = Image.new('RGB', (basewidth, image.size[1]), (255, 255, 255))
    image_fon.paste(image, (round((basewidth - image.size[0]) / 2), 0))
    return image_fon


# получение аниме/манги по фильтрам
def getItems(user, message, anime_info):
    if anime_info is not None:  # если введенное название нашлось
        img = Image.open(urlopen(anime_info.image_url))
        image = getImage(img)
        key, descript = searchNameMenuAnime(user, anime_info.name, anime_info.genres, anime_info.score,
                                            anime_info.description, anime_info.site_url,
                                            anime_info.video_url)  # тут так же для манги
        # bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id, media=types.InputMediaPhoto(image))
        # bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=descript, parse_mode='Markdown', reply_markup=key)

        bot.delete_message(message.chat.id, user.cur_msg.message_id)
        user.cur_msg = bot.send_photo(message.chat.id, image, caption=descript, parse_mode='Markdown', reply_markup=key)
        # bot.send_photo(message.chat.id, image, caption=descript,reply_markup=key)
    else:
        key = types.InlineKeyboardMarkup()
        if user.cur_menu == curMenu.SearchFilter:
            if user.cur_aggregator == app.shikimori_anime_agg:
                but_2 = types.InlineKeyboardButton(text="Назад к фильтрам", callback_data="FilterAnime")
            else:
                but_2 = types.InlineKeyboardButton(text="Назад к фильтрам", callback_data="FilterManga")
        else:
            if user.cur_aggregator == app.shikimori_anime_agg:
                but_2 = types.InlineKeyboardButton(text="Назад", callback_data="Anime")
            else:
                but_2 = types.InlineKeyboardButton(text="Назад", callback_data="Manga")
        key.row(but_2)
        image = Image.open(r'static\searchnameAnime.jpg')
        getImage(image)
        bot.delete_message(message.chat.id, user.cur_msg.message_id)
        user.cur_msg = bot.send_photo(message.chat.id, image, caption="Ничего не найдено(", reply_markup=key)


# Описание всех выбранных фильтров
def getCaptionFiltres(user):
    if user.cur_filter.genres == [] and user.cur_filter.kind == '' and user.cur_filter.rating == '' and user.cur_filter.score == 1:
        capt = "Вы еще ничего не выбрали\nПора это сделать!"
    elif user.cur_aggregator == app.shikimori_anime_agg:
        capt = "*Вы выбрали:*\n*Жанры:* " + ', '.join(list(map(lambda x: genresAnime[x], user.cur_filter.genres))) + \
               "\n*Оценка:* " + str(user.cur_filter.score) + \
               "\n*Рейтинг:* " + user.cur_filter.rating + \
               "\n*Тип:* " + user.cur_filter.kind
    elif user.cur_aggregator == app.shikimori_manga_agg:
        capt = "*Вы выбрали:*\n*Жанры:* " + ', '.join(list(map(lambda x: genresMangu[x], user.cur_filter.genres))) + \
               "\n*Оценка:* " + str(user.cur_filter.score) + \
               "\n*Тип:* " + user.cur_filter.kind
    return capt


'''
def getAnime():
    name = "Виви: Песнь флюоритового глаза / Vivy: Fluorite Eye's Song"
    genres = ["Экшен", "Музыка", "Фантастика", "Триллер"]
    score = 8.47
    description = "Добро пожаловать в Ниаленд — выставку искусственного интеллекта и парк, \
    объединивший в себе мечты, надежды и науку. Именно здесь была создана Дива — первый в истории \
    автономный искин-гуманоид, полностью подобный человеку, но существующий только для \
    одной-единственной цели — петь песни и дарить своим слушателям счастье. Не сыскав \
    популярности, Дива Виви, как её назвала одна из первых поклонниц, 12-летняя девочка Момока, \
    продолжала выходить на сцену. Каждый раз она стремилась вложить в свои песни душу, \
    до тех пор пока её размеренному существованию внезапно не пришел конец. Посреди дня к ней \
    подключается Мацумото — таинственный ИИ, представившийся именем своего создателя. По его словам, \
    он прибыл из будущего с задачей предотвратить войну между человечеством и искусственным интеллектом, \
    случившуюся сто лет спустя. Какое будущее ждёт этот мир? Правду ли говорит Мацумото? Сможет ли Дива \
    отказаться от своего первоначального назначения ради спасения человечества? Так начинается история Виви длиной в сотню лет."
    image = "https://nyaa.shikimori.one/system/animes/original/46095.jpg?1620639091"
    siteInfo = "https://shikimori.one/animes/46095-vivy-fluorite-eye-s-song"
    siteVideo = 'https://www.wakanim.tv/ru/v2/catalogue/show/1292/vivi-pesn-flyuoritovogo-glaza-vivy-fluorite-eyes-song'
    return name, genres, score, description, image, siteInfo, siteVideo

def getAnimeForSearchName():
    name = "Ходячий замок / Howl no Ugoku Shiro"
    genres = ["Приключения", "Драма", "Фэнтези", "Романтика"]
    score = 8.67
    description = "Восемнадцатилетняя шляпница Софи ведёт тихую и ничем не примечательную городскую жизнь. Однако \
    типичный её распорядок рушится, когда в окрестностях города объявляется Ходячий замок Хаула — колдуна, \
    заключившего сделку с демоном огня Кальцифером и носящего дурную славу «похитителя» девичьих сердец. \
    Вечером после работы очаровательный голубоглазый красавец, оказавшийся, как ни странно, самим Хаулом, \
    спасает Софи от приставаний двух солдафонов, и девушка тут же влюбляется в своего спасителя. Однако \
    итогом их встречи становится проклятие Ведьмы Пустоши, превратившее Софи в девяностолетнюю старуху. \
    Теперь Софи вынуждена покинуть родной дом и отправиться на поиски ведьмы, просить ту снять проклятие. \
    Дорога же приводит «девушку» к тому самому Ходячему замку, где у неё и появляется шанс начать новую \
    жизнь... "
    image = "https://kawai.shikimori.one/system/animes/original/431.jpg?1617279661"
    siteInfo = "https://shikimori.one/animes/431-howl-no-ugoku-shiro"
    siteVideo = 'https://hd.kinopoisk.ru/film/4c4086bb916d4d01b984e2d5a8a63005/' #хе-хе, ссылка на кинопоиск
    return name, genres, score, description, image, siteInfo, siteVideo
'''


# второй аргумент = true, если мы к главной странице возвращаемся, и false при старте бота
def setMainPage(user, message, edit):
    photo = open('static/avatarka.jpg', 'rb')
    key = types.InlineKeyboardMarkup()
    but_1 = types.InlineKeyboardButton(text="Аниме", callback_data="Anime")
    but_2 = types.InlineKeyboardButton(text="Манга", callback_data="Anime") # todo: remove
    #but_2 = types.InlineKeyboardButton(text="Манга", callback_data="Manga")
    key.add(but_1, but_2)
    if edit:
        bot.edit_message_media(chat_id=message.chat.id, message_id=message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=message.chat.id, message_id=message.message_id,
                                 caption="Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный скрасить твое одиночество.\nЧто желаешь посмотреть?".format(
                                     message.from_user, bot.get_me()), parse_mode='html', reply_markup=key)
    else:
        user.cur_msg = bot.send_photo(message.chat.id, photo,
                                      caption="Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот, созданный скрасить твое одиночество.\nЧто желаешь посмотреть?".format(
                                          message.from_user, bot.get_me()), parse_mode='html', reply_markup=key)
        # bot.send_photo(message.chat.id, photo, caption="Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный скрасить твое одиночество.\nЧто желаешь посмотреть?".format(message.from_user, bot.get_me()), parse_mode='html', reply_markup=key)


@bot.message_handler(commands=["start"])
def inline(message):
    user = app.get_user_session(message.from_user.id)
    setMainPage(user, message, False)


# обработка отправки сообщения пользователя
@bot.message_handler(content_types=['text'])
def send_text(message):
    user = app.get_user_session(message.from_user.id)
    # если мы в "Поиск по названию"
    if user.cur_menu == curMenu.SearchName:
        user.cur_filter.name = message.text.lower()
        user.cur_iterator = user.cur_aggregator.get_items(user.cur_filter)
        # получили результат поиска
        anime_info = user.cur_iterator.get_item()
        getItems(user, message, anime_info)
        user.cur_menu = curMenu.SearchFalse
    else:
        bot.send_message(message.chat.id, "Не стоит спамить!\nНачни заново")
        bot.delete_message(message.chat.id, user.cur_msg.message_id)
        setMainPage(user, message, False)


@bot.callback_query_handler(func=lambda c: True)
def inline(c):
    user = app.get_user_session(c.from_user.id)

    # перешли по кнопке "Аниме"
    if c.data == 'Anime':
        user.cur_filter = ShikimoriItemFilter()
        user.cur_aggregator = app.shikimori_anime_agg

        zeroFilter(user)

        photo = Image.open(r'static\animeMenu.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        but_1 = types.InlineKeyboardButton(text="Поиск по названию", callback_data="SearchByNameAnime")
        but_2 = types.InlineKeyboardButton(text="Поиск по фильтру", callback_data="FilterAnime")
        but_3 = types.InlineKeyboardButton(text="Для тебя!", callback_data="AdviceAnime")
        but_4 = types.InlineKeyboardButton(text="Новинки", callback_data="NewAnime")
        but_6 = types.InlineKeyboardButton(text="Избранное", callback_data="FavouritesAnime")
        but_5 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="BackMainPage")
        key.row(but_1)
        key.row(but_2)
        key.row(but_3)
        key.row(but_4)
        key.row(but_6)
        key.row(but_5)

        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Чем могу помочь?",
                                 reply_markup=key)
        # bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text="Выбери", reply_markup=key)

    # перешли по кнопке "Манга"
    if c.data == 'Manga':
        user.cur_filter = ShikimoriItemFilter()

        zeroFilter(user)

        user.cur_aggregator = app.shikimori_manga_agg
        photo = Image.open(r'static\mangaMenu.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        but_1 = types.InlineKeyboardButton(text="Поиск по названию", callback_data="SearchByNameManga")
        but_2 = types.InlineKeyboardButton(text="Поиск по фильтру", callback_data="FilterManga")
        but_3 = types.InlineKeyboardButton(text="Для тебя!", callback_data="AdviceManga")
        but_4 = types.InlineKeyboardButton(text="Новинки", callback_data="NewManga")
        but_6 = types.InlineKeyboardButton(text="Избранное", callback_data="FavouritesManga")
        but_5 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="BackMainPage")
        key.row(but_1)
        key.row(but_2)
        key.row(but_3)
        key.row(but_4)
        key.row(but_6)
        key.row(but_5)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Чем могу помочь?",
                                 reply_markup=key)
        # bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text="Выбери", reply_markup=key)

    # кнопка "Вернуться на главную"
    if c.data == "BackMainPage":
        setMainPage(user, c.message, True)

    '''
    # кнопка "Новинки" для Аниме
    if c.data == "NewAnime":
      name, genres, score, description, url, siteInfo, siteVideo = getAnime()
      img = Image.open(urlopen(url))
      image = getImage(img)
      key, descript = getNovinkiMenuAnime(name, genres, score, description, siteInfo, siteVideo)
      bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id, media=types.InputMediaPhoto(image))
      bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=descript, parse_mode='Markdown', reply_markup=key)

    # кнопка "Новинки" для Манги
    if c.data == "NewManga":
      name, genres, score, description, url, siteInfo, siteVideo = getAnime() # тут для манги написать функцию
      img = Image.open(urlopen(url))
      image = getImage(img)
      key, descript = getNovinkiMenuAnime(name, genres, score, description, siteInfo, siteVideo) # тут так же для манги
      bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id, media=types.InputMediaPhoto(image))
      bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=descript, parse_mode='Markdown', reply_markup=key)
    '''
    # поиск по названию аниме
    if c.data == "SearchByNameAnime":
        # global searchName
        # searchName = True
        user.cur_menu = curMenu.SearchName
        photo = Image.open(r'static\searchnameAnime.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Введи название:",
                                 reply_markup=key)
        key = types.KeyboardButton

    # поиск по названию аниме
    if c.data == "SearchByNameManga":
        # searchName = True
        user.cur_menu = curMenu.SearchName
        photo = Image.open(r'static\searchnameAnime.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Введи название:",
                                 reply_markup=key)
        key = types.KeyboardButton

    # избранное для аниме
    if c.data == "ToFavouritesAnime":
        anime_info = user.cur_iterator.get_item()
        try:
            user.favorite_list.add_item(anime_info)
            print("добавили в избранное: " + anime_info.name)
            bot.answer_callback_query(c.id, show_alert=True, text="Добавлено в избранное")
        except AlreadyExistException as ex:
            bot.answer_callback_query(c.id, show_alert=True, text="Уже в избранном.")

    # просмотреть избранное для аниме
    if c.data == "FavouritesAnime":
        bot.answer_callback_query(c.id, show_alert=True, text="В избранном ничего нет.")
    # посмотреть избранное для манги
    if c.data == "FavouritesManga":
        bot.answer_callback_query(c.id, show_alert=True, text="В избранном ничего нет.")

    if c.data == "NewAnime":
        bot.answer_callback_query(c.id, show_alert=True, text="Новинок пока нет. Заходи позже!")
    if c.data == "AdviceAnime":
        bot.answer_callback_query(c.id, show_alert=True, text="Пока нечего тебе посоветовать.")

    # фильтры для аниме
    if c.data == "FilterAnime":
        user.cur_menu = curMenu.SearchFilter
        photo = Image.open(r'static\filter.jpg')
        photo = getImage(photo)
        key = getFilterMenu(TypeSearch.Anime)
        capt = getCaptionFiltres(user)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=capt,
                                 parse_mode='Markdown', reply_markup=key)

    # фильтры для манги
    if c.data == "FilterManga":
        user.cur_menu = curMenu.SearchFilter

        photo = Image.open(r'static\filterManga.jpg')
        photo = getImage(photo)
        key = getFilterMenu(TypeSearch.Manga)
        capt = getCaptionFiltres(user)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=capt,
                                 parse_mode='Markdown', reply_markup=key)

    # жанры для аниме
    if c.data == "GenresAnime":
        photo = Image.open(r'static\genres.jpg')
        photo = getImage(photo)
        global keyGenre
        keyGenre = getGenresMenu(genresAnime, TypeSearch.Anime)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                 caption="*Выбранные жанры:* " + ', '.join(
                                     list(map(lambda x: genresAnime[x], user.cur_filter.genres))),
                                 parse_mode='Markdown', reply_markup=keyGenre)

    # жанры для манги
    if c.data == "GenresManga":
        photo = Image.open(r'static\genresMangu.jpg')
        photo = getImage(photo)
        keyGenre = getGenresMenu(genresMangu, TypeSearch.Manga)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                 caption="*Выбранные жанры:* " + ', '.join(
                                     list(map(lambda x: genresMangu[x], user.cur_filter.genres))),
                                 parse_mode='Markdown', reply_markup=keyGenre)

    # при выборе жанра
    if c.data in genresAnime or c.data in genresMangu:

        # если жанр уже есть в выбранных, то не добавляем
        if c.data not in user.cur_filter.genres:
            if user.cur_aggregator == app.shikimori_anime_agg:
                bot.answer_callback_query(c.id, show_alert=True,
                                          text="Выбран жанр: " + genresAnime[c.data] + " с id = " + c.data)
                user.cur_filter.genres.append(c.data)
                bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                         caption="*Выбранные жанры:* " + ', '.join(
                                             list(map(lambda x: genresAnime[x], user.cur_filter.genres))),
                                         parse_mode='Markdown', reply_markup=keyGenre)
            elif user.cur_aggregator == app.shikimori_manga_agg:
                bot.answer_callback_query(c.id, show_alert=True,
                                          text="Выбран жанр: " + genresMangu[c.data] + " с id = " + c.data)
                user.cur_filter.genres.append(c.data)
                bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id,
                                         caption="*Выбранные жанры:* " + ', '.join(
                                             list(map(lambda x: genresMangu[x], user.cur_filter.genres))),
                                         parse_mode='Markdown', reply_markup=keyGenre)

    # меню для выбора Рейтинга
    if c.data == "Rating":
        photo = Image.open(r'static\ratingAnime.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        for item, id in ratingList.items():
            but = types.InlineKeyboardButton(text=item, callback_data=item)
            key.row(but)
        if user.cur_aggregator == app.shikimori_anime_agg:
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterAnime")
        elif user.cur_aggregator == app.shikimori_manga_agg:
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterManga")
        but_2 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
        key.row(but_1, but_2)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Выбери рейтинг",
                                 reply_markup=key)

    # при выборе рейтинга
    if c.data in ratingList:
        bot.answer_callback_query(c.id, show_alert=True,
                                  text="Выбран рейтинг: " + c.data + " с id = " + str(ratingList[c.data]))

        user.cur_filter.rating = ratingList[c.data]

        ratingSelected.append(c.data)

    # меню для выбора Оценки
    if c.data == "Assesment":
        photo = Image.open(r'static\assesment.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        for item, id in assessmentList.items():
            but = types.InlineKeyboardButton(text=item, callback_data=item)
            key.row(but)
        if user.cur_aggregator == app.shikimori_anime_agg:
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterAnime")
        elif user.cur_aggregator == app.shikimori_manga_agg:
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterManga")
        but_2 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
        key.row(but_1, but_2)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Выбери оценку:",
                                 reply_markup=key)

    # при выборе оценки
    if c.data in assessmentList:
        bot.answer_callback_query(c.id, show_alert=True,
                                  text="Выбрана оценка: " + c.data + " с id = " + str(assessmentList[c.data]))
        user.cur_filter.score = assessmentList[c.data]
        assesmentSelected.append(c.data)

    # меню для выбора Типы для аниме
    if c.data == "TypeMenu":
        photo = Image.open(r'static\typeAnime.jpg')
        photo = getImage(photo)
        key = types.InlineKeyboardMarkup()
        if user.cur_aggregator == app.shikimori_anime_agg:
            lst = typeAnimeList
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterAnime")
        elif user.cur_aggregator == app.shikimori_manga_agg:
            lst = typeMangaList
            but_1 = types.InlineKeyboardButton(text="Вернуться назад", callback_data="FilterManga")
        for item, id in lst.items():
            but = types.InlineKeyboardButton(text=item, callback_data=item)
            key.row(but)
        but_2 = types.InlineKeyboardButton(text="На главную", callback_data="BackMainPage")
        key.row(but_1, but_2)
        bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id,
                               media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption="Выбери тип:",
                                 reply_markup=key)

    # при выборе Типа
    if c.data in typeAnimeList or c.data in typeMangaList:
        if user.cur_aggregator == app.shikimori_anime_agg:
            bot.answer_callback_query(c.id, show_alert=True,
                                      text="Выбран Тип: " + c.data + " с id = " + str(typeAnimeList[c.data]))
            user.cur_filter.kind = typeAnimeList[c.data]
        elif user.cur_aggregator == app.shikimori_manga_agg:
            bot.answer_callback_query(c.id, show_alert=True,
                                      text="Выбран Тип: " + c.data + " с id = " + str(typeMangaList[c.data]))
            user.cur_filter.kind = typeMangaList[c.data]
        typeSelected.append(c.data)

    # Применить фильтры
    if c.data == "ApplyFilterAnime" or c.data == "ApplyFilterManga":
        user.cur_iterator = user.cur_aggregator.get_items(user.cur_filter)
        # получили результат поиска
        anime_info = user.cur_iterator.get_item()
        getItems(user, c.message, anime_info)
        # bot.answer_callback_query(c.id, show_alert=True, text= "Жанры: " + ', '.join(listOfSelectedGenres) + "\nРейтинг: " + ''.join(ratingSelected) + "\nТип: " + ''.join(typeSelected) + "\nОценка: " + ''.join(assesmentSelected))

    # Сбросить фильтры
    if c.data == "ResetFilter":
        user.cur_filter = ShikimoriItemFilter()
        user.cur_filter.genres = []
        photo = Image.open(r'static\filter.jpg')
        photo = getImage(photo)
        if user.cur_aggregator == app.shikimori_anime_agg:
            key = getFilterMenu(TypeSearch.Anime)
        else:
            key = getFilterMenu(TypeSearch.Manga)
        capt = getCaptionFiltres(user)
        # bot.edit_message_media(chat_id=c.message.chat.id, message_id=c.message.message_id, media=types.InputMediaPhoto(photo))
        bot.edit_message_caption(chat_id=c.message.chat.id, message_id=c.message.message_id, caption=capt,
                                 parse_mode='Markdown', reply_markup=key)

    # при запросе следующего аниме
    if c.data == "NextAnime":
        # bot.answer_callback_query(c.id, show_alert=True, text="Хотим получить следующее аниме")
        # получили результат поиска
        anime_info = user.cur_iterator.get_next_item()
        getItems(user, c.message, anime_info)

    # при запросе следующего аниме
    if c.data == "PrevAnime":
        # bot.answer_callback_query(c.id, show_alert=True, text="Хотим получить предыдущее аниме")
        # получили результат поиска
        anime_info = user.cur_iterator.get_prev_item()
        getItems(user, c.message, anime_info)

    # при запросе следующего манги
    if c.data == "NextManga":
        bot.answer_callback_query(c.id, show_alert=True, text="Хотим получить следующее аниме")

    # при запросе следующего манги
    if c.data == "PrevManga":
        bot.answer_callback_query(c.id, show_alert=True, text="Хотим получить предыдущее аниме")


if __name__ == "__main__":
    bot.polling(none_stop=True)
