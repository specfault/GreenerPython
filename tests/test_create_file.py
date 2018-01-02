from os.path import isfile


def create_file(name):
    with open(name, 'w') as f:
        f.close()


def test_create_file():
    source_file = "bla.py"
    create_file(source_file)
    test_file = "test_bla.py"
    create_file(test_file)
    assert isfile(test_file)
