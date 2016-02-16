# -*- coding: utf-8 -*-
"""
This modules handles flask app and pass the data taken from database
to the main webpage.

Charts.js documentation:
http://www.chartjs.org/docs

"""

# Standard imports
from flask import Flask, render_template
import sys
sys.path.append('../')

# Custom imports
from irc_bot import commons as cm
from irc_bot import database as db

#static_url_path :
#can be used to specify a different path for the static files on the web.
#Defaults to the name of the static_folder folder.
#static_folder :
#the folder with static files that should be served at static_url_path.
#Defaults to the 'static' folder in the root path of the application.

app = Flask(__name__)
# Initialize SQLAlchemy session (flask auto-removes the sssion later
session = db.loading_sql()

@app.route(cm.NGINX_PREFIX)
def index():
    """Main page with graphs.

    This func gets all data to be displayed on the html template
    """
    prev_day_msgs = db.Log.get_day_messages(session, previous=True)
    prev_week_msgs = db.Log.get_week_messages(session, previous=True)
    day_msgs = db.Log.get_day_messages(session)
    week_msgs = db.Log.get_week_messages(session)


#    data_bar_day = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
#    data_bar_week = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
#    data_line_week = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 74, 0, 0, 0, 0, 0, 0, 0]]

    return render_template('index.html',
                           nginx_prefix=cm.STATIC_PREFIX,
                           data_bar_day=db.Log.get_top_posters(day_msgs),
                           data_bar_prev_day=db.Log.get_top_posters(prev_day_msgs),
                           data_bar_week=db.Log.get_top_posters(week_msgs),
                           data_line_prev_week=db.Log.get_messages_per_hour(prev_week_msgs),
                           data_line_week=db.Log.get_messages_per_hour(week_msgs),
                           data_line_day=db.Log.get_messages_per_hour(day_msgs))


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close the SQLAlchemy session => MAJOR IMPROVMENT !!!
    http://flask.pocoo.org/docs/0.10/patterns/sqlalchemy/
    """
    session.remove()


def main():
    app.run(debug=True)


if __name__ == "__main__":

    main()
