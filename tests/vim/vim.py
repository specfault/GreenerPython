import os
import subprocess
from py import path


environment = os.environ
# make sure we're testing with the current version of save_file
# don't use an older version that happens to be in PATH
environment['PATH'] = '.' + os.pathsep + environment['PATH']


def executing_file():
    return path.local(__file__)


def directory_of_executing_file():
    return path.local(executing_file().dirname)


def vim_escape(name):
    res = [el if el != ' ' else '\\ ' for el in name]
    return ''.join(res)


def save(file):
    dir = path.local(file.dirname)
    script = dir.join('vimsrcipt.txt')
    script.write(":e " + vim_escape(str(file)) + "\n" + ":wq\n")
    test_dir = directory_of_executing_file()
    vimrc = test_dir.join('.vimrc')
    command = ['vim', '-u', str(vimrc), '-s', str(script)]
    print(command)
    res = subprocess.call(command, env=environment)
    assert res == 0
