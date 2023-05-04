import os


class Env:

    def __init__(self):
        return

    @staticmethod
    def get_directory_separator():
        return '/' if os.name not in ['nt'] else '\\'

    @staticmethod
    def get_home_dir():
        return os.path.expanduser('~')

    @staticmethod
    def get_home_download_dir():
        return os.path.expanduser('~') + '/Downloads'


if __name__ == '__main__':
    print(Env.get_home_dir())
    exit(0)
