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


def test_create_test_file_in_source_directory(tmpdir):
    """there's no 'tests' directory so the test file should be created next to the corresponding source file"""
    source_file = tmpdir.join("bla.py")
    create_file(source_file)
    test_file  = tmpdir.join("test_bla.py")
    assert test_file.check() # check that file exists



def test_create_test_file_inside_test_directory(tmpdir):
    """test directory in the same folder as the source file"""
    test_dir = tmpdir.mkdir('tests')
    source_file = tmpdir.join("bla.py")
    create_file(source_file)
    test_file  = test_dir.join("test_bla.py")
    assert test_file.check() # check that file exists


def test_create_test_file_inside_test_directory_further_up(tmpdir):
    """directory structure of source file should be duplicated inside tests"""
    source_dir = tmpdir.mkdir('blubb')
    test_dir = tmpdir.mkdir('tests')
    source_file = source_dir.join("bla.py")
    create_file(source_file)
    test_file  = test_dir.join('blubb').join("test_bla.py")
    assert test_file.check() # check that file exists


def test_create_test_file_directly(tmpdir):
    """creating a test file should not create a test for the test"""
    test_dir = tmpdir.mkdir('tests')
    source_file = tmpdir.join("test_bla.py")
    create_file(source_file)
    assert not test_dir.listdir() # no test for the test
