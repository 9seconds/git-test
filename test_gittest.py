# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import contextlib
import fnmatch
import imp
import json
import os
import os.path
import posixpath
import shutil
import subprocess
import sys

import pytest


if sys.version_info.major == 2:
    to_str = unicode
else:
    to_str = str


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
"""Project directory."""

GITTEST_FILENAME = os.path.join(CURRENT_DIR, "git-test")
"""Filename of the script file."""

GITTEST = imp.load_source("gittest", GITTEST_FILENAME)
"""Module to test."""


@pytest.yield_fixture
def clean_directory(tmpdir):
    with tmpdir.as_cwd():
        yield tmpdir

    shutil.rmtree(tmpdir.strpath)


@pytest.fixture
def git_directory(clean_directory):
    git_call("init", "-q")
    git_call("config", "user.name", "user_name")
    git_call("config", "user.email", "user@name.com")

    return clean_directory


@pytest.fixture
def tool_configured(git_directory):
    prepare_gittest("ls -lAh")

    return git_directory


@contextlib.contextmanager
def git_commit():
    git_call("clean", "-xfdq")
    yield
    git_call("commit", "-aq", "-m", "wip")


def prepare_gittest(command):
    with git_commit():
        with open(".gittest", "wt") as filefp:
            json.dump(
                {GITTEST.TEST_TYPE_DEFAULT: {"command": command}},
                filefp)

        git_call("add", ".gittest")


def git_call(*args):
    output = subprocess.check_output(["git"] + list(args))
    output = output.rstrip()
    output = output.decode("utf-8")

    return output


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

    def test_iter_rstrip(self):
        for item in GITTEST.iter_rstrip(["a\n", "a\n\n", "a", "a\r\n"]):
            assert item == "a"


class TestGit(object):

    @pytest.fixture(autouse=True)
    def tool_configured(self, git_directory):
        prepare_gittest("ls -lAh")
        self.current_dir = git_directory

    def setup_method(self, method):
        self.git = GITTEST.Git()

    def test_toplevel_path(self):
        assert self.git.toplevel_path == self.current_dir.strpath

    def test_current_commit_sha(self):
        assert git_call("rev-parse", "HEAD") == self.git.current_commit_sha

    @pytest.mark.parametrize("test_class", (
        "",
        "default",
        "tox",
        "default_tox",
        "___"
    ))
    def test_ref_for(self, test_class):
        reference = self.git.ref_for(test_class)
        full_ref = posixpath.join("refs", "notes", reference)
        pull_rem_ref, pull_loc_ref = GITTEST.PullCommand.REFSPEC.split(":")

        assert reference.startswith(GITTEST.TEST_REFNS)
        assert fnmatch.fnmatch(full_ref, GITTEST.PushCommand.REFSPEC)
        assert fnmatch.fnmatch(full_ref, pull_rem_ref)
        assert fnmatch.fnmatch(full_ref, pull_loc_ref)

    def test_error_output(self):
        with pytest.raises(GITTEST.ProcessError):
            list(self.git.output("lasdf"))

    def test_status_untracked(self):
        self.current_dir.join("file").write_text("1", "utf-8")

        assert self.git.status() == {"file": "??"}

    def test_status_add(self):
        self.current_dir.join("file").write_text("1", "utf-8")
        git_call("add", "file")

        assert self.git.status() == {"file": "A"}

    def test_status_commited(self):
        with git_commit():
            self.current_dir.join("file").write_text("1", "utf-8")
            git_call("add", "file")

        assert self.git.status() == {}

    def test_status_modified(self):
        fileobj = self.current_dir.join("file")

        with git_commit():
            fileobj.write_text("1", "utf-8")
            git_call("add", "file")

        fileobj.write_text("22", "utf-8")

        assert self.git.status() == {"file": "M"}

    def test_status_deleted(self):
        fileobj = self.current_dir.join("file")

        with git_commit():
            fileobj.write_text("1", "utf-8")
            git_call("add", "file")

        fileobj.remove()

        assert self.git.status() == {"file": "D"}

    def test_status_ignored(self):
        fileobj = self.current_dir.join("file")

        with git_commit():
            fileobj.write_text("1", "utf-8")
            self.current_dir.join(".gitignore").write_text("file", "utf-8")
            git_call("add", ".gitignore")

        fileobj.write_text("22", "utf-8")

        assert self.git.status() == {}
