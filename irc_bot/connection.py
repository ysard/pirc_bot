# -*- coding: utf-8 -*-
"""
This modules handles the IRC connection.
The class IRCAnalytics is the heart of this program.
It saves all events in database.
"""

# Standard imports
import datetime
from irc.bot import *
# Tuto:
# https://openclassrooms.com/courses/programmer-un-bot-irc-simplement-avec-ircbot

# Custom imports
from irc_bot import commons as cm
from irc_bot import database as db

LOGGER = cm.logger()

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

    def get_current_date(self):
        """Return string with current date"""
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

    def on_pubmsg(self, serv, ev):
        """Called when a user posts a message"""
        author = ev.source.nick
        LOGGER.debug(self.get_current_date() + " - " + \
                     author + " posted : " + str(*ev.arguments))

        # Insert in database
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
            serv.privmsg(self, ev.target, cm.BOT_MESSAGE)

            return
        LOGGER.debug(self.get_current_date() + " - <" + \
                     author + "> joined the channel")

        # Insert in database
        self.insert_in_database(author, cm.IRC_JOIN)

    def on_part(self, serv, ev):
        """Called when a user leaves the channel"""
        author = ev.source.nick

        # Filter the bot activity (on exit ??)
        if author == cm.BOT_NAME:
            return
        LOGGER.debug(self.get_current_date() + " - <" + \
                     author + "> left the channel")

        # Insert in database
        self.insert_in_database(author, cm.IRC_QUIT)

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

def main():
    """Start the bot"""

    bot_instance = IRCAnalytics(server_list=[(cm.SERVER_URL, cm.SERVER_PORT)],
                                nickname=cm.BOT_NAME,
                                realname=cm.BOT_REALNAME)

    # Start the bot
    bot_instance.start()

if __name__ == "__main__":

    main()
