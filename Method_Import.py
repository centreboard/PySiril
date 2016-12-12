import requests
import xml.etree.cElementTree as ElementTree
from textwrap import dedent
from Exceptions import MethodImportError
from CompositionClasses import STAGE_DICT_INT_TO_STR

stages = {4: "minimus", 5: "doubles", 6: "minor", 7: "triples", 8: "major", 9: "caters", 10: "royal", 11: "cinques",
          12: "maximus", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}


def get_method(method_title, short=""):
    if method_title.lower().startswith("stedman"):
        for stage, name in stages.items():
            if stage % 2 and method_title.lower() == "stedman {}".format(name):
                if not short:
                    short = "St"
                return dedent("""
                {short} = +3.1, "  @", (p = {short}_p), (b = {short}_b), (s = {short}_s)
                six = slow
                quick = +1.3.1.3.1, (six = slow)
                slow =  +3.1.3.1.3, (six = quick)
                {short}_p = +{n}, six, "  @"
                {short}_b = +{n2}, six, "- @"
                {short}_s = +{n2}{n1}{n}, six, "s @"
                """.format(short=short, n=STAGE_DICT_INT_TO_STR[stage], n1=STAGE_DICT_INT_TO_STR[stage - 1],
                           n2=STAGE_DICT_INT_TO_STR[stage - 2]))
    params = {'title': method_title, 'fields': 'pn'}
    source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
    root = ElementTree.fromstring(source.text)
    method_xml = root
    xmlns = '{http://methods.ringing.org/NS/method}'
    method_data_1 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
    method_data_2 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')
    if not short:
        short = method_title[:2]
    if len(method_data_1) != 0:
        notation = method_data_1[0].text
        le = method_data_1[1].text
        return dedent("""
        lh = ""
        finish = lh, finish
        method = {short}
        {short} = (method = lh, {short}_pn, {short}_lh), method
        {short}_pn = &{notation}
        {short}_lh = (p = lh = {short}_p), (b = lh = {short}_b), (s = lh = {short}_s), (lh={short}_p)
        {short}_p = &{le}
        {short}_b = bob, "- @"
        {short}_s = single, "s @\"""".format(short=short, notation=notation, le=le))

    elif len(method_data_2) != 0:
        notation = method_data_2[0].text
        return "{short} = +{notation}, (p={short})".format(short=short, notation=notation)
    else:
        raise MethodImportError(method_title)
