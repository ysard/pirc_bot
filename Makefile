CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
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
	# 2 workers, bind localhost:4000
	# Binding to nginx proxy
	gunicorn --user=www-data --group=www-data --log-level=debug -w 1 -b 127.0.0.1:4000 irc_bot.irc_bot:app

prod_flask_start:
	sudo rm /tmp/irc_bot.sock
	#sudo chmod a+wx /tmp/irc_bot.sock
	# Binding to nginx proxy via unix socket
	gunicorn --user=www-data --group=www-data --log-level=debug --workers 1 --bind unix:/tmp/irc_bot.sock -m 007 irc_bot.irc_bot:app

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help