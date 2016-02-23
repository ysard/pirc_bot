
# Description

The goal of this project is to provide an analysis bot of messages, and relationships between the authors
of these messages on an IRC channel.
Numerous charts and graphs are produced and are made available from a web interface.
The entire project is made on a full python stack.
You will find [Flask](http://flask.pocoo.org/) as a Python microframework based on Jinja2.
The project is powered by [Gunicorn](http://docs.gunicorn.org/en/stable/index.html) project as a Python
WSGI HTTP Server for Unix systems; and by [Nginx](http://nginx.org/) as a proxy with powerful caching features.

![Website screenshot](./pirc_bot1.png)
![Website screenshot](./pirc_bot2.png)

# Installation

## Core

You have to install all given Python requirements (in a virtualenv for exemple):

    pip3.5 install -r requirements.txt

*Note:* Please note that Python 3.5+ is **necessary**; otherwise the correct behavior is not guaranteed.
*Note:* networkx & pydotplus are optional (see below the configuration paragraph).

## Nginx

Here you will find an example of Nginx configuration host which is largely based on
the documentation of [Gunicorn](http://docs.gunicorn.org/en/stable/deploy.html).

You can also take a look at [Nginx documentation](http://nginx.org/en/docs/http/load_balancing.html)
for the load-balancing configuration.

    :::nginx
    server {
        location /pirc_bot {

            # checks for static file, if not found proxy to app
            try_files $uri @proxy_to_app;
        }

        location /pirc_bot/static/ {
            autoindex on;
            alias   /path/to/project/irc_bot/website_files/static/;
        }

        # Flask proxy config for irc_bot interface
        location @proxy_to_app {

            # enable this if and only if you use HTTPS
            # proxy_set_header X-Forwarded-Proto https;
            proxy_set_header   Host             $http_host;

            # proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto $scheme;

            # we don't want nginx trying to do something clever with
            # redirects, we set the Host: header above already.
            proxy_redirect     off;

            # Filter static files (may be redondant with location '/pirc_bot/static/'
            if (!-f $request_filename) {
                proxy_pass http://flask_server;
                break;
            }
        }
    }
    upstream flask_server {
        # swap the commented lines below to switch between socket and port
        # You can enable load balancing by specifying multiple servers and adding weights on them.
        server unix:/run/pircbot.sock fail_timeout=0;
        #server 127.0.0.1:4000 weight=1000 fail_timeout=0;
    }

*Note:* In upstream section, Unix sockets can be used as good as basic http exchange between Nginx & Gunicorn.
However the Unix sockets are are by far advised if you run Gunicorn & Nginx on the same host.

## As a service

A Systemd script is provided in order to facilitate the configuration of the web interface as a service.

    :::ini
    [Unit]
    Description=pirc bot
    #Requires=network.socket
    After=network.target

    [Service]
    PIDFile=/run/pircbot.pid
    Group=www-data
    WorkingDirectory=/project/directory
    Environment="PATH=/usr/local/bin"
    ExecStart=/usr/local/bin/gunicorn --timeout 13 --workers 1 --pid /run/pircbot.pid --bind unix:/run/pircbot.sock -m 007 irc_bot.irc_bot:app
    ExecReload=/bin/kill -s HUP $MAINPID
    ExecStop=/bin/kill -s TERM $MAINPID

    [Install]
    WantedBy=multi-user.target

Change `Environment` key and change the path of gunicorn if you plan to work in a virtualenv.
Apart from this, the installation of the service (in `/etc/systemd/system/pircbot.service`) can be made with the following command:

    make install


# Configuration

All the settings are located in the `irc_bot\commons.py` file.

## NetworkX use

    USE_NETWORKX     = False

Basicaly you can choose to activate the use of [NetworkX python module](http://networkx.github.io/documentation/networkx-1.9.1/overview.html)
for the relationships graph generation in DOT file format.
Otherwise the DOT string is made on the fly by the program.
Currently there is no advantage to use NetworkX rather than the basic code.
Keep in mind that some CPU limited configurations such as raspberry pi B + will be very difficult to import this library.

## IRC parameters

    SERVER_URL       = "irc.freenode.net"
    SERVER_PORT      = 6667
    BOT_NAME         = "pirc_bot"
    # whois info
    BOT_REALNAME     = "pirc bot " + info.PACKAGE_VERSION + \
        " <http://my_website/pirc_bot>"
    # Message sended on connection
    BOT_MESSAGE      = "#My Bot Analytics " + info.PACKAGE_VERSION + \
        " - http://my_website/pirc_bot"
    # IRC channel
    CHANNEL          = "#my_channel"

## Administration

You can specify a whitelist file `pseudos_whitelist.txt` with one "good" pseudonynm on each line.

You can also use a regex string for the IP address of your admin account.
The admin accounts will be in a specific file : `admins.txt`.
(The bot will authorize your admin commands only on IP & Pseudonym matching)

These files will be loaded along with the bot.

    ENABLE_USERS_WHITELIST = False
    USERS_WHITELIST  = DIR_DATA + "pseudos_whitelist.txt"
    ADMINS_LIST      = DIR_DATA + "admins.txt"
    ADMINS_HOSTS_REG = '.*(192.168.1.200).*'


## Nginx prefix

On dev environment specify these settings:

* "/" string for NGINX_PREFIX
* "" string for STATIC_PREFIX

On prod environment don't forget to synchronize these settings with
Nginx config.

    # Prod
    #NGINX_PREFIX     = "/pirc_bot"
    #STATIC_PREFIX    = NGINX_PREFIX
    # Dev
    NGINX_PREFIX     = "/"
    STATIC_PREFIX    = ""

## Data caching

By disable real-time generation of graphs and data, each query on the website
will question the database & the python code.
In some plateforms this could be very time consuming.
Thus by default, a thread will be used to pre-generate data,
according to the following delay (in seconds).

    ENABLE_REALTIME  = True
    DELAY            = 40

# Utilisation

## Web server

You can load the server in development environment with:

    make dev_flask_start

Gunicorn will be loaded on http://127.0.0.1:4000

If pircbot was installed as a service you can do:

    make systd_prod_flask_start
    make systd_prod_flask_stop

or obviously:

    sudo systemctl start pircbot.service
    sudo systemctl stop pircbot.service

*Note:* You can customize the number of Gunicorn workers / threads by workers in pircbot.service and in the Makefile.

## IRC bot

You can load the bot with the following command:

    make irc_start

### IRC public commands

Obtain a list of all commands:

    pircbt: 1
    pircbt: help

Obtain a list of all anchors in website:

    pircbt: 2
    pircbt: website

### IRC admin commands

Admin commands use [Client-to-client (ctcp) protocol](https://en.wikipedia.org/wiki/Client-to-client_protocol).
The aim is to send direct inputs to the bot.

Enable/disable whitelist on the fly:

    /ctcp pirc_bt 31 <1/0>

Add user on whitelist & save him in whitelist file:

    /ctcp pirc_bt 32 <user>

Remove a user from the whitelist & synchronize the whitelist file:

    /ctcp pirc_bt 33 <user>

Remove logs of a user:

    /ctcp pirc_bt 34 <user>

Remove graph relationships of a user:

    /ctcp pirc_bt 35 <user>

Remove logs & relationships of a user:

    /ctcp pirc_bt 36 <user>

Do a time stamped database backup:

    /ctcp pirc_bt 37