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

@app.route('/')
def index():
    with db.SQLA_Wrapper() as session:
#
        day_messages = db.Log.get_day_messages(session)
        week_messages = db.Log.get_week_messages(session)

        data_bar_day = db.Log.get_top_posters(day_messages)
        data_bar_week = db.Log.get_top_posters(week_messages)
        data_line_week = db.Log.get_messages_per_hour(week_messages)

#        bar_data = db.Log.get_top_posters(r)
    #bar_data = {'Plopp': 7, 'test': 2, 'DrIDK': 28, 'anon_bt': 2, 'Natir': 36, 'neolem': 1, 'Lou__': 1}
#    labels = ['Natir', 'DrIDK', 'Plopp', 'test', 'anon_bt', 'Lou__', 'neolem']
#    values = [36, 28, 7, 2, 2, 1, 1]

#    data_bar_day = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
#    data_bar_week = [['Natir', 'DrIDK', 'Plopp', 'anon_bt', 'test', 'neolem', 'Lou__'], [36, 28, 7, 2, 2, 1, 1]]
#    data_line_week = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 74, 0, 0, 0, 0, 0, 0, 0]]

    return render_template('index.html',
                           nginx_prefix=cm.NGINX_PREFIX,
                           data_bar_day=data_bar_day,
                           data_bar_week=data_bar_week,
                           data_line_week=data_line_week)


def main():
    print("je suis ici")
    app.run(debug=True)






if __name__ == "__main__":

    main()
