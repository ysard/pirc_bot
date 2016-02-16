CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
#LOGLEVEL=--loglevel=debug
#LOGLEVEL=--loglevel=info

COMMAND=$(PYTHON) $(LOGLEVEL)

all:
	$(COMMAND)
	
irc_start:
	$(COMMAND) start

dev_flask_start:
	$(COMMAND) start_flask

prod_flask_start:
	# 2 workers, bind localhost:4000
	gunicorn -w 2 -b 127.0.0.1:4000 irc_bot.irc_bot:app

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help