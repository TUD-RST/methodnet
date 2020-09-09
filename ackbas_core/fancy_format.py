import dataclasses
import re
import yaml

class ParseException(Exception):
    def __init__(self, msg):
        self.msg = msg


class Token:
    @dataclasses.dataclass
    class TokenType:
        regexp: str

    KW_TYPE = TokenType(r"type")
    KW_METHOD = TokenType(r"method")
    COLON = TokenType(r":")
    COMMA = TokenType(r",")
    ARROW = TokenType(r"->")
    IDENTIFIER = TokenType(r"[\wÄÖÜäöü](?:[\wÄÖÜäöü\- ]*[\wÄÖÜäöü])?")
    COMMENT = TokenType(r"#.*\n")
    QUOTED_STRING = TokenType(r'"[^"]*"')

    def __init__(self, type, string):
        self.type = type
        self.string = string

    def __str__(self):
        return f"Token({self.string})"


TOKEN_TYPES = [Token.KW_TYPE,
               Token.KW_METHOD,
               Token.COLON,
               Token.COMMA,
               Token.ARROW,
               Token.COMMENT,
               Token.IDENTIFIER,
               Token.QUOTED_STRING]


def parse_file(fname):
    # Lex

    with open(fname, 'r', encoding='utf8') as f:
        file_str = f.read()

    tokens = []

    cursor = 0

    while cursor < len(file_str):
        current_substr = file_str[cursor:]
        match_result = re.match(r"\s*", current_substr)
        cursor += match_result.end()

        if cursor >= len(file_str):
            break  # file ended with whitespace

        current_substr = file_str[cursor:]
        for tt in TOKEN_TYPES:
            match_result = re.match(tt.regexp, current_substr)
            if match_result:
                matched_str = match_result.group()
                tokens.append(Token(tt, matched_str))
                cursor += match_result.end()
                break
        else:
            raise ParseException("No token match found for " + current_substr)

    # Parse

    types = {}
    methods = {}

    cursor = 0

    def has_next():
        nonlocal cursor
        return cursor < len(tokens)

    def next():
        if has_next():
            nonlocal cursor
            cursor += 1
            return tokens[cursor - 1]
        else:
            return None

    def peek():
        if has_next():
            nonlocal cursor
            return tokens[cursor]
        else:
            return None

    def match(tt):
        if has_next() and peek().type == tt:
            return next()
        else:
            return None

    def expect(tt):
        assert has_next() and peek().type == tt
        return next()

    def parse_comma_list():
        result_list = [expect(Token.IDENTIFIER).string]
        while match(Token.COMMA):
            result_list.append(expect(Token.IDENTIFIER).string)

        return result_list

    while cursor < len(tokens):
        if match(Token.KW_TYPE):
            type_name = expect(Token.IDENTIFIER).string
            if match(Token.COLON):
                super_class_names = parse_comma_list()
            else:
                super_class_names = []

            maybe_description = match(Token.QUOTED_STRING)
            if maybe_description:
                description_string = maybe_description.string[1:-1]
            else:
                description_string = ""

            types[type_name] = {'super': super_class_names, 'description': description_string}
        elif match(Token.KW_METHOD):
            method_name = expect(Token.IDENTIFIER).string
            expect(Token.COLON)
            input_names = parse_comma_list()
            expect(Token.ARROW)
            output_names = parse_comma_list()

            maybe_description = match(Token.QUOTED_STRING)
            if maybe_description:
                description_string = maybe_description.string[1:-1]
            else:
                description_string = ""

            methods[method_name] = {'inputs': input_names, 'outputs': output_names, 'description': description_string}
        elif match(Token.COMMENT):
            pass
        else:
            raise ParseException("Unexpected token")

    return types, methods


def write_as_yaml(fname, types, methods):
    yaml_content = {
        'types': types,
        'methods': methods
    }

    with open(fname, 'w', encoding='utf8') as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
