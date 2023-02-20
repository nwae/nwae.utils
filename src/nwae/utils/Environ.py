import os


class Environ:

    def __init__(self):
        return

    @staticmethod
    def get_home_dir():
        return os.path.expanduser('~')


if __name__ == '__main__':
    print(Environ.get_home_dir())
    exit(0)
