CMD_PYTHON=python3
PYTHON=$(CMD_PYTHON) -m irc_bot
#LOGLEVEL=--loglevel=debug
#LOGLEVEL=--loglevel=info

COMMAND=$(PYTHON) $(LOGLEVEL)

all:
	$(COMMAND)
	
start:
	$(COMMAND) start

version:
	$(COMMAND) --version
help:
	$(COMMAND) --help