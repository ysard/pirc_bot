# -*- coding: utf-8 -*-
"""
Data caching used to avoid useless delay when a user refresh the website.
"""

# Standard imports
from threading import Thread
# Custom imports
from irc_bot import commons as cm
#from irc_bot import database as db

LOGGER = cm.logger()

class DataCaching(Thread):
    """Overriding the Thread class and only override the __init__()
    and run() methods of this class.

    https://docs.python.org/3.5/library/threading.html

    This class is used to load an independant thread ables to forge data
    according to the delay fixed in commons.py.

    Attributes:
        - private: _sqla_session
        - private: _forge_data, a callable used to interrogate database.
        - public: data, data ready to be used by Flask;
            A dictionary of all parameters used in the template.
            <dict>
    """

    def __init__(self, sqla_session, forge_data):
        """Constructor
        :param arg1: SQLAlchemy session.
        :param arg2: Callable used to interrogate database.
        :type arg1: <SQL session object>
        :type arg2: <callable>
        """
        Thread.__init__(self)

        self.data          = dict()
        self._sqla_session = sqla_session
        self._forge_data   = forge_data


    def run(self):
        """Heart of the class; This method forges data.

        Data is accessible by Flask from the public attribute self.data
        """

        import time
        LOGGER.info("Caching thread started !")

        while True:

            # Get all data
            # Make data visible from parent thread
            self.data = self._forge_data(self._sqla_session)

            # Wait 30 seconds before new processing
            time.sleep(cm.DELAY)

