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
from app.rh_wrapper import RhWrapper
from app.db_access import DbAccess
from app.models import options_held, stocks_held
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

@login_required(login_url="/login/")
def index(request):
    return render(request, "index.html")

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
    data = []
    labels = []
    total_equity = 0
    stocks_equity = 0
    portfolio_cash = 0
    options_equity = 0
    today_stocks_realized_pl = 0
    total_stocks_realized_pl = 0
    today_stocks_unrealized_pl = 0
    total_stocks_unrealized_pl = 0
    today_options_unrealized_pl = 0
    total_options_unrealized_pl = 0

    current_dir = os.path.dirname(os.path.realpath(__file__))
    username = open(current_dir + '/username.txt', 'r').read()
    password = open(current_dir + '/password.txt', 'r').read()

    RhWrapper.rh_pull_orders_history(user_id=username, passwd=password)
    RhWrapper.rh_pull_portfolio_data(user_id=username, passwd=password)

    DbAccess.calc_pl_from_order_history()
    DbAccess.calc_my_stock_positions()
    DbAccess.calc_my_option_positions()

    portfolio_cash              = DbAccess.get_from_db('portfolio_cash')
    stocks_equity               = DbAccess.get_from_db('stocks_equity')
    options_equity              = DbAccess.get_from_db('options_equity')
    total_equity                = stocks_equity + options_equity + portfolio_cash

    today_stocks_realized_pl    = DbAccess.get_from_db('today_stocks_realized_pl')
    total_stocks_realized_pl    = DbAccess.get_from_db('total_stocks_realized_pl')
    today_stocks_unrealized_pl  = DbAccess.get_from_db('today_stocks_unrealized_pl')
    total_stocks_unrealized_pl  = DbAccess.get_from_db('total_stocks_unrealized_pl')

    today_options_unrealized_pl = DbAccess.get_from_db('today_options_unrealized_pl')
    total_options_unrealized_pl = DbAccess.get_from_db('total_options_unrealized_pl')

    DbAccess.set_to_db('options_equity', total_equity)
    DbAccess.calc_portfolio_diversity(total_equity)

    labels.append('stocks_equity')
    labels.append('options_equity')
    labels.append('cash')
    if total_equity:
        data.append(round((stocks_equity  / total_equity) * 100, 2))
        data.append(round((options_equity / total_equity) * 100, 2))
        data.append(round((portfolio_cash / total_equity) * 100, 2))
    else:
        data.append(0)
        data.append(0)
        data.append(0)

    data_for_template = {
        'labels_1'                     : labels,
        'data_1'                       : data,
        'labels_2'                     : labels,
        'data_2'                       : data,
        'options_equity'               : options_equity,
        'total_options_unrealized_pl'  : total_options_unrealized_pl,
        'today_options_unrealized_pl'  : today_options_unrealized_pl,
        'stocks_equity'                : stocks_equity,
        'today_stocks_realized_pl'     : today_stocks_realized_pl,
        'total_stocks_realized_pl'     : total_stocks_realized_pl,
        'total_stocks_unrealized_pl'   : total_stocks_unrealized_pl,
        'today_stocks_unrealized_pl'   : today_stocks_unrealized_pl,
        'margin_or_cash'               : portfolio_cash,
        'portfolio_value'              : total_equity,
    }
    return render(request, 'summary.html', data_for_template)

def options(request):
    qset = options_held.objects.all()
    if request.method == 'POST':
        long_term_list = request.POST.getlist('long_term')
        for item in qset:
            if item.option_id in long_term_list:
                item.long_term = True
            else:
                item.long_term = False
            item.save()

    ctx = {}
    ctx['table'] = list(qset)
    return render(request, 'options.html', ctx)

def stocks(request):
    qset = stocks_held.objects.all()
    if request.method == 'POST':
        long_term_list = request.POST.getlist('long_term')
        for item in qset:
            if item.symbol in long_term_list:
                print (item.symbol)
                item.long_term = True
            else:
                item.long_term = False
            item.save()

    ctx = {}
    ctx['table'] = list(qset)
    return render(request, 'stocks.html', ctx)
