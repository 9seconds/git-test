# -*- coding: utf-8 -*-


import imp
import os.path
import sys

import pytest


def load_source(filename, module_name="module"):
    module = imp.new_module(module_name)

    with open(filename, "rt") as resource:
        content = resource.read()

    if sys.version_info.major == 2:
        exec content in module.__dict__
    else:
        exec(content, module.__dict__)

    sys.modules[module_name] = module

    return module



CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
GITTEST_FILENAME = os.path.join(CURRENT_DIR, "git-test")
GITTEST = load_source(GITTEST_FILENAME, "gittest")


class TestFunctions(object):

    @pytest.mark.parametrize("data", (
        {},
        {"lalala": 1},
        dict.fromkeys(map(str, range(10))),
        {"long": "line\n\n\n\n\nline"}
    ))
    def test_serialization(self, data):
        serialized = GITTEST.dict_to_base64(data)

        assert "\n" not in serialized
        assert GITTEST.base64_to_dict(serialized) == data
