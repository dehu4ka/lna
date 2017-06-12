import csv
from django.db import connection
from .models import ArgusADSL, ArgusFTTx, ArgusGPON
import re

tel_pattern = re.compile("\((\d+)\)(\d+)")
ip_pattern = re.compile("(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})")


def adsl_tel_num_to_int(tel_num):
    """
    Преобразует телефонный номер из вида (34936)30005 в 3493630005
    :param tel_num: телефонный номер со скобками на входе
    :return: телефонный номер в виде числа со скобками на выходе
    """
    m = re.search(tel_pattern, tel_num)
    if m:
        return int(m.group(1)+m.group(2))
    return ''


def fttx_tel_num_to_int(tel_num):
    if tel_num == '':
        return ''
    res = re.findall(r'\d+', tel_num)
    if res:
        res = res[-1]
    else:
        res = ''
    return res


def gpon_tel_num_to_int(tel_num):
    """
    Выдаём из строки типа (34936)IMS28321 телефонный номер
    :param tel_num: (34936)IMS28321
    :return: 3493628321
    """
    if tel_num == '':
        return ''
    res = re.findall(r'\d+', tel_num)
    out = ''
    if res:
        for some_string in res:
            out += some_string
    else:
        out = ''
    return out


def parse_iptv_login(raw_login):
    """
    Преобразует IPTV-логин в нормальный вид
    :param raw_login: IP-TV Smart TUBE089004932
    :return: 77089004932
    """
    if raw_login == '':
        return ''
    return '77'+raw_login[16:]


def parse_inet_login(raw_login):
    """
    Преобразует Интернет-логин в нормальный вид
    :param raw_login: СПД893623347
    :return: 77893623347
    """
    if raw_login == '':
        return ''
    return '77' + raw_login[3:]


def clear_xdsl_slot(slot):
    out = slot.replace('Порты ADSL2+_AnnexA - ', '')
    out = out.replace('Порты ADSL2_AnnexA - ', '')
    out = out.replace('Порты ADSL2+_AnnexB - ', '')
    out = out.replace('Порты ADSL2_AnnexB - ', '')
    out = out.replace('Порты ADSL_AnnexA - ', '')
    out = out.replace('Порты ADSL_AnnexB - ', '')
    if len(out) > 2:  # остаётся самый шлак...
        temp = out[-2:]  # берём последние три символа в надежде
        # Ищем цифры https://stackoverflow.com/questions/4289331/python-extract-numbers-from-a-string
        res = re.findall(r'\d+', temp)
        if res:
            res = res[-1]
            return res
        else:
            res = 0  # если не нашли - пишем 0
        # print(res, " <= ", temp, " <= ", out)
            return res
    return out


def get_ne_ip_from_hostname(hostname):
    m = re.findall(ip_pattern, hostname)
    if m:
        return m[0]
    return "0.0.0.0"


def clear_city(city):
    return city.replace('Ямало-Ненецкий АО, ', '')


def clear_hostname(hostname):
    # берём первые символы, оставляя за скобками IP. Скобки не входят в поиск.
    res = re.findall(r'(89-[0-9A-Za-z-]+)', hostname)
    if res:
        res = res[0]  # получаем hostname
    else:
        res = 'N/A'
    return res


def clear_fttx_port(port):
    if port == '':
        return ''
    res = re.findall(r'\d+', port)
    if res:
        res = res[-1]
    else:
        res = ''
    return res


def get_gpon_slot(slot):
    """
    Преобразует 89-GBKNSK-EDG110-O2 Huawei (мкр 14-й, 45)[10.228.102.249] - РО-2-3(1:8) - 12-44/1(1:8) в "2-3"
    :param slot:
    :return:
    """
    res = re.findall(r'[POРО]-(\d+-\d+)', slot) #  И русские и английские символы
    if res:
        res = res[-1]
    else:
        res = ''
    return res


def parse_adsl_csv(filename):
    cursor = connection.cursor()
    cursor.execute("TRUNCATE argus_ArgusADSL CASCADE;")

    # По одному объекты вставляются мееедленно. Будем вставлять пачкой
    records = list()

    # some filename hardcoding...
    with open('lna'+filename, encoding='windows-1251') as csv_file:
        reader = csv.reader(csv_file, delimiter=';', quotechar='"')
        next(reader)
        next(reader)
        next(reader)
        next(reader)  # Первые четыре строчки неинтересные. (Заголовки CSV)
        counter = 0
        for row in reader:
            client = ArgusADSL()
            client.city = clear_city(row[1])
            client.hostname = clear_hostname(row[2])
            client.ne_ip = row[3]
            if client.ne_ip == '':
                client.ne_ip = get_ne_ip_from_hostname(client.hostname)
            client.tel_num = adsl_tel_num_to_int(row[4])
            client.address = row[5]
            client.fio = row[6]
            client.room = row[7]
            client.iptv_login = parse_iptv_login(row[8])
            client.inet_login = parse_inet_login(row[9])
            client.slot = clear_xdsl_slot(row[10])
            client.port = row[11]
            records.append(client)
            counter += 1
            # break
        # Массовое добавление
        ArgusADSL.objects.bulk_create(records, batch_size=1000)
    return counter


def parse_gpon_csv(filename):
    cursor = connection.cursor()
    cursor.execute("TRUNCATE argus_ArgusGPON CASCADE;")

    # По одному объекты вставляются мееедленно. Будем вставлять пачкой
    records = list()

    # some filename/path hardcoding...
    with open('lna' + filename, encoding='windows-1251') as csv_file:
        reader = csv.reader(csv_file, delimiter=';', quotechar='"')
        next(reader)
        next(reader)
        next(reader)
        next(reader)  # Первые четыре строчки неинтересные. (Заголовки CSV)
        counter = 0
        ignored = 0
        for row in reader:
            client = ArgusGPON()
            client.address = row[18]
            client.fio = row[16]
            if client.address == '' or client.fio == '':  # Есть пустые строки, их игнорируем
                ignored += 1
            else:
                client.city = clear_city(row[1])
                client.hostname = clear_hostname(row[2])
                client.ne_ip = row[3]
                client.tel_num = gpon_tel_num_to_int(row[23])
                client.room = row[19]
                client.iptv_login = parse_iptv_login(row[22])
                client.inet_login = parse_inet_login(row[21])
                if row[5] != '':
                    client.slot = row[4] + '-' + row[5]  # Что-то типа 1-2 (на первой карте второй порт)
                else:
                    client.slot = get_gpon_slot(row[6])
                client.port = row[11]
                client.lira = row[20]
                records.append(client)
                counter += 1
                # break
        # Массовое добавление
        ArgusGPON.objects.bulk_create(records, batch_size=1000)
    return counter, ignored


def parse_fttx_csv(filename):
    cursor = connection.cursor()
    cursor.execute("TRUNCATE argus_ArgusFTTX CASCADE;")

    # По одному объекты вставляются мееедленно. Будем вставлять пачкой
    records = list()

    # some filename/path hardcoding...
    with open('lna' + filename, encoding='windows-1251') as csv_file:
        reader = csv.reader(csv_file, delimiter=';', quotechar='"')
        next(reader)
        next(reader)
        next(reader)
        next(reader)  # Первые четыре строчки неинтересные. (Заголовки CSV)
        counter = 0
        ignored = 0
        for row in reader:
            client = ArgusFTTx()
            client.address = row[12]
            client.fio = row[11]
            if client.address == '' or client.fio == '':  # Есть пустые строки, их игнорируем
                ignored += 1
            else:
                client.city = clear_city(row[1])
                client.hostname = clear_hostname(row[2])
                # Отдельного поля под IP нет
                client.ne_ip = get_ne_ip_from_hostname(row[2])
                client.tel_num = fttx_tel_num_to_int(row[10])
                client.room = row[13]
                client.iptv_login = parse_iptv_login(row[9])
                client.inet_login = parse_inet_login(row[8])
                # бесполезно на текущий момент. К тому же у нас нет коммутаторов со многими слотами (типа нет)
                client.slot = 0
                client.port = clear_fttx_port(row[5])
                client.lira = row[7]
                records.append(client)
                counter += 1
            # break
        # Массовое добавление
        ArgusFTTx.objects.bulk_create(records, batch_size=1000)
    return counter, ignored
