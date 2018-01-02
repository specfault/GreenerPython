from os.path import isfile


def create_file(file):
    file.open(mode = 'w')


def test_create_file(tmpdir):
    source_file = tmpdir.join("bla.py")
    create_file(source_file)
    test_file  = tmpdir.join("test_bla.py")
    create_file(test_file)
    assert test_file.check() # check that file exists
