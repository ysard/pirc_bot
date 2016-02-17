CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
SOCKET_FILE="/tmp/irc_bot.sock"
SERVICE_NAME="pircbot.service"
#LOGLEVEL=--loglevel=debug
#LOGLEVEL=--loglevel=info
COMMAND=$(PYTHON) $(LOGLEVEL)
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

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
	# DON'T FORGET TO EXECUTE THIS COMMAND: sudo chown www-data:www-data /tmp/irc_bot.sock
	# Binding to nginx proxy via unix socket
	gunicorn --timeout 10 --workers 1 --bind unix:/tmp/irc_bot.sock -m 007 irc_bot.irc_bot:app
	#sudo chown www-data:www-data /tmp/irc_bot.sock

systd_prod_flask_start:
	sudo systemctl start $(SERVICE_NAME)

systd_prod_flask_stop:
	sudo systemctl stop $(SERVICE_NAME)

systd_prod_flask_restart:
	sudo systemctl restart $(SERVICE_NAME)

install:
	sudo cp $(SERVICE_NAME) /etc/systemd/system/
	sudo sed -i -e 's#/project/directory#$(ROOT_DIR)#g' /etc/systemd/system/pircbot.service
	sudo chmod a+x /etc/systemd/system/$(SERVICE_NAME)
	sudo systemctl daemon-reload

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help