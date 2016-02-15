# -*- coding: utf-8 -*-

# Standard imports
import datetime
import os

# Custom imports
from irc_bot import commons

# SQL Alchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

LOGGER = commons.logger()

# /!\ initialization for SQL Alchemy Object Mapping
# /!\ This line MUST BE before Profile class that inherits from it
# /!\ This line MUST BE CALLED before any loading of SQL Engine
Base = declarative_base()

################################################################################
class SQLA_Wrapper():
    """Context manager for DB wrapper

    Auto flush & commit changes on exit.

    """

    def __init__(self, **kwargs):
        """Ability to reuse or not the database"""
        # Default: memory=False, reuse=True
        self._kwargs = kwargs

    def __enter__(self):
        """Get a pointer to SQL Alchemy session

        :return: SQLAlchemy session.
        :rtype: <SQL session object>
        """
        self._session = loading_sql(**self._kwargs)
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        """Check to see if it is ending with an exception.

        In this case, exception is raised within the with statement.
        => We do a session rollback.
        Otherwise we flush changes before commit them.

        """

        if (exc_type is not None) and (exc_type is not SystemExit):
            LOGGER.error("Rollback the database")
            self._session.rollback()
            return

        self._session.flush()
        self._session.commit()


def loading_sql(**kwargs):
    """Create an engine & create all the tables we need

    :param: Optional boolean allowing to reuse the database instead of deleting it.
    :type: <boolean>
    :return: session object
    :rtype: <Session()>

    """

    #Base = declarative_base() => see above, near imports
    # Create an engine and create all the tables we need

    # Erase DB file if already exists
    db_file = commons.DIR_DATA + 'bdd.sqlite'
    db_exists = os.path.isfile(db_file)

    if kwargs.get('reuse', True) is False and db_exists:
        os.remove(db_file)

    engine = create_engine('sqlite:///' + db_file, echo=False)
    # The pymysql DBAPI is a pure Python port of the MySQL-python (MySQLdb) driver, and targets 100% compatibility.
#    engine = create_engine('mysql+pymysql://root:@localhost/symfony')
    Base.metadata.create_all(engine)

    #returns an object for building the particular session you want

    #   bind=engine: this binds the session to the engine,
    #the session will automatically create the connections it needs.
    #   autoflush=True: if you commit your changes to the database
    #before they have been flushed, this option tells SQLAlchemy to flush them
    #before the commit is gone.
    #   autocommit=False: this tells SQLAlchemy to wrap all changes between
    #commits in a transaction. If autocommit=True is specified,
    #SQLAlchemy automatically commits any changes after each flush;
    #this is undesired in most cases.
    #   expire_on_commit=True: this means that all instances attached
    #to the session will be fully expired after each commit so that
    #all attribute/object access subsequent to a completed transaction
    #will load from the most recent database state.

    Session = scoped_session(sessionmaker(bind=engine, autoflush=True))

    return Session()

################################################################################
class Item():

    @classmethod
    def get_number(cls, session):
        """Return the number of objects stored in DB.

        :param arg1: SQLAlchemy session.
        :type arg1: <SQL session object>

        :return: Number of objects.
        :rtype: <int>

        """
        return session.query(cls).count()

    @classmethod
    def get_all(cls, session):
        """Get a list of all objects

        :param arg1: SQLAlchemy session.
        :type arg1: <SQL session object>

        :return: List of objects.
        :rtype: <list <Object>>

        """

        # Query for SQLite system
        return session.query(cls).all()


class Log(Base, Item):

    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)

    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    pseudo    = Column(String(50), nullable=False)
    event     = Column(Integer, nullable=False)

    # Unicity constraint
    # Note for MySQL, unicity & index is the same thing
    Index('index_1', 'event', 'pseudo', unique=True)

    def __init__(self, pseudo, event):
        """Constructor takes pseudo of the poster & the event type

        :param arg1: Poster's pseudo
        :param arg2: Event's type
        :type arg1: <str>
        :type arg2: <str>

        """
        self.pseudo = pseudo
        self.event = event

    def set_name(self, value):
        assert (value in AUTH_STATUS), "Integrity error: Bad Status name"
        self.name = value

    def __repr__(self):
        return "id:{}, timestamp:{}, pseudo:{}, event:{}".format(
                    self.id,
                    self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    self.pseudo,
                    self.event)


if __name__ == "__main__":

    with SQLA_Wrapper() as session:

        log = Log("test", 4)

        # Add object to SQLite DB
        session.add(log)
        session.commit()

        print("Nb logs:", Log.get_number(session))
        print("All logs:", session.query(Log).all())



