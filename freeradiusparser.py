# -*- coding: utf-8 -*-
import codecs
import six

from pyparsing import (Literal, White, Word, alphanums, CharsNotIn, printables,
                       Forward, Group, OneOrMore, ZeroOrMore,
                       Suppress, pythonStyleComment, Regex)


class BaseParser(object):

    def get(self):
        """
        return the grouped config
        """
        return

    def get_dict(self):
        """
        return the parsed data as a dictionary
        """
        return

    def dump(self):
        """
        dump the data to stdout
        """
        return

    def format(self, dict_config):
        '''
        :return: The formatted data as it would be written to a file
        '''
        return
    
    def save(self, dict_config=None, outfile=None):
        if dict_config:
            output = self.format(dict_config)
            f = codecs.open(outfile, 'w', 'utf-8')
            for line in output.splitlines():
                f.write(line + "\n")
            f.close()


class ClientConfParser(BaseParser):
    key = Word(alphanums + "_")
    client_key = Word(alphanums + "-_/.:")
    LBRACE, RBRACE, EQUALS, HASH = map(Suppress, '{}=#')
    space = White().suppress()
    value = Word(printables, excludeChars='{}\n# \t')
    assignment = Group(key + EQUALS + value)
    intern_section = (LBRACE
                      + ZeroOrMore(assignment)
                      + RBRACE)
    named_section = Group(key + Group(intern_section))
    sections = Group(key + Group(intern_section | named_section))
    client_block = Forward()
    client_block << Group(Literal("client").suppress()
                          + client_key
                          + LBRACE
                          + Group(ZeroOrMore(assignment ^ sections))
                          + RBRACE)
    client_file = OneOrMore(client_block).ignore(pythonStyleComment)

    file_header = """# File parsed and saved by privacyidea.\n\n"""
    
    def __init__(self,
                 infile="/etc/freeradius/clients.conf",
                 content=None):
        self.file = None
        if content:
            self.content = content
        else:
            self.file = infile
            self._read()

    def _read(self):
        """
        Reread the contents from the disk
        """
        f = codecs.open(self.file, "r", "utf-8")
        self.content = f.read()
        f.close()
        
    def get(self):
        """
        return the grouped config
        """
        if self.file:
            self._read()
        config = self.client_file.parseString(self.content)
        return config
    
    def get_dict(self):
        '''
        return the client config as a dictionary.
        '''
        ret = {}
        config = self.get()
        for client in config:
            client_key = client.pop(0)
            client_config = {}
            for attribute in client:
                client_config.update(ClientConfParser._parse_entry(attribute))
            ret[client_key] = client_config
        return ret

    def dump(self):
        conf = self.get() or {}
        for client in conf:
            print("%s: %s" % (client[0], client[1]))

    def format(self, dict_config):
        '''
        :return: The formatted data as it would be written to a file
        '''
        output = u""
        output += self.file_header
        for client, attributes in dict_config.items():
            output += u"client %s {\n" % client
            output += ClientConfParser._format_entry(attributes)
            output += u"}\n\n"
        return output

    @staticmethod
    def _parse_entry(e):
        if isinstance(e, six.text_type):
            return e
        if isinstance(e, six.string_types):  # pragma: no cover
            return e.decode()
        if len(e) == 0:
            return {}
        return {k: ClientConfParser._parse_entry(v) for k, v in e}

    @staticmethod
    def _format_entry(e, s=False, lvl=4):
        ret = ''
        if len(e) == 0 and s:
            ret += u' {\n'
        for k, v in e.items():
            if isinstance(v, dict):
                if s:
                    ret += u' {0!s} {{\n'.format(k) \
                           + ClientConfParser._format_entry(v, s=False,
                                                            lvl=lvl)
                else:
                    ret += u' ' * lvl + u'{0!s}'.format(k) \
                           + ClientConfParser._format_entry(v, s=True,
                                                            lvl=lvl + 4) \
                           + u' ' * lvl + u'}\n'
            elif isinstance(v, six.string_types):
                if s:
                    ret += u' {\n'
                    s = False
                ret += u' ' * lvl + u'{0!s} = {1!s}\n'.format(k, v)
            else:  # pragma: no cover
                print('Error formatting freeradius client entry: '
                      'Unknown type: ' + str(type(v)) + ' ' + str(e))
        return ret


class UserConfParser(BaseParser):
    
    key = Word(alphanums + "-")
    username = Word(alphanums + "@_.-/")
    client_key = Word(alphanums + "-_/.:")
    space = White().suppress()
    comma = ","
    value = CharsNotIn("{}\n#, ")
    comment = "#"
    # operator = ":="
    operator = Regex(r":=|==|=|\+=|!=|>|>=|<|<=|=~|!~|=\*|!\*")
    assignment = Group(space
                       + key
                       + space.suppress()
                       + operator
                       + space.suppress()
                       + value
                       + ZeroOrMore(space).suppress()
                       + ZeroOrMore(comma).suppress())
    user_block = Forward()
    # USERNAME key operator value
    # <tab> key operator value
    user_block << Group(username
                        + space
                        + key
                        + operator
                        + space
                        + value
                        + Group(ZeroOrMore(assignment)))
    
    user_file = OneOrMore(user_block).ignore(pythonStyleComment)
    
    file_header = """# File parsed and saved by privacyidea.\n\n"""
    
    def __init__(self,
                 infile="/etc/freeradius/users",
                 content=None):
        self.file = None
        if content:
            self.content = content
        else:
            self.file = infile
            f = codecs.open(self.file, "r", "utf-8")
            self.content = f.read()
            f.close()
            
    def get(self):
        """
        return the grouped config
        
        something like this:
        [
        ['DEFAULT', 'Framed-Protocol', '==', 'PPP', [['Framed-Protocol', '=', 'PPP'], ['Framed-Compression', '=', 'Van-Jacobson-TCP-IP']]],
        ['DEFAULT', 'Hint', '==', '"CSLIP"', [['Framed-Protocol', '=', 'SLIP'], ['Framed-Compression', '=', 'Van-Jacobson-TCP-IP']]],
        ['DEFAULT', 'Hint', '==', '"SLIP"', [['Framed-Protocol', '=', 'SLIP']]]
        ]
        """
        config = self.user_file.parseString(self.content)
        return config

    def get_dict(self):
        pass

    def dump(self):
        pass

    def format(self, config):
        '''
        :return: The formatted data as it would be written to a file
        '''
        output = ""
        output += self.file_header
        for user in config:
            output += "%s %s %s %s\n" % (user[0], user[1], user[2], user[3])
            if len(user[4]):
                i = 0
                for reply_item in user[4]:
                    i += 1
                    output += "\t%s %s %s" % (reply_item[0],
                                              reply_item[1],
                                              reply_item[2])
                    if i < len(user[4]):
                        output += ","
                    output += "\n"
            output += "\n"
        return output
