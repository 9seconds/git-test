# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import imp
import os
import os.path

import pytest


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
GITTEST_FILENAME = os.path.join(CURRENT_DIR, "git-test")
GITTEST = imp.load_source("gittest", GITTEST_FILENAME)


def teardown_module():
    try:
        os.remove(GITTEST_FILENAME + "c")
    except Exception:
        pass


class TestFunctions(object):

    @pytest.mark.parametrize("data", (
        {},
        {"lalala": 1},
        dict.fromkeys(map(str, range(10))),
        {"long": "line\n\n\n\n\nline"},
        {"юникод": "да"}
    ))
    def test_serialization(self, data):
        serialized = GITTEST.dict_to_base64(data)

        assert "\n" not in serialized
        assert GITTEST.base64_to_dict(serialized) == data

    def test_tmpfile(self):
        with GITTEST.tmpfile() as filename:
            assert os.path.isfile(filename)
            assert os.access(filename, os.R_OK | os.W_OK)

        assert not os.path.exists(filename)

    def test_unicode_filereader(self, tmpdir):
        fileobj = tmpdir.join("filename")
        fileobj.write_text("latin\nпривет", "utf-8")

        reader = GITTEST.unicode_filereader(fileobj.open(encoding="utf-8"))

        assert next(reader) == "latin\n"
        assert next(reader) == "привет"
