import csv
import re
import sqlite3

import bs4.element
import requests
from bs4 import BeautifulSoup as BS
import time
from b24 import call_b24_method

B24APIKEY = 'aid284xmwhcnonuq'
URL = 'niieco.bitrix24.ru'
WEBHOOK = 'https://niieco.bitrix24.ru/rest/12/aid284xmwhcnonuq/'
SLEEP = 1
count = 0
request_order = []

db = sqlite3.connect('server.db', check_same_thread=False)
sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS pages(
url TEXT
        )""")
db.commit()



def find_total(html):
    total = ""
    return total

def extract_header(string):
    str_pattern = r"(<.*>)(\s\s)*(\s)(.*)"
    str_vol = re.findall(str_pattern, string)
    return str_vol[0][3].strip()

def extract_row_name(string):
    str_pattern = r"(\n)(\s\s*)(.*)"  # (<.*>)(\s\s)*(\s)(.*)
    str_vol = re.findall(str_pattern, string)
    return str_vol[0][3].strip()

def extract_volue(string):
    try:
        try:
            str_pattern = r"(            .*              )"
            str_vol = re.findall(str_pattern, string)
            return str_vol[0].strip()
        except:
            str_pattern = r"(<p>)([\w\d\s]*</p>)"
            str_vol = re.findall(str_pattern, string)
            ret = str_vol[0][1]
            str_pattern = r"([\w\d\s]*)(</p>)"
            ret = re.findall(str_pattern, ret)
    except:
        return string
    return ret[0][0]

def extract_row_title(string):
    str_pattern = r"(\n)(\s\s*)(.*:)"
    str_vol = re.findall(str_pattern, string)
    # str_pattern2 = r"(.* \r?)"
    # str_vol2 = re.findall(str_pattern2, str_vol[0][2])
    return str_vol[0][2]

def extract_organ(tag):
    #organ_title_pattern = r"<p>(.*)<\/p>.*?href=.*?>(.*?)<\/a>"
    #organ_title = re.findall(organ_title_pattern, tag)
    #' '.join(organ_title)
    return tag.text

def extract_volue_without(tag):
    cony = list()
    con = tag.find_all('p')
    for co in con:
        cony.append(str(co))
    return cony

def extract_phone_and_comments(string):
    ret = dict()
    phone_pattern = r"(\+7|8|7).*?(\d{3}).*?(\d{3}).*?(\d{2}).*?(\d{2})"
    phone = re.findall(phone_pattern, string)
    comment_pattern = "(.*<p>)(.*)(<\/p><)"
    comment = re.findall(comment_pattern, string)
    phone_str = str()
    for i in phone[0]:
        phone_str = phone_str + i
    ret['phone'] = phone_str
    ret['comment'] = comment[0][1]
    return ret

def extract_date(string):
    ret = dict()
    if len(string) <= 19:
        ret['start'] = string
        ret['end'] = ''
    else:
        date_pattern = r"(\d.*)( - )(.*\d)"
        date = re.findall(date_pattern, string)
        ret['start'] = date[0][0]
        ret['end'] = date[0][2]
    return ret

def extract_descussion_object_title(string):
    ret = dict()
    title_pattern = r"[а-я, ,А-Я]*"
    title = re.findall(title_pattern, string)
    title_out = str()
    for i in title:
        if len(i) == 0 or i == ' ':
            pass
        else:
            title_out = title_out + i
    return title_out

def write_file(row):
    header = row.keys()
    global count
    if count == 0:
        with open('zakazi.csv', 'w', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=header, lineterminator="\r\n", delimiter=",")
            f = writer.writeheader()
            f = writer.writerow(row)
            count += 1
    else:
        with open('zakazi.csv', 'a', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, lineterminator="\r\n", fieldnames=header, delimiter=",")
            f = writer.writerow(row)
    count += 1
    if count == 10:
        return 10

def parsing_news_page_v3(url_for_page_parsing):
    #url_for_page_parsing = 'https://rpn.gov.ru/public/111020230952206/'
    print(url_for_page_parsing)
    time.sleep(SLEEP)
    rr = requests.get(url_for_page_parsing)
    htmls = BS(rr.content, 'html.parser')
    row_dic = {}
    row_dic['Орган, на официальном сайте которого необходимо разместить информацию:'] = list()
    row_dic['Дата и время проведения:'] = list() #3
    row_dic['Ссылка на страницу события:'] = url_for_page_parsing#4
    # Обработка заголовка страницы
    header = htmls.find_all("h1")
    row_dic['Название заявки:'] = extract_header(str(header))#5

    header2 = htmls.find_all("h2")
    item_number = extract_header(str(header2))

    #content_box = htmls.find_all(class_="contentBox")
    #class_ui = htmls.find_all(class_="ui")
    # Разбираем поля заявки
    rows = htmls.find_all(class_="text _dark")
    keys = htmls.find_all(class_="sectionNewsPage__infoSupport")
    if item_number == 'Учётный номер заявки:':
        row_dic['Учётный номер заявки:'] = extract_volue(str(rows[0]))#6
        rows.pop(0)
        rows.pop(-1)
    #Проверка на название полей
    if rows.__len__() == keys.__len__():
        if_error = False
        past_key_p_string = ''
        for key in keys:
            key_text = key.text
            key_p_string = extract_row_title(str(key_text))
            if key_p_string == 'Полное наименование заказчика:':
                row_dic['Полное наименование заказчика:'] = extract_volue(str(rows[keys.index(key)]))#7
                past_key_p_string = key_p_string
            elif key_p_string == 'Краткое наименование заказчика:':
                row_dic['Краткое наименование заказчика:'] = extract_volue(str(rows[keys.index(key)]))#8
                past_key_p_string = key_p_string
            elif key_p_string == 'ИНН заказчика:':
                row_dic['ИНН заказчика:'] = extract_volue(str(rows[keys.index(key)]))#9
                past_key_p_string = key_p_string
            elif key_p_string == 'ОГРН (ОГРНИП) заказчика:':
                row_dic['ОГРН (ОГРНИП) заказчика:'] = extract_volue(str(rows[keys.index(key)]))#10
                past_key_p_string = key_p_string
            elif key_p_string == 'Город:' and past_key_p_string in ['ОГРН (ОГРНИП) заказчика:','ИНН заказчика:','Краткое наименование заказчика:','Полное наименование заказчика:']:
                row_dic['Город заказчика:'] = extract_volue(str(rows[keys.index(key)]))#11
            elif key_p_string == 'Индекс, улица, дом, строение, корпус:' and past_key_p_string in ['ОГРН (ОГРНИП) заказчика:','ИНН заказчика:','Краткое наименование заказчика:','Полное наименование заказчика:']:
                row_dic['Индекс, улица, дом, строение, корпус:'] = extract_volue(str(rows[keys.index(key)]))#12
            elif key_p_string == 'Номер телефона:' and past_key_p_string in ['ОГРН (ОГРНИП) заказчика:','ИНН заказчика:','Краткое наименование заказчика:','Полное наименование заказчика:']:
                row_dic['Номер телефона:'] = extract_volue(str(rows[keys.index(key)]))#13
            elif key_p_string == 'Адрес электронной почты, факс заказчика:':
                row_dic['Адрес электронной почты, факс заказчика:'] = extract_volue(str(rows[keys.index(key)]))#14
            elif key_p_string == 'Полное наименование исполнителя:':
                row_dic['Полное наименование исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#15
                past_key_p_string1 = key_p_string
            elif key_p_string == 'Краткое наименование исполнителя:':
                row_dic['Краткое наименование исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#16
                past_key_p_string1 = key_p_string
            elif key_p_string == 'ИНН исполнителя:':
                row_dic['ИНН исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#17
                past_key_p_string1 = key_p_string
            elif key_p_string == 'ОГРН (ОГРНИП) исполнителя:':
                row_dic['ОГРН (ОГРНИП) исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#18
                past_key_p_string1 = key_p_string
            elif key_p_string == 'Город:' and past_key_p_string1 in ['ОГРН (ОГРНИП) исполнителя:','ИНН исполнителя:','Краткое наименование исполнителя:','Полное наименование исполнителя:']:
                row_dic['Город исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#19
            elif key_p_string == 'Индекс, улица, дом, строение, корпус:' and past_key_p_string1 in ['ОГРН (ОГРНИП) исполнителя:','ИНН исполнителя:','Краткое наименование исполнителя:','Полное наименование исполнителя:']:
                row_dic['Индекс, улица, дом, строение, корпус исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#20
            elif key_p_string == 'Номер телефона:' and past_key_p_string1 in ['ОГРН (ОГРНИП) исполнителя:','ИНН исполнителя:','Краткое наименование исполнителя:','Полное наименование исполнителя:']:
                row_dic['Номер телефона исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#21
            elif key_p_string == 'Адрес электронной почты, факс исполнителя:':
                row_dic['Адрес электронной почты, факс исполнителя:'] = extract_volue(str(rows[keys.index(key)]))#22
            elif key_p_string == 'Орган, на официальном сайте которого необходимо разместить информацию:':
                executor_authority_out = extract_organ(rows[keys.index(key)])
                row_dic['Орган, на официальном сайте которого необходимо разместить информацию:'] = executor_authority_out#23
            elif key_p_string == 'Наименование:':
                row_dic['Наименование деятельности:'] = extract_volue(str(rows[keys.index(key)]))#24
            elif key_p_string == 'Место реализации:':
                row_dic['Место реализации:'] = extract_volue(str(rows[keys.index(key)]))#25
            elif key_p_string == 'Цель осуществления:':
                row_dic['Цель осуществления:'] = extract_volue(str(rows[keys.index(key)]))#26
            elif key_p_string == 'Сроки проведения оценки воздействия на окружающую среду:':
                impact_assessment_time = extract_date(extract_volue(str(rows[keys.index(key)])))
                row_dic['Сроки проведения оценки воздействия на окружающую среду старт:'] = impact_assessment_time['start']#27
                row_dic['Сроки проведения оценки воздействия на окружающую среду окончание:'] = impact_assessment_time['end']#28
            elif key_p_string == 'Наименование:':
                row_dic['Наименование авторизованой организации:'] = extract_volue(str(rows[keys.index(key)]))#29
            elif key_p_string == 'Адрес места нахождения и фактический адрес:':
                row_dic['Адрес места нахождения и фактический адрес:'] = extract_volue(str(rows[keys.index(key)]))#30
            elif key_p_string == 'Контактный телефон:':
                authorized_organizing_out = extract_phone_and_comments(str(rows[keys.index(key)]))
                row_dic['Контактный телефон:'] = authorized_organizing_out['phone']#31
                row_dic['Контактный телефон комментарий:'] = authorized_organizing_out['comment']#32
            elif key_p_string == 'Адрес электронной почты, факс:':
                row_dic['Адрес электронной почты, факс:'] = extract_volue(str(rows[keys.index(key)]))#33
            elif key_p_string == 'Объект общественных обсуждений:':
                row_dic['Объект общественных обсуждений:'] = extract_descussion_object_title(str(rows[keys.index(key)]))#34
            elif key_p_string == 'Место доступности объекта общественного обсуждения:':
                row_dic['Место доступности объекта общественного обсуждения:'] = extract_volue(str(rows[keys.index(key)]))#35
            elif key_p_string == 'Сроки доступности объекта общественного обсуждения:':
                authorized_organizing_time = extract_date(extract_volue(str(rows[keys.index(key)])))
                row_dic['Сроки доступности объекта общественного обсуждения открытие:'] = authorized_organizing_time['start']#36
                row_dic['Сроки доступности объекта общественного обсуждения закрытие:'] = authorized_organizing_time['end']#37
            elif key_p_string == 'Форма проведения общественного обсуждения:':
                row_dic['Форма проведения общественного обсуждения:'] = extract_volue(str(rows[keys.index(key)]))#38
            elif key_p_string == 'Сроки проведения:':
                row_dic['Сроки проведения:'] = extract_volue(str(rows[keys.index(key)]))#39
            elif key_p_string == 'Место размещения и сбора опросных листов (если такое место отличается от места размещения объекта общественных обсуждений), в том числе в электронном виде:':
                row_dic['Место размещения и сбора опросных листов (если такое место отличается от места размещения объекта общественных обсуждений), в том числе в электронном виде:'] = extract_volue(str(rows[keys.index(key)]))#40
            elif key_p_string == 'Форма и место представления замечаний и предложений:':
                row_dic['Форма и место представления замечаний и предложений:'] = extract_descussion_object_title(str(rows[keys.index(key)]))#41
            elif key_p_string == 'Форма проведения:':
                row_dic['Форма проведения:'] = extract_volue(str(rows[keys.index(key)]))#42
            elif key_p_string == 'Места размещения объекта общественного обсуждения:':
                row_dic['Места размещения объекта общественного обсуждения:'] = extract_volue(str(rows[keys.index(key)]))#43
            elif key_p_string == 'Дата публикации:':
                row_dic['Дата публикации:'] = extract_volue(str(rows[keys.index(key)]))#44
            elif key_p_string == 'Место проведения:':
                row_dic['Место проведения:'] = extract_volue(str(rows[keys.index(key)]))#45
            elif key_p_string == 'Дата и время проведения:':
                impact_assessment_time = extract_date(extract_volue(str(rows[keys.index(key)])))
                row_dic['Дата и время проведения старт:'] = impact_assessment_time['start']#46
                row_dic['Дата и время проведения окончание:'] = impact_assessment_time['end']#47
            elif key_p_string == 'Место сбора замечаний, комментариев и предложений:':
                row_dic['Место сбора замечаний, комментариев и предложений: '] = extract_volue(str(rows[keys.index(key)]))#48


            else:
                if if_error:
                    print(f"key={key_p_string}")
                    row_dic['Добавить ключ'].append(key_p_string)
                else:
                    print(f" Не нашел в url = {url_for_page_parsing}: ")
                    print(f"key={key_p_string} ")
                    row_dic = {'Добавить ключ': key_p_string}
                    if_error = True
    else:
        print(f"Массивы не равны url = {url_for_page_parsing}")


    return row_dic

def send_to_b24(event=dict()):
    #нормализация данных
    for key, value in event.items():
        if isinstance(value, list):
            ' '.join(value)


    # Создаем ЛИД
    method = 'crm.lead.add'
    params = {
        'FIELDS':{
                        'TITLE': event['Название заявки:'] if 'Название заявки:' in event.keys() else None,
                    'STATUS_ID': "NEW",
            "UF_CRM_1699396336": event['Ссылка на страницу события:'] if 'Ссылка на страницу события:' in event.keys() else None,
            "UF_CRM_1699396352": event['Название заявки:'] if 'Название заявки:' in event.keys() else None,
            "UF_CRM_1699396374": event['Учётный номер заявки:'] if 'Учётный номер заявки:' in event.keys() else None,
            "UF_CRM_1699396393": event['Полное наименование заказчика:'] if 'Полное наименование заказчика:' in event.keys() else None,
            "UF_CRM_1699396412": event['Краткое наименование заказчика:'] if 'Краткое наименование заказчика:' in event.keys() else None,
            "UF_CRM_1699396435": event['ИНН заказчика:'] if 'ИНН заказчика:' in event.keys() else None,
            "UF_CRM_1699396473": event['ОГРН (ОГРНИП) заказчика:'] if 'ОГРН (ОГРНИП) заказчика:' in event.keys() else None,
            "UF_CRM_1699396513": event['Место реализации:'] if 'Место реализации:' in event.keys() else None,
            "UF_CRM_1699396524": event['Город заказчика:'] if 'Город заказчика:' in event.keys() else None,
            "UF_CRM_1699396533": event['Цель осуществления:'] if 'Цель осуществления:' in event.keys() else None,
            "UF_CRM_1699396540": event['Индекс, улица, дом, строение, корпус:'] if 'Индекс, улица, дом, строение, корпус:' in event.keys() else None,
            "UF_CRM_1699396565": event['Номер телефона:'] if 'Номер телефона:' in event.keys() else None,
            "UF_CRM_1699396568": event['Сроки проведения оценки воздействия на окружающую среду старт:'] if 'Сроки проведения оценки воздействия на окружающую среду старт:' in event.keys() else None,
            "UF_CRM_1699396579": event['Адрес электронной почты, факс заказчика:'] if 'Адрес электронной почты, факс заказчика:' in event.keys() else None,
            "UF_CRM_1699396591": event['Сроки проведения оценки воздействия на окружающую среду окончание:'] if 'Сроки проведения оценки воздействия на окружающую среду окончание:' in event.keys() else None,
            "UF_CRM_1699396598": event['Полное наименование исполнителя:'] if 'Полное наименование исполнителя:' in event.keys() else None,
            "UF_CRM_1699396609": event['Наименование авторизованой организации:'] if 'Наименование авторизованой организации:' in event.keys() else None,
            "UF_CRM_1699396618": event['Краткое наименование исполнителя:'] if 'Краткое наименование исполнителя:' in event.keys() else None,
            "UF_CRM_1699396627": event['Адрес места нахождения и фактический адрес:'] if 'Адрес места нахождения и фактический адрес:' in event.keys() else None,
            "UF_CRM_1699396669": event['Контактный телефон:'] if 'Контактный телефон:' in event.keys() else None,
            "UF_CRM_1699396683": event['Контактный телефон комментарий:'] if 'Контактный телефон комментарий:' in event.keys() else None,
            "UF_CRM_1699396697": event['Адрес электронной почты, факс:'] if 'Адрес электронной почты, факс:' in event.keys() else None,
            "UF_CRM_1699396717": event['ОГРН (ОГРНИП) исполнителя:'] if 'ОГРН (ОГРНИП) исполнителя:' in event.keys() else None,
            "UF_CRM_1699396718": event['Объект общественных обсуждений:'] if 'Объект общественных обсуждений:' in event.keys() else None,
            "UF_CRM_1699396738": event['Город исполнителя:'] if 'Город исполнителя:' in event.keys() else None,
            "UF_CRM_1699396748": event['Место доступности объекта общественного обсуждения:'] if 'Место доступности объекта общественного обсуждения:' in event.keys() else None,
            "UF_CRM_1699396757": event['Индекс, улица, дом, строение, корпус исполнителя:'] if 'Индекс, улица, дом, строение, корпус исполнителя:' in event.keys() else None,
            "UF_CRM_1699396773": event['Номер телефона исполнителя:'] if 'Номер телефона исполнителя:' in event.keys() else None,
            "UF_CRM_1699396774": event['Сроки доступности объекта общественного обсуждения открытие:'] if 'Сроки доступности объекта общественного обсуждения открытие:' in event.keys() else None,
            "UF_CRM_1699396789": event['Сроки доступности объекта общественного обсуждения закрытие:'] if 'Сроки доступности объекта общественного обсуждения закрытие:' in event.keys() else None,
            "UF_CRM_1699396794": event['Адрес электронной почты, факс исполнителя:'] if 'Адрес электронной почты, факс исполнителя:' in event.keys() else None,
            "UF_CRM_1699396806": event['Форма проведения общественного обсуждения:'] if 'Форма проведения общественного обсуждения:' in event.keys() else None,
            "UF_CRM_1699396812": event['Орган, на официальном сайте которого необходимо разместить информацию:'] if 'Орган, на официальном сайте которого необходимо разместить информацию:' in event.keys() else None,
            "UF_CRM_1699396826": event['Сроки проведения:'] if 'Сроки проведения:' in event.keys() else None,
            "UF_CRM_1699396827": event['Наименование деятельности:'] if 'Наименование деятельности:' in event.keys() else None,
            "UF_CRM_1699396847": event['Место сбора замечаний, комментариев и предложений:'] if 'Место сбора замечаний, комментариев и предложений:' in event.keys() else None,
            "UF_CRM_1699396848": event['Место размещения и сбора опросных листов (если такое место отличается от места размещения объекта общественных обсуждений), в том числе в электронном виде:'] if 'Место размещения и сбора опросных листов (если такое место отличается от места размещения объекта общественных обсуждений), в том числе в электронном виде:' in event.keys() else None,
            "UF_CRM_1699396863": event['Дата и время проведения окончание:'] if 'Дата и время проведения окончание:' in event.keys() else None,
            "UF_CRM_1699396866": event['Форма и место представления замечаний и предложений:'] if 'Форма и место представления замечаний и предложений:' in event.keys() else None,
            "UF_CRM_1699396880": event['Дата и время проведения старт:'] if 'Дата и время проведения старт:' in event.keys() else None,
            "UF_CRM_1699396883": event['Форма проведения:'] if 'Форма проведения:' in event.keys() else None,
            "UF_CRM_1699396896": event['Место проведения:'] if 'Место проведения:' in event.keys() else None,
            "UF_CRM_1699396900": event['Места размещения объекта общественного обсуждения:'] if 'Места размещения объекта общественного обсуждения:' in event.keys() else None,
            "UF_CRM_1699396916": event['Дата публикации:'] if 'Дата публикации:' in event.keys() else None,
            "UF_CRM_1699403149": event['ИНН исполнителя:'] if 'ИНН исполнителя:' in event.keys() else None,
        }
    }
    res = call_b24_method(method, params)
    print(res)



def parsing_news_desk(url_for_parsing):
    url_for_adding = 'https://rpn.gov.ru/public/'
    events = dict()
    event_id = 0
    page_counter = 1
    while event_id not in events.keys():
        url_for_parsing = f'https://rpn.gov.ru/public/?PAGEN_1={page_counter}#content-top'
        r = requests.get(url_for_parsing)
        htmls = BS(r.content, 'html.parser')
        total_news = find_total(htmls)
        # print(html)
        page_news = htmls.find_all(class_="sectionNews__item")

        for i in range(0, page_news.__len__(), 1):
            item_news = page_news[i].find(class_="newsPreview__imageBox")
            a_tag = str(item_news)
            url_pattern = r'href="/public/(.*?)"'
            urls = re.findall(url_pattern, a_tag)
            urls = f'{url_for_adding}{urls[0]}'
            id_pattern = r'/public/(\d*)'
            event_id = re.findall(id_pattern, urls)
            event_id = event_id[0]
            if event_id in events.keys():
                break
            sql.execute(f"SELECT url FROM pages WHERE url = ?",(urls,))
            row = sql.fetchone()
            if row is None:
                sql.execute("INSERT INTO pages (url) VALUES (?)", (urls,))
                db.commit()
            else:
                pass#exit()

            event = parsing_news_page_v3(urls)
            send_to_b24(event)
            events[f"{event_id}"]=event
            if i >= 100:
                return events
        print(f'Страница = {page_counter}')
        page_counter += 1
        event_id = 0
        if page_counter > 5:
            return events
    return events

def dict_formatter(events):
    keys = dict()
    for _, event in events.items():
        e_keys = event.keys()
        for key in e_keys:
            if key not in keys:
                keys[f'{key}'] = ''
    event_out = list()
    event_row = dict()
    """    for event_id in events:
            event_row['id'] = event_id
            for key in keys:
                events_line = events[f'{event_id}']
                try:
                    event_row[f'{key}'] = events_line [f'{key}']
                except:
                    event_row[f'{key}'] = ''
            event_out.append(event_row)
    """
    for event_id in events:
        event_row = {'id': event_id}
        for key in keys:
            events_line = events[event_id]
            try:
                event_row[key] = events_line[key]
            except KeyError:
                event_row[key] = ''
        event_out.append(event_row)



    return event_out

url_for_parsing = 'https://rpn.gov.ru/public/?PAGEN_1=1#content-top'
events = parsing_news_desk(url_for_parsing)
"""
#Запись в Файл
eventa_out = dict_formatter(events)
for row in eventa_out:
    write_file(row)
"""

