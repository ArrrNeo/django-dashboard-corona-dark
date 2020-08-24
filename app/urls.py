# -*- encoding: utf-8 -*-
"""
MIT License
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views

urlpatterns = [
    # Matches any html file - to be used for gentella
    # Avoid using your .html in your resources.
    # Or create a separate django app.
    re_path(r'^.*\.html', views.pages, name='pages'),

    # The home page
    path('', views.debit_spread_chart, name='debit_spread_chart'),

    path('summary/', views.summary, name='summary'),
    path('options/', views.options, name='options'),
    path('stocks/', views.stocks, name='stocks'),
    path('debit_spread_chart/', views.debit_spread_chart, name='debit_spread_chart'),
    path('covered_calls_chart/', views.covered_calls_chart, name='covered_calls_chart'),
    path('history/', views.history, name='history'),
]
