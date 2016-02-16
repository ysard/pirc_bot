CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
SOCKET_FILE="/tmp/irc_bot.sock"
#LOGLEVEL=--loglevel=debug
#LOGLEVEL=--loglevel=info

COMMAND=$(PYTHON) $(LOGLEVEL)

all:
	$(COMMAND)
	
irc_start:
	$(COMMAND) irc_bot_start

#dev_flask_start:
#	$(COMMAND) start_flask_dev

dev_flask_start:
	# 1 worker, bind localhost:4000
	# Binding to nginx proxy
	gunicorn --log-level=debug -w 1 -b 127.0.0.1:4000 irc_bot.irc_bot:app

prod_flask_start:
	if [ -e $(SOCKET_FILE) ]; then sudo rm $(SOCKET_FILE); fi
	# Binding to nginx proxy via unix socket
	gunicorn --timeout 120 --log-level=debug --workers 1 --bind unix:/tmp/irc_bot.sock -m 007 irc_bot.irc_bot:app
	#sudo chown www-data:www-data /tmp/irc_bot.sock

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help