# -*- coding: utf-8 -*-
"""
This module handles the SQLite database with SQLAlchemy.
The class Log is used to insert events in db.

"""
# Custom imports
from irc_bot import commons as cm

# Standard imports
import datetime
# https://docs.python.org/3.5/library/datetime.html
import os
from collections import Counter
from operator import itemgetter
import itertools as it
# Don't import networkx if flag is False
if cm.USE_NETWORKX:
    import networkx as nx

# SQL Alchemy
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

LOGGER = cm.logger()

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
        self._session = loading_sql(**self._kwargs)()
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
    db_file = cm.DIR_DATA + 'bdd.sqlite'
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

    # PAY ATTENTION HERE:
    # http://stackoverflow.com/questions/21078696/why-is-my-scoped-session-raising-an-attributeerror-session-object-has-no-attr
    return scoped_session(sessionmaker(bind=engine, autoflush=True))
#    Session =
#    return Session()

################################################################################
class Item():
    """Some usefull methods to handle the objects in database"""

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


class Edge(Base, Item):
    """ """

    __tablename__ = 'edge'
    id = Column(Integer, primary_key=True)

    # use utcnow to avoid timezones
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    pseudo1   = Column(String(20), nullable=False)
    pseudo2   = Column(String(20), nullable=False)

    # Unicity constraint
    # Note for MySQL, unicity & index is the same thing
    Index('index_1', 'pesudo1', 'pseudo2', unique=True)

    def __init__(self, pseudo1, pseudo2):
        """Constructor takes pseudo of the poster & the event type

        ..note: timestamp is setup automatically

        :param arg1: Poster's pseudo
        :param arg2: Event's type
        :type arg1: <str>
        :type arg2: <str>

        """
        # Lexicographic sort
        self.pseudo1, self.pseudo2 = \
            (pseudo1, pseudo2) if (pseudo1 < pseudo2) else (pseudo2, pseudo1)

    def __repr__(self):
        return "id:{}, timestamp:{}, pseudo1:{}, pseudo2:{}".format(
            self.id,
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.pseudo1,
            self.pseudo2)


    @staticmethod
    def get_nodes(edges):
        """Return a Counter of all nodes (aka user's pseudonyms).

        Values are used to ressize nodes on graph.

        :param: List of Edges.
        :type: <list <Edge>>
        :return: Counter of pseudonyms.
        :rtype: <Counter <str> : <int>>
        """

        g = ((edge.pseudo1, edge.pseudo2) for edge in edges)
        g = it.chain(*g)

        return Counter(node for node in g)

    @staticmethod
    def get_formatted_nodes(edges):
        """Used to format nodes in DOT format.

        ..Note: Protection of node names with quotes "" => avoid curious
            things with composite names

        :param: List of Edges.
        :type: <list <Edge>>
        :return: DOT nodes.
        :rtype: <str>
        """

        # chaman_gitan [value=51, title="3 message(s)"];
        return ['"{}" [value={}, title="{} message(s)"];'.format(pseudo,
                                                               value,
                                                               value)
            for pseudo, value in Edge.get_nodes(edges).items()]

    @staticmethod
    def get_formatted_edges(edges):
        """Used to format edges in DOT format.

        ..Note: Protection of node names with quotes "" => avoid curious
            things with composite names

        :param: List of Edges.
        :type: <list <Edge>>
        :return: DOT edges.
        :rtype: <str>
        """

        # neolem -- gentilbot397  [title="7 message(s)", value=7];
        all_edges = Counter((edge.pseudo1, edge.pseudo2) for edge in edges)
        return ['"{}" -- "{}" [value={}, title="{} message(s)"];'.format(pseudo1,
                                                                     pseudo2,
                                                                     all_edges[(pseudo1, pseudo2)],
                                                                     all_edges[(pseudo1, pseudo2)])
            for pseudo1, pseudo2 in all_edges.keys()]

    @staticmethod
    def get_graph(edges):
        """Return a relation graph in dot format according to the given Edges.

        ..Note: There is an autodetection of the use of NetworkX lib

        ..Note: The returned string could be displayed in Jinja,
            with 'text | safe' filter.

        ..Note: Colormap & degrees:
        https://networkx.github.io/documentation/latest/examples/drawing/node_colormap.html
        http://matplotlib.org/users/colormaps.html

        :param: List of Edge.
        :type: <list <Edge>>
        :return: dot string ready to be used.
        :rtype: <str>
        """

        # Without Networkx
        if cm.USE_NETWORKX is not True:
            return 'graph "" { ' + \
            ' '.join(Edge.get_formatted_nodes(edges)) + \
            ' '.join(Edge.get_formatted_edges(edges)) + \
            '}'

        # With Networkx
        # Counter of pseudos
        all_nodes = Edge.get_nodes(edges)
        # Counter of edges
        all_edges = Counter((edge.pseudo1, edge.pseudo2) for edge in edges)

        # Add nodes automatically by adding weighted edges directly
        # Problem : this creates weight attribute but Vis uses value attribute..
        G = nx.Graph()
        G.add_weighted_edges_from([(e[0], e[1], all_edges[e]) for e in all_edges])

        # Set edges titles (according to weights)
        # PS: labels are always displayed on graph,
        # whereas titles are displayed on mouse hover.
        # PS2: to be resized, elements must have values value instead of weight.
        [nx.set_edge_attributes(G, 'title',
                                {edge : str(weight) + " message(s)"})
            for edge, weight in nx.get_edge_attributes(G, 'weight').items()]
        [nx.set_edge_attributes(G, 'value',
                                {edge : weight})
            for edge, weight in nx.get_edge_attributes(G, 'weight').items()]
        # Add weights on nodes
        [nx.set_node_attributes(G, 'value',
                                {node : all_nodes[node]})
            for node in G.nodes_iter()]
        [nx.set_node_attributes(G, 'title',
                                {node : str(all_nodes[node]) + " message(s)"})
            for node in G.nodes_iter()]

#        print(nx.get_edge_attributes(G, 'weight'))
#        print(nx.get_edge_attributes(G, 'label'))
#        print(nx.get_node_attributes(G, 'weight'))

        # Write into file => ULGYYY
        # https://networkx.github.io/documentation/latest/_modules/networkx/drawing/nx_pydot.html
        # Save dot file
#        nx.drawing.nx_pydot.write_dot(G, "test.dot")
        return nx.drawing.nx_pydot.to_pydot(G).to_string().replace('\n', ' ')


class Log(Base, Item):
    """Log class definition"""

    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)

    # use utcnow to avoid timezones
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    pseudo    = Column(String(50), nullable=False)
    event     = Column(Integer, nullable=False)

    # Unicity constraint
    # Note for MySQL, unicity & index is the same thing
    Index('index_1', 'event', 'pseudo', unique=True)

    def __init__(self, pseudo, event):
        """Constructor takes pseudo of the poster & the event type

        ..note: timestamp is setup automatically

        :param arg1: Poster's pseudo
        :param arg2: Event's type
        :type arg1: <str>
        :type arg2: <str>

        """
        self.pseudo = pseudo
        self.event = event

    def __repr__(self):
        return "id:{}, timestamp:{}, pseudo:{}, event:{}".format(
            self.id,
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.pseudo,
            self.event)


    @staticmethod
    def get_day_messages(session, previous=False):
        """Get all messages in the current day.

        :param arg1: SQLAlchemy session.
        :param arg2: A boolean to retrieve messages
            from the current or previous day.
        :type arg1: <SQL session object>
        :type arg2: <boolean>
        :return: Lists of Log objects.
        :rtype: <list <Log>>

        """
        # Beginning of today
        d1 = datetime.datetime.now().replace(hour=0, minute=0, second=0)

        # Is starting day the current or previous day ?
        if previous == True:
            d1 = d1.replace(day=d1.day - 1)

#        d1 = datetime.datetime.today()

        # En of today
        d2 = d1.replace(day=d1.day + 1)

        query = session.query(Log).filter(Log.timestamp >= d1,
                                          Log.timestamp < d2,
                                          Log.event == cm.IRC_MSG)
        results = [entity for entity in query]

        LOGGER.debug("Messages per day : " + str(len(results)))
        return results


    @staticmethod
    def get_week_messages(session, previous=False):
        """Get all messages in the current week.

        :param arg1: SQLAlchemy session.
        :type arg1: <SQL session object>
        :return: Lists of Log objects.
        :rtype: <list <Log>>

        """
        # Today
        d1 = datetime.datetime.today().replace(hour=0, minute=0, second=0)

        # Is starting day the current or the day of the last week ?
        if previous == True:
            d1 = d1.replace(day=d1.day - 7) # sub 7 days

        # Current week
        week_start = d1 - datetime.timedelta(days=d1.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        query = session.query(Log).filter(Log.timestamp >= week_start,
                                          Log.timestamp < week_end,
                                          Log.event == cm.IRC_MSG)
        results = [entity for entity in query]

        LOGGER.debug("Messages per week : " + str(len(results)))
        return results


    @staticmethod
    def get_messages_per_hour(logs):
        """Extracts number of messages per hour of the day from the log list.

        :param: List of logs
        :type: <list <Log>>
        :return: Lists of hours & number of messages
        :rtype: [[labels], [values]]

        """
        unzip = lambda liste: [tuple(li) for li in zip(*liste)]

        # Initialize all hours of a day
        all_messages_by_hours = Counter({hour : 0 for hour in range(00,24)})
        # Update with data : Count messages by hours
        all_messages_by_hours.update(log.timestamp.hour for log in logs)
        # Sort on day hours & return 2 lists [labels][values]
        all_messages_by_hours = unzip(sorted(all_messages_by_hours.items(),
                                             key=itemgetter(0)))

        LOGGER.debug("Messages per hour : " + str(all_messages_by_hours))
        return all_messages_by_hours


    @staticmethod
    def get_top_posters(logs):
        """Extracts pseudo & number of messages from the log list.

        ..Note: 15 most common

        :param: List of logs
        :type: <list <Log>>
        :return: Lists of labels & number of messages
        :rtype: [[labels], [values]]

        """
        unzip = lambda liste: [tuple(li) for li in zip(*liste)]

        # Sort the Counter on the n most common elements and their counts
        all_posters = unzip(Counter(log.pseudo for log in logs).most_common(15))
        return all_posters


    @staticmethod
    def get_average_msgs_per_day(logs):
        """Return a list of average messages per day
        since the beginning of the logging

        :param: List of logs
        :type: <list <Log>>
        :return: List of values.
        :rtype: <list>

        """

        # Get number of unique days in db (weekday, day, month, year)
        unique_days = {(log.timestamp.weekday(),
                        log.timestamp.day,
                        log.timestamp.month,
                        log.timestamp.year) for log in logs}
        # Count them
        nb_unique_days = Counter(day for day, _, _, _ in unique_days)
        LOGGER.debug("Number of unique days:" + str(nb_unique_days))

        # Initialize all days of a week
        all_messages_by_days = Counter({_ : 0 for _ in range(0,7)})
        # Update with data : Count messages by days (0 to 6)
        all_messages_by_days.update(log.timestamp.weekday() for log in logs)

        # Extract an ordered list : each day and average messages
        all_messages_by_days = \
            [all_messages_by_days[day]/nb_unique_days.get(day, 1) for day in range(0,7)]

        return all_messages_by_days


def forge_data(session):
    """This function forges data for the website.

    It's used by Flask or DataCaching object to generate data.

    :param: SQLAlchemy session.
    :type: <SQL session object>
    :return: Dictionary of all parameters used in the template.
    :rtype: <dict>
    """

    prev_day_msgs  = Log.get_day_messages(session, previous=True)
    prev_week_msgs = Log.get_week_messages(session, previous=True)
    day_msgs       = Log.get_day_messages(session)
    week_msgs      = Log.get_week_messages(session)
    edges          = Edge.get_all(session)

    return {
        'nginx_prefix' : cm.STATIC_PREFIX,
        'data_bar_day' : Log.get_top_posters(
            day_msgs),
        'data_bar_prev_day' : Log.get_top_posters(
            prev_day_msgs),
        'data_bar_week' : Log.get_top_posters(
            week_msgs),
        'data_line_prev_week' : Log.get_messages_per_hour(
            prev_week_msgs),
        'data_line_week' : Log.get_messages_per_hour(
            week_msgs),
        'data_line_prev_day' : Log.get_messages_per_hour(
            prev_day_msgs),
        'data_line_day' : Log.get_messages_per_hour(
            day_msgs),
        'data_average' : Log.get_average_msgs_per_day(
            Log.get_all(session)),
        'data_graph' : Edge.get_graph(edges)
    }


if __name__ == "__main__":

    with SQLA_Wrapper() as session:

#        session.add(Edge("a", "b"))
#        session.add(Edge("c", "d"))
#        session.add(Edge("e", "f"))
#        session.add(Edge("a", "c"))
#        session.add(Edge("d", "e"))
#        session.add(Edge("a", "f"))
#        session.commit()
#        exit()
        print(Edge.get_nodes(Edge.get_all(session)))
        print(Edge.get_formatted_nodes(Edge.get_all(session)))
        print(Edge.get_formatted_edges(Edge.get_all(session)))
        print(Edge.get_graph(Edge.get_all(session)))
        exit()


#        current_log = Log("test", 4)
#
#        # Add object to SQLite DB
#        session.add(current_log)
#        session.commit()

        print(Log.get_week_messages(session, previous=True))
        Log.get_day_messages(session, previous=True)
        r = Log.get_week_messages(session)
        print(Log.get_messages_per_hour(r))

        print(Log.get_average_msgs_per_day(Log.get_all(session)))
        exit()
        r = Log.get_top_posters(r)
        print(r)


#        print("Nb logs:", Log.get_number(session))
#        print("All logs:", session.query(Log).all())



