# -*- coding: utf-8 -*-

import logging
from irc_bot import info
from logging.handlers import RotatingFileHandler

# Directory paths
DIR_LOGS         = 'logs/'
DIR_DATA         = 'data/'

# Flask website paths
DIR_WEBSITE      = 'website_files/'
DIR_W_STATIC     = DIR_WEBSITE + 'static'
DIR_W_TEMPLATES  = DIR_WEBSITE + 'templates'

# Import config:
# Switch to True if you want to use Networkx.
# PS: the import of this lib on Raspberry Pi is a real problem...
USE_NETWORKX     = False

# IRC parameters
SERVER_URL       = "irc.freenode.net"
SERVER_PORT      = 6667
BOT_NAME         = "pirc_b"
BOT_REALNAME     = "pirc bot " + info.PACKAGE_VERSION + \
    " <http://pro-domo.ddns.net/pirc_bot>"
BOT_MESSAGE      = "#BIG Analytics " + info.PACKAGE_VERSION + \
    " - http://pro-domo.ddns.net/pirc_bot"
CHANNEL          = "#big_rennes"
#CHANNEL          = "#big_test"
# During the import, variables are filled with pseudodyms in corresponding files
ENABLE_USERS_WHITELIST = False
USERS_WHITELIST  = DIR_DATA + "pseudos_whitelist.txt"
ADMINS_LIST      = DIR_DATA + "admins.txt"
ADMINS_HOSTS_REG = ''

# Nginx prefix
NGINX_PREFIX     = "/pirc_bot"
# Don't touch that (it's the prefix of static files from web user point of view)
STATIC_PREFIX   = NGINX_PREFIX + '/static'

# Disable real-time generation of graphs
# A thread will be used to generate data,
# according to the following delay (in seconds)
ENABLE_REALTIME  = False
DELAY            = 40

# Logging
LOGGER_NAME      = info.PACKAGE_NAME
LOG_LEVEL        = logging.INFO

################################################################################
# IRC events - DON'T TOUCH THAT !
IRC_JOIN = 0
IRC_QUIT = 1
IRC_KICK = 2
IRC_MSG  = 3

# IRC config loading
def load_users(file):
    """Return a list of users in the given text file"""
    with open(file, 'r') as file:
        return {line.strip() for line in file}

def update_users():
    """Refresh the whitelist file with the current whitelist"""
    with open(DIR_DATA + "pseudos_whitelist.txt", 'w') as file:
        [file.write(user + '\n') for user in USERS_WHITELIST]

USERS_WHITELIST = load_users(USERS_WHITELIST)
ADMINS_LIST = load_users(ADMINS_LIST)
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




