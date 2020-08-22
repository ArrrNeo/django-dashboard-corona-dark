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
from app.stock_utils import StockUtils
from app.models import options_held, stocks_held, stock_daily_db_table
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from heapq import nsmallest

# import pprint
# import datetime
# from datetime import date
# import dateutil.relativedelta

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
    total_equity = 0
    stocks_equity = 0
    portfolio_cash = 0
    options_equity = 0
    total_stocks_unrealized_pl = 0
    total_options_unrealized_pl = 0

    stocks_data = []
    stocks_labels = []
    options_data = []
    options_labels = []
    portfolio_data = []
    portfolio_labels = []

    current_dir = os.path.dirname(os.path.realpath(__file__))
    username = open(current_dir + '/username.txt', 'r').read()
    password = open(current_dir + '/password.txt', 'r').read()

    RhWrapper.rh_pull_portfolio_data(user_id=username, passwd=password)
    DbAccess.calc_my_stock_positions()
    DbAccess.calc_my_option_positions()

    portfolio_cash              = DbAccess.get_from_db('portfolio_cash')
    stocks_equity               = DbAccess.get_from_db('stocks_equity')
    options_equity              = DbAccess.get_from_db('options_equity')
    total_equity                = stocks_equity + options_equity + portfolio_cash

    total_stocks_unrealized_pl  = DbAccess.get_from_db('total_stocks_unrealized_pl')
    total_options_unrealized_pl = DbAccess.get_from_db('total_options_unrealized_pl')

    DbAccess.set_to_db('total_equity', total_equity)
    DbAccess.calc_portfolio_diversity(total_equity)

    portfolio_labels.append('stocks_equity')
    portfolio_labels.append('options_equity')
    portfolio_labels.append('cash')
    if total_equity:
        portfolio_data.append(round((stocks_equity  / total_equity) * 100, 2))
        portfolio_data.append(round((options_equity / total_equity) * 100, 2))
        portfolio_data.append(round((portfolio_cash / total_equity) * 100, 2))
    else:
        portfolio_data.append(0)
        portfolio_data.append(0)
        portfolio_data.append(0)

    qset = stocks_held.objects.all()
    for row in qset:
        stocks_data.append(row.pp_equity)
        stocks_labels.append(row.symbol)
    
    qset = options_held.objects.all()
    for row in qset:
        options_data.append(row.pp_equity)
        options_labels.append(row.symbol + ' ' + str(row.expiration_date) + ' ' + str(row.strike_price) + ' ' + str(row.option_type))

    data_for_template = {
        'stocks_labels'                : stocks_labels,
        'stocks_data'                  : stocks_data,
        'options_labels'               : options_labels,
        'options_data'                 : options_data,
        'portfolio_labels'             : portfolio_labels,
        'portfolio_data'               : portfolio_data,
        'options_equity'               : options_equity,
        'total_options_unrealized_pl'  : total_options_unrealized_pl,
        'stocks_equity'                : stocks_equity,
        'total_stocks_unrealized_pl'   : total_stocks_unrealized_pl,
        'margin_or_cash'               : portfolio_cash,
        'portfolio_value'              : total_equity,
    }
    return render(request, 'summary.html', data_for_template)

def history(request):
    ctx = {}
    current_dir = os.path.dirname(os.path.realpath(__file__))
    username = open(current_dir + '/username.txt', 'r').read()
    password = open(current_dir + '/password.txt', 'r').read()
    RhWrapper.rh_pull_orders_history(user_id=username, passwd=password)
    DbAccess.process_all_orders()

    qset = stock_daily_db_table.objects.all().order_by('-date')[:20]
    ctx['dates']   = [str(x.date) for x in qset]
    ctx['days_pl'] = [x.day_pl for x in qset]

    return render(request, 'history.html', ctx)

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

def debit_spread_chart(request):
    ctx = {}
    ticker = 'ROKU'
    num_strikes = 10
    calculations = []
    min_profit_pc = 5
    log_scale = False
    option_date = (StockUtils.getOptionsDate(ticker)[0])

    if request.method == 'POST':
        ticker = request.POST.get('ticker')
        option_date = str(request.POST.get('date'))
        num_strikes = int(request.POST.get('num_strikes'))
        log_scale = bool(request.POST.get('log_scale'))
        min_profit_pc = int(request.POST.get('min_profit_pc'))

    ctx['ticker'] = ticker
    ctx['date'] = option_date
    ctx['log_scale'] = log_scale
    ctx['num_strikes'] = num_strikes
    ctx['min_profit_pc'] = min_profit_pc

    info = StockUtils.getStockInfo(ticker)
    curr_price = (info['bid'] + info['ask'])/2
    ctx['curr_price'] = curr_price

    data = StockUtils.getOptions(ticker, option_date)
    data = nsmallest(num_strikes, data, key=lambda x: abs(x['strike'] - curr_price))
    data = sorted(data, key=lambda k: k['strike'])
    for i in range(0, len(data)):
        for j in range(i+1, len(data)):
            entry = {}
            entry['premium'] = data[i]['ask'] - data[j]['bid']
            entry['max_profit'] = (data[j]['strike'] - data[i]['strike']) - entry['premium']
            entry['long_strike'] = data[i]['strike']
            entry['short_strike'] = data[j]['strike']
            # entry['trade'] = 'buy: ' + str(entry['long_strike']) + 'c, sell: ' + str(entry['short_strike']) + 'c'
            if entry['premium'] == 0:
                continue
            entry['itm_percent'] = ((ctx['curr_price'] - (entry['long_strike'] + entry['premium'])) / ctx['curr_price']) * 100
            entry['max_profit_pc'] = (entry['max_profit'] / entry['premium']) * 100
            if entry['max_profit_pc'] <= min_profit_pc:
                continue
            calculations.append(entry)
    calculations = sorted(calculations, key=lambda k: k['max_profit_pc'])

    ctx['premium'] = [x['premium'] for x in calculations]
    ctx['max_profit'] = [x['max_profit'] for x in calculations]
    ctx['max_profit_pc'] = [x['max_profit_pc'] for x in calculations]
    ctx['long_strike'] = [x['long_strike'] for x in calculations]
    ctx['short_strike'] = [x['short_strike'] for x in calculations]
    ctx['itm_percent'] = [x['itm_percent'] for x in calculations]
    ctx['x_axis_chart_2'] = 'long_strike'
    ctx['y_axis_chart_2'] = 'max_profit_percent'
    # for entry in calculations:
    #     print ('trade: %s, premium: %7.2f, max_profit: %7.2f, max_profit_pc: %7.2f' % (entry['trade'], entry['premium'], entry['max_profit'], entry['max_profit_pc']))

    return render(request, 'debit_spread_chart.html', ctx)
