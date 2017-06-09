import csv


def parse_adsl_csv(filename):
    print("Trying to PARSE ADSL with file: "+filename)
    # some filename hardcoding...
    with open('lna'+filename, encoding='windows-1251') as csv_file:
        reader = csv.reader(csv_file, delimiter=';', quotechar='"')
        next(reader)
        next(reader)
        next(reader)
        next(reader)  # Первые четыре строчки неинтересные.
        for row in reader:
            print(row)
            break
    pass


def parse_gpon_csv(filename):
    pass

def parse_fttx_csv(filename):
    pass
