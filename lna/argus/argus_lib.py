import csv
from django.db import connection
from .models import ArgusADSL
import re

tel_pattern = re.compile("\((\d+)\)(\d+)")
ip_pattern = re.compile("[(\[](10.+)[)\]]")  # Все IP начинаются на 10

def tel_num_to_int(tel_num):
    """
    Преобразует телефонный номер из вида (34936)30005 в 3493630005
    :param tel_num: телефонный номер со скобками на входе
    :return: телефонный номер в виде числа со скобками на выходе
    """
    m = re.search(tel_pattern, tel_num)
    if m:
        return int(m.group(1)+m.group(2))
    return -1


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


def clear_slot(slot):
    return slot.replace('Порты ADSL2+_AnnexA - ', '')


def get_ne_ip_from_hostname(hostname):
    m = re.search(ip_pattern, hostname)
    if m:
        return m.group(1)
    return "0.0.0.0"


def clear_city(city):
    return city.replace('Ямало-Ненецкий АО, ', '')

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
        for row in reader:
            client = ArgusADSL()
            client.city = clear_city(row[1])
            client.hostname = row[2]
            client.ne_ip = row[3]
            if client.ne_ip == '':
                client.ne_ip = get_ne_ip_from_hostname(client.hostname)
            client.tel_num = tel_num_to_int(row[4])
            client.address = row[5]
            client.fio = row[6]
            client.room = row[7]
            client.iptv_login = parse_iptv_login(row[8])
            client.inet_login = parse_inet_login(row[9])
            client.xdsl_slot = clear_slot(row[10])
            client.xdsl_port = row[11]
            records.append(client)
            # break
        # Массовое добавление
        ArgusADSL.objects.bulk_create(records, batch_size=1000)
    pass


def parse_gpon_csv(filename):
    pass

def parse_fttx_csv(filename):
    pass
