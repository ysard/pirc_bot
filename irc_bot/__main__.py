# -*- coding: utf-8 -*-
"""
Created on Feb 2016

..sectionauthor:: Pierre.VIGNET <pierre.vignet@inria.fr>
"""

import argparse
import os

from irc_bot import commons
from irc_bot.info import PACKAGE_VERSION  # , PACKAGE_NAME

LOGGER = commons.logger()


def irc_bot_start(args):
    """Load the bot"""
    from irc_bot import connection
    param = args_to_param(args)
    connection.main(**param)

def start_flask_dev(args):
    """Load flask app in dev environment"""
    from irc_bot import website
    param = args_to_param(args)
    website.main(**param)

def args_to_param(args):
    """Return argparse namespace as a dict {variable name: value}"""
    return {k: v for k, v in vars(args).items() if k != 'func'}


class readable_dir(argparse.Action):
    """
    http://stackoverflow.com/questions/11415570/directory-path-types-with-argparse
    """

    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values

        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                "readable_dir:{0} is not a valid path".format(prospective_dir))

        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError(
                "readable_dir:{0} is not a readable dir".format(prospective_dir))



if __name__ == '__main__':
    # parser configuration
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v, --version', action='version',
                        version='%(prog)s ' + PACKAGE_VERSION, )
    subparsers = parser.add_subparsers(title='subcommands')

    # subparser: load ircbot
    load_ircbot = subparsers.add_parser('irc_bot_start',
                                        help=irc_bot_start.__doc__, )
    load_ircbot.set_defaults(func=irc_bot_start)

    # subparser: flask website
    load_flask = subparsers.add_parser('start_flask_dev',
                                        help=start_flask_dev.__doc__, )
    load_flask.set_defaults(func=start_flask_dev)


    # get program args and launch associated command
    args = parser.parse_args()
    args.func(args)
