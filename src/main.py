import sys
from settings import db_settings


def main(*args):
    print(db_settings.url)


if __name__ == '__main__':
    main(*sys.argv[1:])
