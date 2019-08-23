CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
SERVICE_NAME="pircbot.service"
#LOGLEVEL=--loglevel=debug
#LOGLEVEL=--loglevel=info
COMMAND=$(PYTHON) $(LOGLEVEL)
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

irc_start:
	$(COMMAND) irc_bot_start

dev_flask_start:
	# 1 worker, bind localhost:4000
	# Binding to nginx proxy
	gunicorn --log-level=debug --timeout 10 --workers 8 --threads 4 --bind 127.0.0.1:4000 irc_bot.irc_bot:app

systd_prod_flask_start:
	sudo systemctl start $(SERVICE_NAME)

systd_prod_flask_stop:
	sudo systemctl stop $(SERVICE_NAME)

systd_prod_flask_restart:
	sudo systemctl restart $(SERVICE_NAME)

install:
	sudo cp $(SERVICE_NAME) /etc/systemd/system/
	sudo sed -i -e 's#/project/directory#$(ROOT_DIR)#g' /etc/systemd/system/$(SERVICE_NAME)
	sudo chmod a+x /etc/systemd/system/$(SERVICE_NAME)
	sudo systemctl daemon-reload
	sudo mkdir /var/log/pircbot

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help