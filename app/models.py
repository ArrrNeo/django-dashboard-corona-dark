# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class robinhood_db_timestamps(models.Model):
    instrument_type        = models.CharField(max_length=5)
    timestamp              = models.DateTimeField(null=True)

class robinhood_summary(models.Model):
    options_equity         = models.FloatField(default=0)
    stocks_equity          = models.FloatField(default=0)
    crypto_equity          = models.FloatField(default=0)
    portfolio_cash         = models.FloatField(default=0)
    buying_power           = models.FloatField(default=0)

class robinhood_stocks(models.Model):
    symbol                 = models.CharField(max_length=5)
    average_price          = models.FloatField()
    quantity               = models.FloatField()
    open_price             = models.FloatField()
    latest_price           = models.FloatField()
    equity                 = models.FloatField()
    cost_basis             = models.FloatField()
    unrealized_p_l         = models.FloatField(null=True)
    unrealized_p_l_percent = models.FloatField(null=True)
    today_p_l              = models.FloatField(null=True)
    today_p_l_percent      = models.FloatField(null=True)
    long_term              = models.BooleanField(default=False)

class robinhood_options(models.Model):
    chain_symbol           = models.CharField(max_length=5)
    option_id              = models.CharField(max_length=52)
    expiration_date        = models.CharField(max_length=20)
    option_type            = models.CharField(max_length=5)
    strike_price           = models.FloatField()
    average_price          = models.FloatField()
    quantity               = models.FloatField()
    previous_close_price   = models.FloatField()
    current_price          = models.FloatField()
    equity                 = models.FloatField()
    cost_basis             = models.FloatField()
    unrealized_p_l         = models.FloatField(null=True)
    unrealized_p_l_percent = models.FloatField(null=True)
    today_p_l              = models.FloatField(null=True)
    today_p_l_percent      = models.FloatField(null=True)
    long_term              = models.BooleanField(default=False)

class robinhood_crypto(models.Model):
    code                   = models.CharField(max_length=5)
    quantity               = models.FloatField()
    average_price          = models.FloatField()
    current_price          = models.FloatField()
    equity                 = models.FloatField()
    cost_basis             = models.FloatField()
    unrealized_p_l         = models.FloatField(null=True)
    unrealized_p_l_percent = models.FloatField(null=True)

class robinhood_instrument_symbol_lookup(models.Model):
    symbol                 = models.CharField(max_length=5)
    name                   = models.CharField(max_length=30)
    instrument_url         = models.CharField(max_length=92)

class robinhood_stock_split_events(models.Model):
    symbol                 = models.CharField(max_length=5)
    date                   = models.DateField()
    # ratio is new to old ratio, for example if stock splits into 2,
    # then ratio would be 2, and if stock reverse-splits from 2 to 1,
    # then ratio would be 0.5
    ratio                  = models.FloatField()

class robinhood_stock_order_history(models.Model):
    order_type             = models.CharField(max_length=5, default = 'buy')
    symbol                 = models.CharField(max_length=5)
    shares                 = models.FloatField()
    price                  = models.FloatField()
    timestamp              = models.DateTimeField()
