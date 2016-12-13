import requests
import xml.etree.cElementTree as ElementTree
from textwrap import dedent
from Exceptions import MethodImportError
from CompositionClasses import STAGE_DICT_INT_TO_STR

stages = {4: "minimus", 5: "doubles", 6: "minor", 7: "triples", 8: "major", 9: "caters", 10: "royal", 11: "cinques",
          12: "maximus", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}


def get_method(method_title, short=""):
    notation = ""
    le = ""
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
    elif method_title.lower().startswith("grandsire"):
        for stage, name in stages.items():
            if stage % 2 and method_title.lower() == "grandsire {}".format(name):
                if not short:
                    short = "Gr"
                notation = "+3.1, {n2} (+{n}.1)".format(n2=stage-2, n=stage)
                le = "+{n}.1".format(n=stage)
                break
    if not notation:
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
        elif len(method_data_2) != 0:
            notation = method_data_2[0].text
            le = ""
            #return "{short} = +{notation}, (p={short})".format(short=short, notation=notation)
        else:
            raise MethodImportError(method_title)
    return dedent("""
        lh = ""
        finish = lh, (lh = ""), finish //means lh affects exactly once at finish for any number of methods imported
        method = lh, {short}_pn, {short}_lh
        {short} = (method = lh, {short}_pn, {short}_lh), method
        {short}_pn = {notation}
        {short}_lh = (p = (lh = {short}_p), {short}_full_lead), (b = (lh = {short}_b), {short}_full_lead),
                     (s = (lh = {short}_s), {short}_full_lead), (lh={short}_p)
        {short}_full_lead = (p = lh, {short}_pn, (lh = {short}_p)), (b = lh, {short}_pn, (lh = {short}_b)),
                            (s = lh, {short}_pn, lh = {short}_pn)
        // Assign bob and single to desired place notation, e.g. bob = +4; single = +234
        // For different methods with different bobs add a dynamic assignment to the short method name
        // E.g for Belfast with 4ths place bobs, Glasgow with 6ths place
        // method Belfast Surprise "F"; method Glasgow Surprise "G";
        // F = F, (bob = +4); G = G, (bob = +6);
        // prove F, b, G, b
        // Recommend to overwrite below assignments to change lead end behaviour
        {short}_p = {le}
        {short}_b = bob, "- @"
        {short}_s = single, "s @"
        """.format(short=short, notation=notation, le=le))
