import subprocess
from py import path

def create_file(file):
    dir = path.local(file.dirname)
    script = dir.join('vimsrcipt.txt')
    script.write(":e " + str(file) + "\n" + ":wq\n")
    command = ['vim', '-s', str(script)]
    print(command)
    res = subprocess.call(command)
    assert res == 0


def test_create_file(tmpdir):
    source_file = tmpdir.join("bla.py")
    create_file(source_file)
    test_file  = tmpdir.join("test_bla.py")
    assert test_file.check() # check that file exists
