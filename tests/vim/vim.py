import os
import subprocess
from py import path


environment = os.environ
environment['PATH'] += os.pathsep + '.'


def executing_file():
    return path.local(__file__)


def directory_of_executing_file():
    return path.local(executing_file().dirname)


def save(file):
    dir = path.local(file.dirname)
    script = dir.join('vimsrcipt.txt')
    script.write(":e " + str(file) + "\n" + ":wq\n")
    test_dir = directory_of_executing_file()
    vimrc = test_dir.join('.vimrc')
    command = ['vim', '-u', str(vimrc), '-s', str(script)]
    print(command)
    res = subprocess.call(command, env=environment)
    assert res == 0
