import requests
import logging
import xml.etree.cElementTree as ElementTree
from textwrap import dedent
from Exceptions import MethodImportError
from CompositionClasses import STAGE_DICT_INT_TO_STR

logger = logging.getLogger(__name__)

stages = {4: "minimus", 5: "doubles", 6: "minor", 7: "triples", 8: "major", 9: "caters", 10: "royal", 11: "cinques",
          12: "maximus", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}


class MethodCache:
    def __init__(self, file_name="MethodCache.siril"):
        self.cache = {}
        self.appended = {}
        self.file_name = file_name
        try:
            with open(self.file_name) as f:
                for line in f:
                    line = line.strip("\n")
                    if "=" in line:
                        title, pn = line.split("=")
                        notation, le = pn.split(",")
                        self.cache[title.strip()] = (notation.strip(), le.strip())
        except FileNotFoundError:
            # Create it
            with open(file_name, "w"):
                logger.info("Creating new method cache")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.appended:
            with open(self.file_name, "a") as f:
                f.write("".join(("\n{title} = {notation}, {le}".format(title=title, notation=notation, le=le)
                        for title, (notation, le) in self.appended.items())))
            self.appended = {}

    def get(self, method_title):
        # Set title case
        method_title = method_title.strip().title()
        if method_title in self.cache:
            return self.cache[method_title]
        else:
            params = {'title': method_title, 'fields': 'pn'}
            source = requests.get('http://methods.ringing.org/cgi-bin/simple.pl', params=params)
            root = ElementTree.fromstring(source.text)
            method_xml = root
            xmlns = '{http://methods.ringing.org/NS/method}'
            method_data_1 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'symblock')
            method_data_2 = method_xml.findall(xmlns + 'method/' + xmlns + 'pn/' + xmlns + 'block')

            if len(method_data_1) != 0:
                notation = "&" + method_data_1[0].text
                le = "&" + method_data_1[1].text
            elif len(method_data_2) != 0:
                notation = method_data_2[0].text
                le = ""
                # return "{short} = +{notation}, (p={short})".format(short=short, notation=notation)
            else:
                raise MethodImportError(method_title)
            self.cache[method_title] = (notation, le)
            self.appended[method_title] = (notation, le)
            return notation, le

method_cache = MethodCache()


def get_method(method_title, short=""):
    with method_cache as cache:
        notation = ""
        le = ""
        if method_title.lower().startswith("stedman"):
            for stage, name in stages.items():
                if stage % 2 and stage >= 7 and method_title.lower() == "stedman {}".format(name):
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
                if stage > 2 and method_title.lower() == "grandsire {}".format(name):
                    if not short:
                        short = "Gr"
                    notation = "+3.1, {n2} (+-.1) // - defaults to n when n is odd stage".format(n2=stage-2)
                    le = "+-.1"
                    break
        if not notation:
            notation, le = cache.get(method_title)

        if not short:
            short = method_title[:2]
        return dedent("""
                lh =
                finish = lh, (lh = ), finish //means lh affects exactly once at finish
                method = lh, {short}_pn, {short}_lh
                print_p =
                print_b = "- @"
                print_s = "s @"
                print_method = print_{short}
                print_{short} = "{short} \\"
                {short} = (method = lh, {short}_pn, {short}_lh, (print_method = print_{short})), method
                {short}_pn = {notation}
                {short}_lh = (p = (lh = {short}_p), {short}_full_lead), (b = (lh = {short}_b), {short}_full_lead),
                             (s = (lh = {short}_s), {short}_full_lead), (lh={short}_p)
                {short}_full_lead = (p = lh, {short}_pn, (lh = {short}_p)), (b = lh, {short}_pn, (lh = {short}_b)),
                                    (s = lh, {short}_pn, (lh = {short}_s))
                // Assign bob and single to desired place notation, e.g. bob = +4; single = +234
                // For different methods with different bobs add a dynamic assignment to the short method name
                // E.g for Belfast with 4ths place bobs, Glasgow with 6ths place
                // method Belfast Surprise "F"; method Glasgow Surprise "G";
                // F = F, (bob = +4); G = G, (bob = +6);
                // prove F, b, G, b
                {short}_p = {le}, print_p
                {short}_b = bob, print_b
                {short}_s = single, print_s
                """.format(short=short, notation=notation, le=le))
