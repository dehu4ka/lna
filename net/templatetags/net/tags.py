from django import template
import mistune
from pygments import highlight
from pygments.lexer import RegexLexer, bygroups
from pygments.formatters import HtmlFormatter
from pygments.token import *


# thx for nocproject.org for lexers

class NOCCiscoLexer(RegexLexer):
    name = "Cisco.IOS"
    tokens = {
        "root": [
            (r"^!.*", Comment),
            (r"(description)(.*?)$", bygroups(Keyword, Comment)),
            (r"(password|shared-secret|secret)(\s+[57]\s+)(\S+)", bygroups(Keyword, Number, String.Double)),
            (r"(ca trustpoint\s+)(\S+)", bygroups(Keyword, String.Double)),
            (r"^(interface|controller|router \S+|voice translation-\S+|voice-port)(.*?)$", bygroups(Keyword, Name.Attribute)),
            (r"^(dial-peer\s+\S+\s+)(\S+)(.*?)$", bygroups(Keyword, Name.Attribute, Keyword)),
            (r"^(vlan\s+)(\d+)$", bygroups(Keyword, Name.Attribute)),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"(\s+[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}\s+)", Number),  # MAC Address
            (r"^(?:no\s+)?\S+", Keyword),
            (r"\s+\d+\s+\d*|,\d+|-\d+", Number),
            (r".", Text),
        ],
    }


class NOCJuniperLexer(RegexLexer):
    name = "Juniper.JUNOS"
    tokens = {
        "root": [
            (r"#.*$", Comment),
            (r"//.*$", Comment),
            (r"/\*", Comment, "comment"),
            (r"\"", String.Double, "string"),
            (r"inactive:", Error),
            (r"(\S+\s+)(\S+\s+)({)", bygroups(Keyword, Name.Attribute, Punctuation)),
            (r"(\S+\s+)({)", bygroups(Keyword, Punctuation)),
            (r"https?://.*?[;]", String.Double),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"[;\[\]/:<>*{}]", Punctuation),
            (r"\d+", Number),
            (r".", Text)
        ],
        "comment": [
            (r"[^/*]", Comment),
            (r"/\*", Comment, "#push"),
            (r"\*/", Comment, "#pop"),
            (r"[*/]", Comment)
        ],
        "string": [
            (r".*\"", String.Double, "#pop")
        ]
    }


class NOCHuaweiLexer(RegexLexer):
    name = "Huawei.VRP"
    tokens = {
        "root": [
            (r"^#.*", Comment),
            (r"(description)(.*?)$", bygroups(Keyword, Comment)),
            (r"^(interface|ospf|bgp|isis|acl name)(.*?)$", bygroups(Keyword, Name.Attribute)),
            (r"^(vlan\s+)(\d+)$", bygroups(Keyword, Name.Attribute)),
            (r"^(vlan\s+)(\d+\s+)(to\s+)(\d+)$", bygroups(Keyword, Name.Attribute, Keyword, Name.Attribute)),
            (r"^(?:undo\s+)?\S+", Keyword),
            (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?", Number),  # IPv4 Address/Prefix
            (r"49\.\d{4}\.\d{4}\.\d{4}\.\d{4}\.\d{2}", Number),  # NSAP
            (r"\d+", Number),
            (r".", Text)
        ]
    }


class HighlightRenderer(mistune.Renderer):
    def __init__(self, vendor):
        super().__init__()
        self.vendor = vendor

    def block_code(self, code, lang):
        if self.vendor == 'Cisco':
            lexer = NOCCiscoLexer()
        elif self.vendor == 'Juniper':
            lexer = NOCJuniperLexer()
        elif self.vendor == 'Huawei':
            lexer = NOCHuaweiLexer()
        else:
            lexer = NOCCiscoLexer()
        formatter = HtmlFormatter()
        return highlight(code, lexer, formatter)


register = template.Library()


@register.filter
def markdown(value, vendor):
    value = '```pre\n' + value + '\n```'
    renderer = HighlightRenderer(vendor)
    markdown = mistune.Markdown(renderer=renderer)
    return markdown(value)
