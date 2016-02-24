# -*- coding: utf-8 -*-
"""
This modules handles the IRC connection.
The class IRCAnalytics is the heart of this program.
It saves all events in database.
"""

# Standard imports
import datetime
import re
from shutil import copyfile
from functools import wraps
from irc.bot import *
# Tuto:
# https://openclassrooms.com/courses/programmer-un-bot-irc-simplement-avec-ircbot
# IRC events:
# https://github.com/jaraco/irc/blob/08777757fa513b9d7443d07fa801c6e8dc9c97e4/irc/events.py

# Custom imports
from irc_bot import commons as cm
from irc_bot import database as db

LOGGER = cm.logger()


def param_not_none(func):
    """Decorator which verifies if the third positional parameter of the func
    is None or an empty string ''.
    If yes, return; else execute the function.

    ..Note: 1: self, 2: server, 3: param

    ..Note: The wraps decorator from functools is used to know the __name__
        of the decorated function.
        https://docs.python.org/3.5/library/functools.html#functools.wraps
    """
    @wraps(func)
    def modified_func(*args, **kwargs):
        if (args[2] is None) or (args[2] == ''):
            return
        return func(*args, **kwargs)
    return modified_func


class IRCAnalytics(SingleServerIRCBot):
    """
    Inherit from SingleServerIRCBot:
    Events must have the following prototype:
        def on_event(self, serv, ev):

    serv <irc.ServerConnection>: permits to communicate with the server
    ev <irc.Event>: informations about the event

    """

    def __init__(self, **kwargs):
        """Pass arguments to the constructor of the parent class"""
        # Tweak reconnection delay
        kwargs['reconnection_interval'] = 6
        SingleServerIRCBot.__init__(self, **kwargs)

        # Initialize database
        self._db_session = db.loading_sql()
        # Init regex for names in conversation
        self._expr_reg = re.compile('^(\w*): (.*)$')
        # Init regex for admin commands
#        self._admin_reg = re.compile('^(?P<command>3[\d]{1})( (?P<param>.*))?$')
        # Init regex for admin hosts
        self._admins_hosts = re.compile(cm.ADMINS_HOSTS_REG)
        # All admin functions
        self._admin_functions = {'31' : self.enable_whitelist,
                                 '32' : self.user_add,
                                 '33' : self.user_ban,
                                 '34' : self.user_remove_logs,
                                 '35' : self.user_remove_relationships,
                                 '36' : self.full_remove_asshole,
                                 '37' : self.db_backup,
                                }

    def get_current_date(self):
        """Return string with current date"""
        return datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

    def insert_in_database(self, pseudo, event):
        """Insert the event in database & commit it"""
        log = db.Log(pseudo, event)
        self._db_session.add(log)
        self._db_session.commit()

    def on_welcome(self, serv, ev):
        """Called when the bot is connected to the server.

        This method permits to join a specifica channel
        """
        LOGGER.info("Bot connected on server <" + ev.source + \
                    ">, nick : <" + ev.target + ">")
        # LOGGER.info(*ev.arguments)

        # Join channel
        serv.join(cm.CHANNEL)

    def on_whoisuser(self, serv, ev):
        """Print server response to the command "serv.whois([author])"""
        print(ev.arguments)
        LOGGER.info("Host of <" + ev.arguments[0] + \
                    "> is <" + ev.arguments[2] + ">")

    def on_ctcp(self, serv, ev):
        """Handle Client-To-Client (admin) commands.

        ..Note: /ctcp <botname>
        ..Note: Server receives in ev.arguments: ['32', 'user_test']
        """

        # Verification of admin rights
        if (ev.source.nick not in cm.ADMINS_LIST) or \
           (self._admins_hosts.match(ev.source) is None):
            return

        #Handle admin commands
        LOGGER.info("<" + ev.source.nick + "> is an admin")

        # If there is no/bad command or no parameter => an exception is raised
        # (because of access to a bad index in list ev.arguments)
        if len(ev.arguments) == 0:
            return

        try:
            # Find the correct function according to the command code
            # See the constructor for the mapping code <=> function
            func = self._admin_functions[ev.arguments[0]]
            # If the code is not unknown we call the function
            func(serv, ev.arguments[1])
        except:
            # Some func may accept None (a decorator will filter the call)
            func(serv, None)
            pass

    def on_pubmsg(self, serv, ev):
        """Called when a user posts a message"""
        author = ev.source.nick
        message = ev.arguments[0]

        # Filter the message if users whitelist is activated
        if cm.ENABLE_USERS_WHITELIST and not(author in cm.USERS_WHITELIST):
            LOGGER.debug("<" + author + "> is NOT in whitelist")
            return

        LOGGER.info(self.get_current_date() + " - <" + \
                     author + "> : " + message)

        # Detection of relationships
        try:
            # Raise an exception if message is not a relationship
            groups = self._expr_reg.match(message).groups()
            dest = groups[0]

            # Someone is speaking to the bot
            if dest == cm.BOT_NAME:
                self.handle_bot_dialog(serv, author, groups[1])
                #return # TODO: return ?

            # Return on micro message
            if len(groups[1]) <= 3:
                return

            # Verify if dest is a connected on the channel
            connected_users = list(self.channels[ev.target].users())
            LOGGER.debug("Connected users: " + str(connected_users))
            if dest not in connected_users:
                return

            # Add the detected relationship in database
            LOGGER.info("Relation between <" + author + \
                "> and <" + dest + ">")

            self._db_session.add(db.Edge(author, dest))
            self._db_session.commit()
        except AttributeError:
            # The message was not a relationship
            pass

        # Insert the message event in database
        self.insert_in_database(author, cm.IRC_MSG)

    def on_join(self, serv, ev):
        """Called when a user joins the channel"""
        author = ev.source.nick

        # Filter the bot activity
        if author == cm.BOT_NAME:
            # Get all users
            #users = [user for user in self.channels[ev.target].users()]

            LOGGER.info(self.get_current_date() + " - The bot <" + \
                     author + "> joined the channel <" + cm.CHANNEL + ">")
            #LOGGER.info("Users on the channel : " + str(",".join(users)))

            # Send message on channel
            serv.privmsg(ev.target, cm.BOT_MESSAGE)

            return

        LOGGER.info(self.get_current_date() + " - <" + \
                     author + "> joined the channel")

        # Insert in database
        self.insert_in_database(author, cm.IRC_JOIN)

    def on_part(self, serv, ev):
        """Called when a user leaves the channel"""
        author = ev.source.nick

        # Filter the bot activity (on exit ??)
        if author == cm.BOT_NAME:
            return
        LOGGER.info(self.get_current_date() + " - <" + \
                     author + "> left the channel")

        # Insert in database
        self.insert_in_database(author, cm.IRC_QUIT)

    def on_quit(self, serv, ev):
        """Called when a user leaves the server. Same as on_part event."""
        self.on_part(serv, ev)

    def on_kick(self, serv, ev):
        """Called when a user was kicked by another"""
        author = ev.source.nick

        # Filter the bot activity (on exit ??)
        if author == cm.BOT_NAME:
            # Save the session
            self._db_session.flush()
            self._db_session.commit()
            return

        # Print only victim's name
        LOGGER.debug(self.get_current_date() + " - <" + \
                     ev.arguments[0] + "> kicked by <" + author + ">")

        # Insert in database
        self.insert_in_database(ev.arguments[0], cm.IRC_KICK)


    def handle_bot_dialog(self, serv, author, message):
        """Someone is speaking to the bot.

        This function can handle admin commands and help questions.

        """
#        match_admin = self._admin_reg.match(message)

        if message == 'help' or message == '1':
            """Send help"""
            response = "1: help, 2: website, 3: admin ["
            response += " ".join("{}: {} <param/user>".format(k, v.__name__)
                                 for k, v in self._admin_functions.items()) + ']'

            serv.action(cm.CHANNEL, response)
            return

        elif message == 'website' or message == '2':
            """Send anchors of the website"""
            serv.action(cm.CHANNEL,
                " - Barplots: http://pro-domo.ddns.net/pirc_bot#")
            serv.action(cm.CHANNEL,
                " - Messages during weeks: http://pro-domo.ddns.net/pirc_bot#line_week")
            serv.action(cm.CHANNEL,
                " - Messages during days: http://pro-domo.ddns.net/pirc_bot#line_day")
            serv.action(cm.CHANNEL,
                " - Number of messages per day: http://pro-domo.ddns.net/pirc_bot#data_average")
            serv.action(cm.CHANNEL,
                " - Graph of relationships: http://pro-domo.ddns.net/pirc_bot#mynetwork")
            return

#        elif (match_admin is not None) and (author in cm.ADMINS_LIST):
#            """Handle admin commands"""
#            LOGGER.debug("<" + author + "> is an admin")
#
#            # Find the correct function according to the command code
#            # See the constructor for the mapping code <=> function
#            func = self._admin_functions[
#                    match_admin.groupdict().get('command', None)
#            ]
#            # If the code is not unknown we call the function
#            if func is not None:
#                func(serv,
#                     match_admin.groupdict().get('param', None))

    @param_not_none
    def enable_whitelist(self, serv, param):
        """Switch on/off the white list.

        ..Note: Command is <bot name>: 31 <1/0>
        """
        cm.ENABLE_USERS_WHITELIST = True if param == '1' else False
        serv.action(cm.CHANNEL, "Whitelist protection state is: <" + \
                                str(cm.ENABLE_USERS_WHITELIST) + ">")
        LOGGER.info("ADMIN: Whitelist state: <" + \
                    str(cm.ENABLE_USERS_WHITELIST) + \
                    "><" + str(cm.USERS_WHITELIST) + ">")

    @param_not_none
    def user_add(self, serv, param):
        """Add the given user to the whitelist, and refresh whitelist on disk.

        ..Note: Command is <bot name>: 32 <user>
        """
        cm.USERS_WHITELIST.add(param)
        cm.update_users()
        serv.action(cm.CHANNEL, "User <" + param + "> is now authorized.")
        LOGGER.info("ADMIN: User add: <" + param + ">")

    @param_not_none
    def user_ban(self, serv, param):
        """Remove the given user to the whitelist, and refresh whitelist on disk.

        ..Note: Command is <bot name>: 33 <user>
        """
        # If user is not in set; aka already banned
        try:
            cm.USERS_WHITELIST.remove(param)
            cm.update_users()
        except KeyError:
            pass
        serv.action(cm.CHANNEL, "User <" + param + "> is banned.")
        LOGGER.info("ADMIN: User remove: <" + param + ">")

    @param_not_none
    def user_remove_logs(self, serv, param):
        """Remove the logs for the given user.

        ..Note: Command is <bot name>: 34 <user>
        """
        number = db.Log.delete_user(self._db_session, param)
        serv.action(cm.CHANNEL,
                    str(number) + " deleted logs for <" + param + \
                    ">. Have a nice day.")
        LOGGER.info("ADMIN: Remove logs: <" + param + ">")

    @param_not_none
    def user_remove_relationships(self, serv, param):
        """Remove the relationships for the given user.

        ..Note: Command is <bot name>: 35 <user>
        """
        number = db.Edge.delete_user(self._db_session, param)
        serv.action(cm.CHANNEL,
                    str(number) + " deleted edges for <" + param + \
                    ">  Have a nice day.")
        LOGGER.info("ADMIN: Remove relations: <" + param + ">")

    @param_not_none
    def full_remove_asshole(self, serv, param):
        """Remove logs & relationships for the given user"""
        self.user_remove_logs(serv, param)
        self.user_remove_relationships(serv, param)

    def db_backup(self, serv, param):
        """Do a backup of the sqlite database.

        ..Note: The name is chosen from current date.
        ..Note: Command is <bot name>: 36 <user>
        """
        copyfile(cm.DIR_DATA + 'bdd.sqlite',
                 cm.DIR_DATA + 'bdd.sqlite_' + self.get_current_date())
        serv.action(cm.CHANNEL, "Database is backed up.")
        LOGGER.info("ADMIN: DB backup done")


def main():
    """Start the bot"""

    bot_instance = IRCAnalytics(server_list=[(cm.SERVER_URL, cm.SERVER_PORT)],
                                nickname=cm.BOT_NAME,
                                realname=cm.BOT_REALNAME)

    # Start the bot
    bot_instance.start()

if __name__ == "__main__":

    main()
