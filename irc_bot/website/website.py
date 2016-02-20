# -*- coding: utf-8 -*-
"""
This modules handles flask app and pass the data taken from database
to the main webpage.

- Charts.js documentation:
http://www.chartjs.org/docs
- Highcharts.js documentation:
http://api.highcharts.com/highcharts
- Vis.js documentation:
http://visjs.org/docs/network/
"""

# Standard imports
from flask import Flask, render_template

# Custom imports
from irc_bot import commons as cm
from irc_bot import database as db

LOGGER = cm.logger()

#static_url_path :
#can be used to specify a different path for the static files on the web.
#Defaults to the name of the static_folder folder.
#static_folder :
#the folder with static files that should be served at static_url_path.
#Defaults to the 'static' folder in the root path of the application.

app = Flask(__name__,
            static_folder='../../' + cm.DIR_W_STATIC,
            template_folder='../../' + cm.DIR_W_TEMPLATES)
# Initialize SQLAlchemy session (flask auto-removes the session later
session = db.loading_sql()

# Data caching
if not cm.ENABLE_REALTIME:
    from irc_bot.data_caching import DataCaching

    # Pass the callable for database interrogation (have a look to database.py)
    thread = DataCaching(session, db.forge_data)
    thread.start()


@app.route(cm.NGINX_PREFIX)
def index():
    """Main page with graphs.

    This func gets all data to be displayed on the html template

    Examples of data:
    data_bar_day = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
    data_bar_week = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
    data_line_week = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 74, 0, 0, 0, 0, 0, 0, 0]]

    """

    # Data caching
    if not cm.ENABLE_REALTIME:
        return render_template('index.html', **thread.data)

    # With data caching: realtime
    return render_template('index.html', **db.forge_data(session))


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close the SQLAlchemy session => MAJOR IMPROVMENT !!!
    http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    PAY ATTENTION HERE:
    http://stackoverflow.com/questions/21078696/why-is-my-scoped-session-raising-an-attributeerror-session-object-has-no-attr
    """
    LOGGER.debug("SQLA : Closing session...")
    session.remove()


def main():

    app.run()

if __name__ == "__main__":

    main()
