#!/bin/bash

ps axu | grep gua_app.py | grep -v grep |  awk '{print $2; }' | xargs -i kill -9 {}

nohup .venv/bin/python gua_app.py > app.log 2>&1 &