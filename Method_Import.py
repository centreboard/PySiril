import requests
import xml.etree.cElementTree as ElementTree
from Exceptions import MethodImportError

stages = {4:"minimus", 5:"doubles", 6:"minor", }#"triples": 7, "major": 8, "caters": 9, "royal": 10, "cinques": 11,
         # "maximus": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16}


def get_method(method_title, short=""):
    params = {'title': method_title, 'fields': 'pn|stage'}
    source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
    root = ElementTree.fromstring(source.text)
    method_xml = root
    xmlns = '{http://methods.ringing.org/NS/method}'
    method_data_1 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
    method_data_2 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')
    if not short:
        short = method_title[:2]
    if len(method_data_1) != 0:
        stage = method_xml.find(xmlns + 'method/' + xmlns + 'stage').text
        notation = method_data_1[0].text
        le = method_data_1[1].text
        # print(methodin)
        # print('Notation: &', notation, sep='')
        # print('Lead End:', le)
        if le[-1] == stage:
            bob = str(int(stage) - 2)
            single = "{}{}{}".format(str(int(stage) - 2), str(int(stage) - 1), stage)
        else:
            # TODO: better handling of other le, particularly gradsire and stedman
            bob = "4"
            single = "1234"
        return """{short} = &{notation}, &{le}\n{short}_b = &{notation}, &{bob}
{short}_s = &{notation}, &{single}""".format(short=short, notation=notation, bob=bob, le=le, single=single)

    elif len(method_data_2) != 0:
        notation = method_data_2[0].text
        return "{short} = +{notation}".format(short=short, notation=notation)
    else:
        raise MethodImportError
