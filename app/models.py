# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class robinhood_summary(models.Model):
    timestamp              = models.DateTimeField()
    options_equity         = models.FloatField(default=0)
    stocks_equity          = models.FloatField(default=0)
    portfolio_cash         = models.FloatField(default=0)
    buying_power           = models.FloatField(default=0)
    today_realized_pl      = models.FloatField(default=0)
    total_realized_pl      = models.FloatField(default=0)

# table for stocks being held
class robinhood_stocks(models.Model):
    symbol                  = models.CharField(max_length=5)
    average_price           = models.FloatField()
    quantity                = models.FloatField()
    open_price              = models.FloatField()
    latest_price            = models.FloatField()
    equity                  = models.FloatField(default=0)
    cost_basis              = models.FloatField(default=0)
    unrealized_pl           = models.FloatField(default=0)
    long_term               = models.BooleanField(default=False)
    today_unrealized_pl     = models.FloatField(default=0)
    portfolio_diversity     = models.FloatField(default=0)

# table for options being held
class robinhood_options(models.Model):
    chain_symbol            = models.CharField(max_length=5)
    option_id               = models.CharField(max_length=52)
    expiration_date         = models.CharField(max_length=20)
    option_type             = models.CharField(max_length=5)
    strike_price            = models.FloatField()
    average_price           = models.FloatField()
    quantity                = models.FloatField()
    previous_close_price    = models.FloatField()
    current_price           = models.FloatField()
    trade_value_multiplier  = models.FloatField()
    equity                  = models.FloatField(default=0)
    cost_basis              = models.FloatField(default=0)
    unrealized_pl           = models.FloatField(default=0)
    long_term               = models.BooleanField(default=False)
    today_unrealized_pl     = models.FloatField(default=0)
    portfolio_diversity     = models.FloatField(default=0)

class robinhood_instrument_symbol_lookup(models.Model):
    symbol                 = models.CharField(max_length=5)
    name                   = models.CharField(max_length=30)
    instrument_url         = models.CharField(max_length=92)
    # at each transaction in order_histroy parsing, update this field.
    # this is expted to be overwritten multiple times
    average_price          = models.FloatField(default=0)
    # at each transaction in order_histroy parsing, update this field.
    # this is expted to be overwritten multiple times
    # this will go to 0 for stocks completely sold
    quantity               = models.FloatField(default=0)
    # at each transaction in order_histroy parsing, update this field
    # this is expted to be overwritten multiple times
    total_realized_pl      = models.FloatField(default=0)
    today_realized_pl      = models.FloatField(default=0)
    # at each transaction in order_histroy parsing, update this field
    # this is expted to be overwritten multiple times
    # this will go to 0 for stocks completely sold
    equity                 = models.FloatField(default=0)
    last_trade_ts          = models.DateTimeField(null=True)

class robinhood_stock_split_events(models.Model):
    symbol                 = models.CharField(max_length=5)
    new_symbol             = models.CharField(max_length=5)
    date                   = models.DateField()
    # ratio is new to old ratio, for example if stock splits into 2,
    # then ratio would be 2, and if stock reverse-splits from 2 to 1,
    # then ratio would be 0.5
    ratio                  = models.FloatField()
    processed              = models.BooleanField(default=False)

# stores order history next URLs good for fetching only latest orders
class robinhood_stock_order_history_next_urls(models.Model):
    next_url               = models.CharField(max_length=100)

class robinhood_stock_order_history(models.Model):
    processed              = models.BooleanField(default=False)
    order_type             = models.CharField(max_length=5, default = 'buy')
    symbol                 = models.CharField(max_length=5)
    shares                 = models.FloatField()
    price                  = models.FloatField()
    timestamp              = models.DateTimeField()
    # following fields are calculated and added to table as order history is parsed

    # avg price after current transaction for symbol.
    # this should match robinhood_stocks at the end of order history parsing
    # at each transaction update this to robinhood_instrument_symbol_lookup
    average_price          = models.FloatField(default=0)
    # quantity after current transaction for symbol.
    # this should match robinhood_stocks at the end of order history parsing
    # at each transaction update this to robinhood_instrument_symbol_lookup
    total_quantity         = models.FloatField(default=0)
    # realized pl after current transaction for symbol.
    # this should match robinhood_stocks at the end of order history parsing
    # at each transaction update this to robinhood_instrument_symbol_lookup
    order_realized_pl      = models.FloatField(default=0)
    total_realized_pl      = models.FloatField(default=0)
    # equity after current transaction for symbol.
    # this should match robinhood_stocks at the end of order history parsing
    # at each transaction update this to robinhood_instrument_symbol_lookup
    total_equity           = models.FloatField(default=0)
    # avg from day prior to last day of order history will be used to calculate today's realized/unrealized
