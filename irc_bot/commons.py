# -*- coding: utf-8 -*-

import logging
from irc_bot      import info
from logging.handlers   import RotatingFileHandler

# directory paths
DIR_LOGS                = 'logs/'
DIR_DATA                = 'data/'

# Logging
LOGGER_NAME             = info.PACKAGE_NAME
LOG_LEVEL               = logging.DEBUG

# IRC parameters
SERVER_URL = "irc.freenode.net"
SERVER_PORT = 6667
BOT_NAME = "pirc_bt"
BOT_REALNAME = "bt test"
#CHANNEL = "#big_test"
CHANNEL = "#big_rennes"

# IRC events
IRC_JOIN = 0
IRC_QUIT = 1
IRC_KICK = 2
IRC_MSG  = 3

# Nginx prefix in prod environment
# empty string on dev environment
NGINX_PREFIX = "/pirc_bot"

################################################################################

def logger(name=LOGGER_NAME, logfilename=None):
    """Return logger of given name, without initialize it.

    Equivalent of logging.getLogger() call.
    """
    return logging.getLogger(name)



_logger = logging.getLogger(LOGGER_NAME)
_logger.setLevel(LOG_LEVEL)

# log file
formatter    = logging.Formatter(
    '%(asctime)s :: %(levelname)s :: %(message)s'
)
file_handler = RotatingFileHandler(
    DIR_LOGS + LOGGER_NAME + '.log',
    'a', 1000000, 1
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)
_logger.addHandler(file_handler)

# terminal log
stream_handler = logging.StreamHandler()
formatter      = logging.Formatter('%(levelname)s: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(LOG_LEVEL)
_logger.addHandler(stream_handler)


def log_level(level):
    """Set terminal log level to given one"""
    handlers = (_ for _ in _logger.handlers
                if _.__class__ is logging.StreamHandler
               )
    for handler in handlers:
        handler.setLevel(level.upper())




