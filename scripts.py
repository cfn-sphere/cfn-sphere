import subprocess

def test():
    """
    Run all unittests. Equivalent to:
    `poetry run python -u -m unittest discover`
    """
    print(subprocess.run(
        ['nose2', '-v']
    ).stdout)