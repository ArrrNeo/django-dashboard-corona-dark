#!/bin/bash

patch -N env/lib/python3.7/site-packages/pyrh/robinhood.py < pyrh_login.patch
