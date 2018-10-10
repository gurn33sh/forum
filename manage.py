import os
import unittest

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from forum import app, db
from utils.populate import generate_data


#app = create_app(config_name=os.environ.get('APP_SETTINGS'))
manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)

# check if the environment configuration is production
is_prod = (os.environ.get('APP_SETTINGS') == 'production')


@manager.command
def createdb():
    """Creates the db tables"""
    db.create_all()
    db.session.commit()


@manager.command
def dropdb():
    """Drop all db tables"""
    db.drop_all()


@manager.command
def resetdb():
    """Reset all db tables"""
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.command
def populate():
    """Populate some data"""
    resetdb()
    generate_data()


@manager.command
def test(type=""):
    """Run the unit tests without code coverage."""
    try:
        tests = unittest.TestLoader().discover(
            f'tests/{type}',
            pattern='test*.py'
        )
        result = unittest.TextTestRunner(verbosity=2).run(tests)
        if result.wasSuccessful():
            return 0
        return 1
    except ImportError:
        print("There is no test like that!")


if __name__ == "__main__":
    manager.run()
