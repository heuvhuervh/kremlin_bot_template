from fastapi import FastAPI
import logging
import asyncio
import random
import aiohttp
from aiogram import Bot, Dispatcher, types, F, executor
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import os
import signal
from contextlib import asynccontextmanager
from math import radians, sin, cos, sqrt, atan2

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Основная клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏰 О Кремле")],
        [KeyboardButton(text="🖼 Фото")],
        [KeyboardButton(text="❓ Загадка")],
        [KeyboardButton(text="🌤 Погода")],
        [KeyboardButton(text="📍 Отправить местоположение", request_location=True)],
        [KeyboardButton(text="🔄 Перезапуск")],
    ],
    resize_keyboard=True,
)

# Клавиатура для кнопки "Узнать ответ"
answer_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Узнать ответ")],
        [KeyboardButton(text="🔄 Перезапуск")],
    ],
    resize_keyboard=True,
)

# Клавиатура "О Кремле"
kremlin_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📜 История", callback_data="history")],
        [InlineKeyboardButton(text="🗺 Схема Кремля", callback_data="map")],
        [InlineKeyboardButton(text="📸 Исторические фото", callback_data="historical_photos")],
    ]
)

# Клавиатура истории
history_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Довмонтов город", callback_data="history_dovmont")],
        [InlineKeyboardButton(text="Перси", callback_data="history_persi")],
        [InlineKeyboardButton(text="Вечевая площадь", callback_data="history_vechevaya")],
        [InlineKeyboardButton(text="Троицкий собор", callback_data="history_trinity")],
        [InlineKeyboardButton(text="Благовещенский собор", callback_data="history_annunciation")],
        [InlineKeyboardButton(text="Башни", callback_data="history_towers")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ]
)

# Вся информация о Кремле
kremlin_info = {
    "history": "📜 Выберите интересующий раздел истории Псковского Кремля:",
    "history_dovmont": """🏰 Довмонтов город - музей под открытым небом

С южной стороны Крома расположен Довмонтов город. Сегодня это большой музей под открытым небом. Он получил своё название по имени князя Довмонта, который на протяжении 33-х лет правил городом (1266 - 1299 гг.). 

Изначально это место было частью псковского посада. В XIII веке территорию отделили каменной довмонтовой стеной и, вплоть до XVIII века, здесь был административный и духовный центр города. На небольшой территории Довмонтова города располагалось 18 православных храмов.

Во время Северной войны Пётр I стал укреплять город. На территории Довмонтова города расположилась Рождественская батарея. Уровень земли подняли на 4 метра. Все здания и сохранившиеся к тому времени церкви были засыпаны, а в уцелевших размещались склады оружия. 

В начале XIX века остатки обветшалых укреплений и вовсе разобрали за ненадобностью. С тех пор территория эта постепенно превращалась в заросший травой пустырь. Лишь в XX веке начались раскопки и теперь можно видеть частично отрытые фундаменты зданий и церквей.""",
    "history_persi": """🔶 Перси — южная стена Кремля

Перси — южная, приступная стена Крома, которая защищала Вечевую площадь и Троицкий собор. Впервые Перси упоминаются в летописи под 1065 годом, но некоторые исследователи считают, что стена существовала еще в IX в.

Слово «перси» означает «грудь», которой город был готовь встретить врага. Перед стеной псковичи вырыли Греблю — ров, который скорее всего был сухим. Известно, что Перси поднимались над уровнем Гребли не менее, чем на 20 м. Перси всегда были стеной из камня.

Когда в 1348 году Псков освободился от власти Великого Новгорода (несмотря на то что фактически самостоятельным Псков стал почти на век раньше), псковичи использовали Перси как постамент под колокольницу для вечевых и соборных колоколов. Перси, таким образом, стали символом независимого псковского вечевого государства.

Известно, что после 1466 года термин «Перси» практически перестал употребляться, но сама стена еще долгое время являлась уникальным на Руси архитектурным ансамблем.

В 1860 году архитектор Ранвид составил проект восстановления Персей и Смердьей башни, который был осуществлен в 1862-1865 годах. Отреставрированная южная стена простояла непокрытой почти сто лет и к середине XX в. вновь пришла в руинированное состояние. В конце 1950-х годов было принято решение вновь начать реставрационные работы на южной стене Кремля, а в последний раз стену реставрировали в 2014-2015 годах.

На стене Персей расположена интересная композиция, установленная в 1972 году в честь 730-летия победы Александра Невского в Ледовом побоище. Её автор — псковский архитектор, реставратор, художник и кузнец Всеволод Петрович Смирнов. На щите в виде воинского знамени изображены герб (барс) и план Пскова. Под прапором находятся пластины с гербами городов, которые участвовали в сражении на льду Чудского озера в 1242 году — Псков, Новгород, Тверь, Владимир и Переславль-Залесский. Колокола символизируют Вечевой и набатный колокола Псковской вечевой республики.

Сегодня Перси со стороны Кремля (с севера) имеют высоту 6 м, а со стороны Довмонтова города (с юга) — около 15 м, что объясняется резким перепадом рельефа. На западной оконечности Персей стоит восьмиугольная Довмонтова (Смердья) башня, а с востока возвышается Часовая (Троицкая) башня.""",
    "history_vechevaya": """🔔 Вечевая площадь — политический центр Пскова

Вечевая площадь — политический центр средневекового Пскова. Она примыкала к Троицкому собору с южной стороны. На вечевой площади в древности решались все самые важные вопросы жизни города: постройки укреплений, мостов, церквей; вопросы заключения мира и объявления войны. С 1348 по 1510 гг. здесь, на этой площади шумело народное собрание — вече. Это был верховный орган власти, на вече псковичи созывались звоном вечевого колокола.

На вече могли приходить все свободные взрослые мужчины, главы семей и владельцы дворов во Пскове. Поэтому вече называют народным собранием, но господствовали на вече бояре.

Только вече могло принимать новые законы и отменять старые; так, в 1467 году вече утвердило сборник законов Псковской Республики — Псковскую Судную Грамоту. Вече принимало и отправляло послов, избирало и смещало всех высших должностных лиц. Вече определяло поборы с населения, раскладывало подати и повинности, судило высших должностных лиц, а также рассматривало наиболее важные уголовные и гражданские дела. На вече была своя печать, которую прикладывали к утвержденным документам.

В последний раз вечевой колокол звонил 13 января 1510 года, когда завершилась эпоха Псковской вечевой республики и началась история Пскова в составе русского государства Московской Руси.

Сейчас вечевая площадь скрыта позднейшими наслоениями культурного слоя и находится на несколько метров ниже современного уровня поверхности.""",
    "history_trinity": """⛪ Троицкий собор - духовное сердце Пскова

Четвертый по счету храм на этом месте:
- Первый деревянный - X век (по преданию, по велению княгини Ольги)
- Каменный храм 1138 года
- Современное здание - 1699 года

Особенности:
- 7-ярусный иконостас
- Мощи псковских святых
- Чудотворные иконы

Был закрыт в 1935-1941 гг., вновь освящен в 1941 году.""",
    "history_annunciation": """🔔 Благовещенский собор - утраченная святыня

Собор построен в Псковском кремле в 1836 году для совершения богослужений в зимнее время - в период с 17 октября по шестую неделю после Пасхи. На строительство из казны было отпущено 180 000 рублей ассигнациями.

В 1888 году собор был отделан снаружи на средства бывшего церковного старосты, псковского купца Ивана Чернова. В 1890 году на собственные средства собор отделан внутри, на средства купца Ивана Чернова устроены хоры. На средства Псковского купеческого общества в 1898 году устроен балдахин над мощами святого князя Гавриила. По указу Святейшего Синода от 21 июня 1898 года мощи святого князя ежегодно с 15 октября по 23 апреля переносились из Троицкого собора в Благовещенский.

В 1920 - 1922 годах Благовещенский собор также как и Троицкий был передан обновленцам.

На заседании Псковского окружного исполкома 16 ноября 1929 года было заслушано представление окружной комиссии по размещению хлебных грузов о разрешении использовать под временные склады "теплые здания" Троицкого собора, так как верующим, по их мнению, достаточно "зимнего здания". Разрешение было дано с оговоркой "...наблюсти за полной сохранностью исторических, архитектурных и художественных ценностей".

27 августа 1932 года Псковский городской совет принял решение о размещении в соборе инкубаторной станции. О сохранности чего-либо речь уже не шла.

В 1933 году собор был взорван. Власти объявили, что нужен строительный материал для электростанции, но в кремле долго лежали монолитные глыбы взорванного собора.

25 апреля 2003 года на месте взорванного собора архиепископом Псковским и Великолукским Евсевием освящен памятный крест.""",
    "history_towers": """🛡️ Башни Кремля - стражи древнего Пскова

Примерно в одно время с Кутекромой на территории Псковского кремля появилась Троицкая башня (1400-1401 годы). Она также имеет другие названия – Лубянская, Великая и Часовая. Старая башня простояла до 1787 года, и была восстановлена вместе с Троицкими воротами в 1988 году.

История приземистой Власьевской башни начинается в конце XV века. Квадратное в сечении укрепление назвали так потому, что в Средние века рядом с ним находилась Власьевская церковь. Старая башня служила для охраны территории Псковского кремля со стороны реки Великой. Она отличается большим смотровым чердаком и высоким шатром. Эта башня проездная, и в старые времена через нее въезжали в кремль из Завеличья.

В Средние века внутри Псковского кремля размещался Старый Торг, и через ворота Власьевской башни к месту торговли попадали купцы и псковичи. Повозки, груженые товаром, проходили через расположенную в башне городскую таможню. В ночное время башенные ворота закрывали, и до утра возле них дежурила вооруженная охрана. В 60-е годы прошлого века полуразрушенную Власьевскую башню отстроили заново, и она приобрела современный вид. В 2010 году в Псковском кремле произошел сильнейший пожар. Раздуваемый ветром огонь уничтожил деревянный шатер Власьевской башни, но через некоторое время его восстановили.

В Кроме существуют и другие проездные башни. Попасть на его территорию можно через Святые ворота, над которыми возвышается Рыбницкая башня, построенная в XV веке для выхода к кремлю от реки Псковы. В те времена на спуске простирался торговый район Пскова – Рыбники, который и дал башне такое имя.

Первоначальная постройка не сохранилась до наших дней. Она обветшала и была разобрана. Современная Рыбницкая башня появилась в 1970-е годы, благодаря усилиям псковских реставраторов. Это укрепление тоже пострадало от большого пожара 2010 года, но было, как и Власьевская башня, реконструировано.

Довмонтова или Смердья башня интересна тем, что ее восстановлением занимался известный российский архитектор Константин Андреевич Тон. Строители сложили башню по его проекту в 1866 году, во время очередной реконструкции Псковского кремля. Очевидно, что талантливый архитектор привнес в конструкцию много новых элементов, и башня стала похожа на средневековые замки Европы. Многогранное строение венчает металлический флюгер в виде флага, на котором изображен русский воин.

Над долиной Псковы нависает Снетная или Средняя башня – одна из самых высоких в кремле (35 м). Она имеет внушительный диаметр – 11 метров. Сохранились сведения, что помимо оборонных функций, башня служила местом, где держали корм для охранявших кремль собак. Современный вид Снетная башня обрела в 1973 году.

Одна их наиболее живописных башен Псковского кремля стоит возле самого устья Псковы. Приземистая конструкция диаметром 16 м называется Плоской башней. Она гармонично вписывается в окружающий ландшафт и прекрасно смотрится и со стороны реки Великой, и от Псковы. Это единственная из башен кремля, которую не перестраивали на протяжении нескольких столетий. Она сохранила первоначальные пропорции и в наши дни хорошо отреставрирована.""",
    "architecture": """🏰 Архитектура Кремля - гений древних зодчих

Особенности псковской школы зодчества:
- Использование местного известняка
- Лаконичные формы
- Мощные стены с лопатками
- Особые системы сводов
- Боевые галереи (захабы)

Лучшие мастера участвовали в строительстве Московского Кремля.""",
    "places": """📍 Интересные места Кремля

1. Приказные палаты (XVII в.) - административный центр
2. Поганкины палаты - купеческие палаты
3. Место легендарного меча Довмонта
4. "Смердья башня" - по преданию, место казни
5. Древний колодец с родниковой водой
6. Остатки средневековых мостовых""",
    "map": "🗺 Схема Псковского Кремля",
}

# Все фото (полностью сохранены)
photo_urls = [
    "https://wikiway.com/upload/hl-photo/2ab/747/pskovskiy_kreml_29.jpg",
    "https://wikiway.com/upload/hl-photo/f18/15b/pskovskiy_kreml_26.jpg",
    "https://wikiway.com/upload/hl-photo/c9d/56c/pskovskiy_kreml_23.jpg",
    "https://wikiway.com/upload/hl-photo/ff4/9f6/pskovskiy_kreml_20.jpg",
    "https://wikiway.com/upload/hl-photo/481/eef/pskovskiy_kreml_1.jpg",
    "https://avatars.mds.yandex.net/get-altay/13590061/2a00000192586145741777fbab5a3d214ce4/XXXL",
    "https://sun9-21.userapi.com/impg/zLu8okcBi3SOimqubFPtjfLF9yALTPgOyPLX0Q/AA7ktdUjYWM.jpg?size=1620x2160&quality=95&sign=669b56f40a8526009b480fe179ecd56b&type=album",
    "https://sun9-44.userapi.com/impg/0X-6kobOBrTnJs2Bbokd32_wPRZTgXbpCRb7sg/eW2AQNhXvVY.jpg?size=1920x2140&quality=95&sign=294007fe1b9827b841e66b2d730da1ce&type=album",
    "https://avatars.mds.yandex.net/get-altay/13671691/2a00000190d5474f968e75c280efd077cd33/XXXL",
    "https://sun9-44.userapi.com/impg/0X-6kobOBrTnJs2Bbokd32_wPRZTgXbpCRb7sg/eW2AQNhXvVY.jpg?size=1920x2140&quality=95&sign=294007fe1b9827b841e66b2d730da1ce&type=album",
    "https://avatars.mds.yandex.net/get-altay/13455884/2a000001913b3e4233c3e528cd6cc5f86366/XXXL",
    "https://sun9-24.userapi.com/impg/Ear4HHf51_Ixonzyi2BoTA1A0f-QtiWpVqVaxg/IZ2jyRJI86M.jpg?size=1620x2160&quality=95&sign=e0c6f0c123b6af5d453a51ce5c2c1ba1&type=album",
    "https://sun9-9.userapi.com/impg/3XOSUBln5k6SXn0NkLxgHqEsRSsOVERpjuAPJQ/4YkXGBf9Hh8.jpg?size=2560x1440&quality=95&sign=9aa48f922e0fb1874308a9ea868747c6&type=album",
    "https://sun9-73.userapi.com/impg/ItpibdRqp8_Vthp5HNdGLIIS605iq0uB5khL7g/xqyspaGCo2M.jpg?size=1080x938&quality=95&sign=73cbe436199f2a57724e492f0ac33aaa&type=album",
    "https://sun9-32.userapi.com/impg/oU5q-zY62kDwiQuR7E8tCUrGwMTsIb_TYwBDVA/7DdtP9aDPMw.jpg?size=1200x1600&quality=95&sign=ceb06d0c0e5505f7c35ee62eac79eb9f&type=album",
    "https://sun9-46.userapi.com/impg/pf2xWQJW0y6kkNUIH662MeddoVBfXyWP5iASAA/kpgzJopajJY.jpg?size=902x1032&quality=95&sign=e3c7e25350df964a21b9ab4319909230&type=album",
]

# Исторические фото (полностью сохранены)
historical_photo_urls = [
    "https://sun9-6.userapi.com/impg/B8l5F5IPWR_KD7dev8uKCByIeujxLOSVW2YNWA/tnPqvpcgwTw.jpg?size=1600x1058&quality=95&sign=9d5d1483cd561dd86107922135fb7b88&type=album",
    "https://sun9-5.userapi.com/impg/X_csfph-aGP7OJy_aCl5DTivCULXU7C_3vE1cA/LX6tAQEu49c.jpg?size=1287x970&quality=95&sign=1972d6031fab6a31f5f67642d3c06bbf&type=album",
    "https://sun9-77.userapi.com/impg/6JC4ZTdWeh8vUSYuISebZYBe8_xs7T-MMrTZOg/xmhGhxf-8-k.jpg?size=1280x825&quality=95&sign=a65bc0cd61dbf25b6034d4d346babdb4&type=album",
    "https://sun9-19.userapi.com/impg/avHifZ_Jm-BP8L4YfpQzHKUhcU1drgjTrfjLpw/S_lHf5p9VCg.jpg?size=941x1127&quality=95&sign=ee8b51db53e52867aba42606bf4e37fd&type=album",
    "https://sun9-26.userapi.com/impg/UdfOC9sBLWAkd5FU0sL8hHZ8Q_ChOYm3EWx8Pw/jYM5IHSyzkA.jpg?size=1226x774&quality=95&sign=f76ca9614d9897e9b32f83d2b7d3eaf3&type=album",
    "https://sun9-39.userapi.com/impg/JufR54xa6M2AUjHiAIntUsb_kgafl7d4OkYhUQ/XB4w58hhdDs.jpg?size=1600x1196&quality=95&sign=ec705b474b755f748829e3caa727b621&type=album",
    "https://sun9-15.userapi.com/impg/kAiGwFC8RB53pN4Q_uItcnedgJcrh2P0tCPcTw/f8wNgdTFm3k.jpg?size=1036x655&quality=95&sign=8a9f58bb868e0d84bf4aadc1f1bbab81&type=album",
    "https://sun9-68.userapi.com/impg/2w_wl00yRFZr5T9HJnNS089j6xnmzw0zs0F2YA/Q9Czsy4EbXo.jpg?size=926x941&quality=95&sign=a45a9b747fc432d98d4819d116562cfe&type=album",
    "https://sun9-3.userapi.com/impg/eHzo9fQF6z2vr6B1GeWiaHARJlsoxpCa99UoLA/ztAaNrb5BIg.jpg?size=1644x1055&quality=95&sign=66dd844a7ece00076516d706fbed4d81&type=album",
    "https://sun9-43.userapi.com/impg/Qo8vSidlgsqQKaGQjmWG2dGUw7vxF4HJ5RRLWQ/Tw9RfjTrAy4.jpg?size=984x575&quality=95&sign=1a353c965e56905e2bbc744dcfaa43ad&type=album",
    "https://sun9-27.userapi.com/impg/4OIeZlW1pqp4fPWX7lqNBEIjhQv8JbzC4Z-RsA/MiOaROICN0A.jpg?size=1476x1008&quality=95&sign=d962477ca1e9d72921bb4f631c649395&type=album",
]

# Загадки (полностью сохранены)
riddles_list = [
    ("Какая река протекает рядом с Псковским Кремлем?", "великая"),
    ("Какая река протекает рядом с Псковским Кремлем?", "пскова"),
    ("Сколько башен у Псковского Кремля?", "7"),
    ("Как называется угловая башня псковского Кремля?", "Кутекрома"),
    ("Какой храм находится внутри Кремля?", "троицкий собор"),
    (
        "Южная стена Крома называется Перси. А как это слово переводится с древнерусского?",
        "грудь",
    ),
]

# Глобальные переменные для хранения состояния
user_riddles = {}
user_riddle_lists = {}

# Координаты Кремля
KREMLIN_LAT = 57.8222
KREMLIN_LON = 28.3281

# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========
@dp.message(Command("start"))
async def start(message: types.Message):
    welcome_text = """
🏰 *Добро пожаловать в официальный гид по Псковскому Кремлю!*

Здесь вы найдете:
- 📜 Исторические сведения о древней крепости
- 🖼 Фотографии и исторические изображения
- 🗺 Схему Кремля с достопримечательностями
- 🌤 Актуальную погоду в Пскове
- ❓ Интересные загадки о Кремле

Выберите интересующий вас раздел в меню ниже или просто напишите свой вопрос.

*Псковский Кремль* - это:
• Один из древнейших кремлей России (X-XI вв.)
• Объект Всемирного наследия ЮНЕСКО
• Место зарождения псковской вечевой республики
• Уникальный образец псковской школы зодчества

Приятного путешествия в историю! 🏛️
"""
    await message.answer_photo(
        photo="https://sun9-44.userapi.com/impg/0X-6kobOBrTnJs2Bbokd32_wPRZTgXbpCRb7sg/eW2AQNhXvVY.jpg?size=1920x2140&quality=95&sign=294007fe1b9827b841e66b2d730da1ce&type=album",
        caption=welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

@dp.message(F.text)
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text == "🔄 Перезапуск":
        user_riddles.pop(user_id, None)
        user_riddle_lists.pop(user_id, None)
        await message.answer("🔄 Бот перезапущен!", reply_markup=keyboard)

    elif text == "🏰 О Кремле":
        await message.answer("Выберите раздел:", reply_markup=kremlin_inline_keyboard)

    elif text == "🖼 Фото":
        await message.answer("📷 Отправляю фото...")
        for photo_url in photo_urls:
            await message.answer_photo(photo_url)
            await asyncio.sleep(1)
        await message.answer("Все современные фото загружены!")

    elif text == "❓ Загадка":
        if user_id not in user_riddle_lists or not user_riddle_lists[user_id]:
            user_riddle_lists[user_id] = random.sample(riddles_list, len(riddles_list))

        riddle, answer = user_riddle_lists[user_id].pop()
        user_riddles[user_id] = (riddle, answer)
        await message.answer(f"❓ Загадка: {riddle}")

    elif text == "🌤 Погода":
        weather = await get_weather()
        await message.answer(weather)

    elif text == "❓ Узнать ответ":
        if user_id in user_riddles:
            riddle, answer = user_riddles[user_id]
            if "река" in riddle.lower():
                response = "Правильные ответы:\n1. Великая\n2. Пскова"
            else:
                response = f"Правильный ответ: {answer}"
            await message.answer(response, reply_markup=keyboard)
            del user_riddles[user_id]
        else:
            await message.answer("Сейчас нет активных загадок", reply_markup=keyboard)

    elif user_id in user_riddles:
        riddle, answer = user_riddles[user_id]
        if "река" in riddle.lower():
            if text.lower() in ["великая", "пскова"]:
                await message.answer("✅ Правильно!", reply_markup=keyboard)
                del user_riddles[user_id]
            else:
                await message.answer(
                    "❌ Неверно, попробуйте еще раз или нажмите '❓ Узнать ответ'",
                    reply_markup=answer_keyboard,
                )
        else:
            if text.lower() == answer.lower():
                await message.answer("✅ Правильно!", reply_markup=keyboard)
                del user_riddles[user_id]
            else:
                await message.answer(
                    "❌ Неверно, попробуйте еще раз или нажмите '❓ Узнать ответ'",
                    reply_markup=answer_keyboard,
                )

@dp.message(F.content_type == "location")
async def handle_location(message: types.Message):
    lat = message.location.latitude
    lon = message.location.longitude
    distance = calculate_distance(lat, lon, KREMLIN_LAT, KREMLIN_LON)

    if distance < 0.5:
        response = "🏰 Вы у стен Кремля!"
    elif distance < 5:
        response = f"📍 Вы в {distance:.1f} км от Кремля"
    else:
        response = f"🌍 Вы в {distance:.1f} км от Пскова"

    await message.answer(response, reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data

    if data == "back_to_main":
        await callback.message.edit_text(
            "Выберите раздел:", reply_markup=kremlin_inline_keyboard
        )
    elif data == "history":
        await callback.message.edit_text(
            kremlin_info["history"], reply_markup=history_keyboard
        )
    elif data == "map":
        await callback.message.answer_photo(
            "https://sun9-2.userapi.com/impg/SRUn-jZVB031BoD8IBxWUjjaZ7HT3PMKXv1FSg/pSrPAdRyG_o.jpg?size=1600x1156&quality=95&sign=7a665004c8c9ecac218205f7d23fc0ba&type=album",
            caption=kremlin_info["map"],
        )
    elif data in kremlin_info:
        await callback.message.edit_text(
            kremlin_info[data],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data=(
                                "history"
                                if data.startswith("history_")
                                else "back_to_main"
                            ),
                        )
                    ]
                ]
            ),
        )
    elif data == "historical_photos":
        await callback.message.answer("🕰 Исторические фото:")
        for photo_url in historical_photo_urls:
            await callback.message.answer_photo(photo_url)
            await asyncio.sleep(1)
        await callback.answer()

    await callback.answer()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def get_weather(city: str = "Псков"):
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "q": city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ru",
            }
            async with session.get(WEATHER_URL, params=params) as response:
                data = await response.json()
                if response.status == 200:
                    weather = data["weather"][0]["description"]
                    temp = data["main"]["temp"]
                    feels_like = data["main"]["feels_like"]
                    humidity = data["main"]["humidity"]
                    wind = data["wind"]["speed"]
                    return (
                        f"🌤 Погода в {city}:\n"
                        f"• Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                        f"• Состояние: {weather}\n"
                        f"• Влажность: {humidity}%\n"
                        f"• Ветер: {wind} м/с"
                    )
                else:
                    return "Не удалось получить данные о погоде"
    except Exception as e:
        logging.error(f"Ошибка при получении погоды: {e}")
        return "Произошла ошибка при запросе погоды"

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6373.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * (2 * atan2(sqrt(a), sqrt(1 - a)))

# ========== ОБРАБОТКА ЗАВЕРШЕНИЯ РАБОТЫ ==========
async def on_shutdown(dp):
    logging.warning("Получен сигнал завершения работы...")
    await bot.close()
    await dp.storage.close()
    logging.warning("Бот остановлен")

# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем бота в фоне
    asyncio.create_task(executor.start_polling(dp, on_shutdown=on_shutdown))
    yield
    # При завершении закрываем сессию бота
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Bot is running"}

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))