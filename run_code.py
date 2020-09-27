import textwrap
# we actually do use sys but this is not obvious to flake8
import sys  # noqa: F401

source = [None]
source_name2 = [None]
test = [None]


g = globals()
local_variables = locals()


def check(name, source_code, test_code):
    tmp = test_code.split("\n")
    SUT_import = f"import {name}"
    contains_SUT_import = True in [SUT_import in el for el in tmp]
    tmp = [el for el in tmp if SUT_import not in el]
    test[0] = '\n'.join(tmp)
    source[0] = source_code
    source_name2.insert(0, name)
    local_variables.pop(source_name2[0], None)
    # make sure you don't include unittest
    # this way, we notice if the test code forgets to include it
    # I couldn't find a way to unittest this
    # probably because unittest is imported practically  everywhere
    # also, imports seem to leak like crazy
    # apparently, I haven't fully understood Python's module system
    code = textwrap.dedent("""
        from types import ModuleType

        """)
    if contains_SUT_import:
        code += textwrap.dedent(f"""
            {source_name2[0]} = ModuleType(source_name2[0])
            exec(source[0], globals(), {source_name2[0]}.__dict__)
            """)
    code += textwrap.dedent("""
        exec(test[0], globals(), locals())
        suite = unittest.defaultTestLoader.loadTestsFromModule(
            sys.modules[__name__])
        res = unittest.TestResult()
        suite.run(res)
        """)
    try:
        exec(code, g, local_variables)
    except Exception as e:
        return str(e)
    tmp = local_variables['res'].errors
    if tmp:
        return tmp[0][1]
    return None
