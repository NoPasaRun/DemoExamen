from db.connection import create_session
from db.models import User


def main():
    with create_session() as ses:
        user: User = User.get(ses, 1)


if __name__ == '__main__':
    main()
