# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

import os
from django import template
from django.db.models import Sum
from django.template import loader
from django.http import HttpResponse
from django.http import JsonResponse
from app.models import robinhood_options
from app.robinhood_profile import Robinhood
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
import django_tables2 as tables

@login_required(login_url="/login/")
def index(request):
    return render(request, "index.html")

@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    print (request.path)
    try:
        load_template = request.path.split('/')[-1]
        print (load_template)
        html_template = loader.get_template( load_template )
        return HttpResponse(html_template.render(context, request))
    except template.TemplateDoesNotExist:
        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))
    except:
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))

def summary(request):
    labels = []
    data = []

    current_dir = os.path.dirname(os.path.realpath(__file__))
    username = open(current_dir + '/username.txt', 'r').read()
    password = open(current_dir + '/password.txt', 'r').read()

    Robinhood.login(user=username, passwd=password)
    stocks_equity, stocks_upl_today, stocks_upl_total    = Robinhood.get_my_stock_positions()
    options_equity, options_upl_today, options_upl_total = Robinhood.get_my_options_positions()
    crypto_equity   = Robinhood.get_my_crypto_positions()
    total_equity    = stocks_equity + options_equity + crypto_equity
    portfolio_cash  = Robinhood.get_my_portfolio_cash()
    portfolio_value = total_equity + portfolio_cash

    labels.append('stocks_equity')
    labels.append('options_equity')
    labels.append('crypto_equity')
    data.append(round((stocks_equity  / total_equity) * 100, 2))
    data.append(round((options_equity / total_equity) * 100, 2))
    data.append(round((crypto_equity  / total_equity) * 100, 2))

    data_for_template = {
                            'labels_1'             : labels,
                            'data_1'               : data,
                            'labels_2'             : labels,
                            'data_2'               : data,
                            'options_equity'       : options_equity,
                            'options_change'       : options_upl_today,
                            'options_total_change' : options_upl_total,
                            'stocks_equity'        : stocks_equity,
                            'stocks_change'        : stocks_upl_today,
                            'stocks_total_change'  : stocks_upl_total,
                            'crypto_equity'        : crypto_equity,
                            'crypto_change'        : 15.67,
                            'crypto_total_change'  : 45.67,
                            'margin_or_cash'       : portfolio_cash,
                            'portfolio_value'      : portfolio_value,
                        }

    return render(request, 'summary.html', data_for_template)

class OptionsTable(tables.Table):
    class Meta:
        model = robinhood_options

def options(request):
    table = OptionsTable(robinhood_options.objects.all(), exclude=['option_id', 'percent_to_breakeven', 'timestamp'])
    return render(request, 'options.html', { 'table': table })

