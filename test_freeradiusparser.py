# -*- coding: utf-8 -*-
#
#    privacyIDEA Account test suite
# 
#    Copyright (C)  2014 Cornelius Kölbel, cornelius@privacyidea.org
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import os
import pytest
import json
from collections import OrderedDict
from six.moves.urllib.request import urlopen
from .freeradiusparser import ClientConfParser, UserConfParser, BaseParser

SIMPLE_CLIENTS_CONF_TEST_FILE = 'testdata/clients.conf'
FILEOUTPUT_SIMPLE_CLIENTS_CONF = u"""# File parsed and saved by privacyidea.

client localhost {
    ipaddr = 127.0.0.1
    nastype = other
    secret = testing123
    shortname = localhost
}

client private-network-1 {
    ipaddr = 192.168.0.0
    netmask = 24
    secret = testing123-1
    shortname = private-network-1
}

"""

CLIENTS_CONF_TEST_FILE = 'testdata/test_clients.conf'
FILEOUTPUT_CLIENTS_CONF_TEST = u"""# File parsed and saved by privacyidea.

client 127.0.0.1 {
    limit {
        lifetime = 0
    }
    nastype = other
    secret = testing123
    shortname = localhost
}

client 127.0.0.2 {
    limit {
    }
    nastype = other
    secret = testing123
    shortname = localhost
}

client 127.0.0.3 {
    limit foo {
        lifetime = 0
    }
    nastype = other
    secret = testing123
    shortname = localhost
}

client 127.0.0.4 {
    limit foo {
    }
    nastype = other
    secret = testing123
    shortname = localhost
}

client foo {
    limit baz {
        lifetime = 1
    }
    nastype = other
    secret = testing123
    shortname = bar
}

"""

CLIENTS_CONF_RAD30_FILE = 'testdata/rad30_clients.conf'
FILEOUTPUT_RAD30 = u"""# File parsed and saved by privacyidea.

client localhost {
    ipaddr = 127.0.0.1
    limit {
        idle_timeout = 30
        lifetime = 0
        max_connections = 16
    }
    nas_type = other
    proto = *
    require_message_authenticator = no
    secret = testing123
}

client localhost_ipv6 {
    ipv6addr = ::1
    secret = testing123
}

"""

CLIENTS_CONF_CURRENT_URL = 'https://raw.githubusercontent.com/FreeRADIUS/freeradius-server/master/raddb/clients.conf'
FILEOUTPUT_CURRENT = u"""# File parsed and saved by privacyidea.

client localhost {
    ipaddr = 127.0.0.1
    limit {
        idle_timeout = 30
        lifetime = 0
        max_connections = 16
    }
    proto = *
    require_message_authenticator = no
    secret = testing123
}

client localhost_ipv6 {
    ipv6addr = ::1
    secret = testing123
}

"""


USER_CONF_A = """
DEFAULT Auth-Type := perl
"""

USER_CONF_B = """
administrator Cleartext-Password := "secret"
"""

USER_CONF_C = """
user somekey == value
"""
USER_CONF_D = """
DEFAULT    Hint == "SLIP"
    Framed-Protocol = SLIP
"""

USER_CONF_E = """
DEFAULT    Hint == "SLIP"
    Framed-Protocol = SLIP,
    Something = Else
"""

USER_CONF_RAD30_FILE = 'testdata/users_rad30'
USER_CONF_CURRENT_URL = 'https://raw.githubusercontent.com/FreeRADIUS/freeradius-server/v3.0.x/raddb/mods-config/files/authorize'

FILEOUTPUT_USER_ORIG = u"""# File parsed and saved by privacyidea.

DEFAULT Framed-Protocol == PPP
\tFramed-Protocol = PPP,
\tFramed-Compression = Van-Jacobson-TCP-IP

DEFAULT Hint == "CSLIP"
\tFramed-Protocol = SLIP,
\tFramed-Compression = Van-Jacobson-TCP-IP

DEFAULT Hint == "SLIP"
\tFramed-Protocol = SLIP

"""

SIMPLE_USER_CONF_FILE = 'testdata/users'


class TestBaseParser(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def test_base_parser(self):
        bp = BaseParser()
        r = bp.get()
        self.assertEqual(r, None)
        r2 = bp.get_dict()
        assert r2 is None
        bp.dump()
        captured = self.capsys.readouterr()
        assert captured.out == ''
        r = bp.format({})
        self.assertEqual(r, None)

        # do nothing
        bp.save({}, "test.out")
        assert not os.path.exists('test.out')


class TestFreeRADIUSParser(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        pass
    
    def test_clients_conf_simple(self):
        CP = ClientConfParser(infile='testdata/clients.conf')
        config = CP.get_dict()
        self.assertTrue("localhost" in config)
        self.assertTrue("private-network-1" in config)
        self.assertEqual(config.get("private-network-1").get("secret"),
                         "testing123-1")
        self.assertEqual(config.get("private-network-1").get("shortname"),
                         "private-network-1")

    def test_clients_conf_simple_dump(self):
        cp = ClientConfParser(infile='testdata/clients.conf')
        cp.dump()
        captured = self.capsys.readouterr()
        assert "private-network-1: [[" in captured.out
        assert "testing123-1']," in captured.out

    def test_clients_conf_current_from_github(self):
        # load the raw clients.conf from the freeRADIUS github page
        # and compare it with a local version. This way we know if something
        # changed in the original
        try:
            response = urlopen(CLIENTS_CONF_CURRENT_URL)
        except RuntimeError as e:  # pragma: no cover
            print(e)
            pytest.xfail('Could not get data from net!')

        content = response.read().decode()
        CP = ClientConfParser(content=content)
        config = CP.get_dict()
        assert "localhost" in config
        assert "localhost_ipv6" in config
        assert "127.0.0.1" not in config
        self.assertEqual(config.get("localhost").get("secret"),
                         "testing123")
        self.assertEqual(config.get("localhost").get("ipaddr"),
                         "127.0.0.1")
        assert config['localhost']['limit']['max_connections'] == '16'
        # this is a dirty hack to get reproducible results
        cfg = json.loads(json.dumps(config, sort_keys=True),
                         object_pairs_hook=OrderedDict)
        assert CP.format(cfg) == FILEOUTPUT_CURRENT
        
    def test_clients_conf_original_freerad30(self):
        cp = ClientConfParser(infile=CLIENTS_CONF_RAD30_FILE)
        config = cp.get_dict()
        self.assertIn('localhost', config, config)
        self.assertIn('localhost_ipv6', config, config)
        # this is a dirty hack to get reproducible results
        cfg = json.loads(json.dumps(config, sort_keys=True),
                         object_pairs_hook=OrderedDict)
        assert cp.format(cfg) == FILEOUTPUT_RAD30

    def test_clients_conf_with_sections(self):
        cp = ClientConfParser(infile=CLIENTS_CONF_TEST_FILE)
        config = cp.get_dict()
        assert 'foo' in config
        assert 'lifetime' in config['127.0.0.1']['limit']
        assert len(config['127.0.0.2']['limit']) == 0
        assert 'lifetime' in config['127.0.0.3']['limit']['foo']
        assert isinstance(config['127.0.0.4']['limit']['foo'], dict)
        assert len(config['127.0.0.4']['limit']['foo']) == 0
        # this is a dirty hack to get reproducible results
        cfg = json.loads(json.dumps(config, sort_keys=True),
                         object_pairs_hook=OrderedDict)
        assert cp.format(cfg) == FILEOUTPUT_CLIENTS_CONF_TEST

    def test_save_file(self):
        tmpfile = "./tmp-output"
        CP = ClientConfParser(infile=SIMPLE_CLIENTS_CONF_TEST_FILE)
        config = CP.get_dict()
        # this is a dirty hack to get reproducible results
        cfg = json.loads(json.dumps(config, sort_keys=True),
                         object_pairs_hook=OrderedDict)
        CP.save(cfg, tmpfile)
        f = open(tmpfile, "r")
        output = f.read()
        f.close()
        os.unlink(tmpfile)
        self.assertEqual(output, FILEOUTPUT_SIMPLE_CLIENTS_CONF)
        

class TestFreeRADIUSUsers(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def capsys(self, capsys):
        self.capsys = capsys

    def setUp(self):
        pass
    
    def test_users_basic(self):
        UP = UserConfParser(content=USER_CONF_A)
        config = UP.get()
        self.assertEqual(config[0][0], "DEFAULT")
        self.assertEqual(config[0][1], "Auth-Type")
        self.assertEqual(config[0][2], ":=")
        self.assertEqual(config[0][3], "perl")
        # get_dict isn't implemented
        r1 = UP.get_dict()
        assert r1 is None

    def test_users_password(self):
        UP = UserConfParser(content=USER_CONF_B)
        config = UP.get()
        self.assertEqual(config[0][0], "administrator")
        self.assertEqual(config[0][1], "Cleartext-Password")
        self.assertEqual(config[0][2], ":=")
        self.assertEqual(config[0][3], '"secret"')
        
    def test_operators(self):
        UP = UserConfParser(content=USER_CONF_C)
        config = UP.get()
        self.assertEqual(config[0][0], "user")
        self.assertEqual(config[0][1], "somekey")
        self.assertEqual(config[0][2], "==")
        self.assertEqual(config[0][3], 'value')

    def test_reply_items(self):
        UP = UserConfParser(content=USER_CONF_D)
        config = UP.get()
        # [['DEFAULT', 'Hint', '==', '"SLIP"',
        #  [['Framed-Protocol', '=', 'SLIP']]]
        # ]

        self.assertEqual(config[0][0], "DEFAULT")
        self.assertEqual(config[0][1], "Hint")
        self.assertEqual(config[0][2], "==")
        self.assertEqual(config[0][3], '"SLIP"')
        self.assertEqual(config[0][4][0][0], 'Framed-Protocol')
        self.assertEqual(config[0][4][0][1], '=')
        self.assertEqual(config[0][4][0][2], 'SLIP')
        
    def test_reply_items2(self):
        UP = UserConfParser(content=USER_CONF_E)
        config = UP.get()
        # [['DEFAULT', 'Hint', '==', '"SLIP"',
        #  [['Framed-Protocol', '=', 'SLIP']]]
        # ]

        self.assertEqual(config[0][0], "DEFAULT")
        self.assertEqual(config[0][1], "Hint")
        self.assertEqual(config[0][2], "==")
        self.assertEqual(config[0][3], '"SLIP"')
        self.assertEqual(config[0][4][0][0], 'Framed-Protocol')
        self.assertEqual(config[0][4][0][1], '=')
        self.assertEqual(config[0][4][0][2], 'SLIP')
        self.assertEqual(config[0][4][1][0], 'Something')
        self.assertEqual(config[0][4][1][1], '=')
        self.assertEqual(config[0][4][1][2], 'Else')
    
    def test_get_complete(self):
        UP = UserConfParser(infile=USER_CONF_RAD30_FILE)
        config = UP.get()
        self.assertEqual(len(config), 3)
        self.assertEqual(len(config[0][4]), 2)
        self.assertEqual(len(config[1][4]), 2)
        self.assertEqual(len(config[2][4]), 1)
        
    def test_save_file(self):
        tmpfile = "./tmp-output"
        UP = UserConfParser(infile=USER_CONF_RAD30_FILE)
        config = UP.get()
        UP.save(config, tmpfile)
        f = open(tmpfile, "r")
        output = f.read()
        f.close()
        os.unlink(tmpfile)
        self.assertEqual(output, FILEOUTPUT_USER_ORIG)

    def test_read_user_from_file(self):
        UP = UserConfParser(infile=SIMPLE_USER_CONF_FILE)
        config = UP.get()
        user1 = config[0]
        user2 = config[1]
        self.assertEqual(user1[0], "administrator")
        self.assertEqual(user2[0], "DEFAULT")

        # Just dump it, dump() currently does nothing
        UP.dump()
        captured = self.capsys.readouterr()
        assert captured.out == ''

    def test_current_user_config_from_github(self):
        try:
            response = urlopen(USER_CONF_CURRENT_URL)
        except RuntimeError as e:  # pragma: no cover
            print(e)
            pytest.xfail('Could not get data from net!')

        content = response.read().decode()
        up = UserConfParser(content=content)
        output = up.format(up.get())
        assert output == FILEOUTPUT_USER_ORIG
