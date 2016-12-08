import requests
import xml.etree.cElementTree as ET
from Exceptions import MethodImportError


def get_method(methodin, short=""):
    params = {'title': methodin, 'fields': 'pn|stage'}
    source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
    root = ET.fromstring(source.text)
    methodxml = root
    xmlns = '{http://methods.ringing.org/NS/method}'
    methoddata1 = methodxml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
    methoddata2 = methodxml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')
    if not short:
        short = methodin[:2]
    if len(methoddata1) != 0:
        stage = methodxml.find(xmlns + 'method/' + xmlns + 'stage').text
        notation = methoddata1[0].text
        le = methoddata1[1].text
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

    elif len(methoddata2) != 0:
        notation = methoddata2[0].text
        print(methodin)
        print('Notation:', notation)
        notation = notation.replace('-', '.-.').strip('.').split('.')
        return "{short} = +{notation}".format(short=short, notation=notation)
    else:
        raise MethodImportError