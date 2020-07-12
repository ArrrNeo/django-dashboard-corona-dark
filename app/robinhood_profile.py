#!/usr/bin/python3

import pprint
import robin_stocks as r
import robin_stocks.profiles as profiles
from django.utils import timezone
from app.models import robinhood_stocks, robinhood_summary, robinhood_options, robinhood_crypto

class Robinhood():
    def login(user, passwd):
        login = r.login(username=user, password=passwd)

    def get_my_stock_positions():
        equity_total = 0
        positions_data = r.get_open_stock_positions()

        for item in positions_data:
            instrument_url = item['instrument']
            # check if stock is already in database
            if not robinhood_stocks.objects.filter(instrument_url=instrument_url):
                # create and update: fixed info
                symbol              = r.get_instrument_by_url(instrument_url)['symbol']
                name                = r.get_name_by_symbol(symbol)
                obj                 = robinhood_stocks()
                obj.instrument_url  = instrument_url
                obj.symbol          = symbol
                obj.name            = name
            else:
                obj                 = robinhood_stocks.objects.get(instrument_url=instrument_url)
                symbol              = obj.symbol
                refresh_time        = obj.timestamp + timezone.timedelta(minutes=15)
                # check if update is needed
                if timezone.now() < refresh_time:
                    equity_total = equity_total + obj.equity
                    continue
            # update: dynamic info
            average_price           = float(item['average_buy_price'])
            quantity                = float(item['quantity'])
            latest_price            = float(r.get_latest_price(symbol)[0])
            equity                  = latest_price * quantity
            cost_basis              = average_price * quantity
            if not quantity:
                unrealized_p_l = 0
                unrealized_p_l_percent = 0
            else:
                unrealized_p_l          = equity - cost_basis
                unrealized_p_l_percent  = (unrealized_p_l / cost_basis) * 100
            # write to database
            obj.average_price           = average_price
            obj.quantity                = quantity
            # TODO: get correct open_price
            obj.open_price              = latest_price
            obj.latest_price            = latest_price
            obj.equity                  = equity
            obj.cost_basis              = cost_basis
            obj.unrealized_p_l          = unrealized_p_l
            obj.unrealized_p_l_percent  = unrealized_p_l_percent
            obj.timestamp               = timezone.now()
            # save database
            obj.save()
            equity_total                = equity_total + equity
        # write to summary database
        if not robinhood_summary.objects.all():
            obj = robinhood_summary()
        else:
            obj = robinhood_summary.objects.all()[0]
        obj.stocks_equity = equity_total
        # save database
        obj.save()
        return equity_total

    def get_my_options_positions():
        equity_total = 0
        options_position_data = r.get_open_option_positions()
        for item in options_position_data:
            option_id = item['option_id']
            # check if option is already in database
            if not robinhood_options.objects.filter(option_id=option_id):
                # update: fixed info:
                contract_into       = r.get_option_instrument_data_by_id(option_id)
                strike_price        = float(contract_into['strike_price'])
                expiration_date     = contract_into['expiration_date']
                option_type         = contract_into['type']
                chain_symbol        = item['chain_symbol']
                obj                 = robinhood_options()
                obj.option_id       = option_id
                obj.strike_price    = strike_price
                obj.expiration_date = expiration_date
                obj.option_type     = option_type
                obj.chain_symbol    = chain_symbol
            else:
                obj                 = robinhood_options.objects.get(option_id=option_id)
                refresh_time        = obj.timestamp + timezone.timedelta(minutes=15)
                # check if update is needed
                if timezone.now() < refresh_time:
                    equity_total = equity_total + obj.equity
                    continue
            # update: dynamic info
            average_price        = float(item['average_price']) / float(item['trade_value_multiplier'])
            quantity             = float(item['quantity'])
            market_data          = r.get_option_market_data_by_id(option_id)
            ask_price            = float(market_data['ask_price'])
            bid_price            = float(market_data['bid_price'])
            current_price        = (ask_price + bid_price) / 2
            equity               = current_price * quantity * float(item['trade_value_multiplier'])
            cost_basis           = average_price * quantity * float(item['trade_value_multiplier'])
            breakeven_price      = average_price + obj.strike_price
            percent_to_breakeven = 0.0
            if not quantity:
                unrealized_p_l = 0
                unrealized_p_l_percent = 0
            else:
                unrealized_p_l         = equity - cost_basis
                unrealized_p_l_percent = (unrealized_p_l / cost_basis) * 100
            # write to database
            obj.average_price          = average_price
            obj.quantity               = quantity
            obj.ask_price              = ask_price
            obj.bid_price              = bid_price
            obj.current_price          = current_price
            obj.equity                 = equity
            obj.cost_basis             = cost_basis
            obj.breakeven_price        = breakeven_price
            obj.percent_to_breakeven   = percent_to_breakeven
            # TODO: get correct open_price
            obj.open_price             = current_price
            obj.unrealized_p_l         = unrealized_p_l
            obj.unrealized_p_l_percent = unrealized_p_l_percent
            obj.timestamp              = timezone.now()
            # save database
            obj.save()
            equity_total    = equity_total + equity
        # write to summary database
        if not robinhood_summary.objects.all():
            obj = robinhood_summary()
        else:
            obj = robinhood_summary.objects.all()[0]
        obj.options_equity = equity_total
        # save database
        obj.save()
        return equity_total

    def get_my_crypto_positions():
        equity_total = 0
        crypto_position_data = r.get_crypto_positions()

        for item in crypto_position_data:
            code     = item['currency']['code']
            quantity = float(item['quantity'])
            if quantity:
                # check if crypto is already in database
                if not robinhood_crypto.objects.filter(code=code):
                    obj = robinhood_crypto()
                else:
                    obj = robinhood_crypto.objects.get(code=code)
                # update: dynamic info
                current_price               = float(r.get_crypto_quote(code)['mark_price'])
                average_price               = float(item['cost_bases'][0]['direct_cost_basis']) / quantity
                equity                      = current_price * quantity
                cost_basis                  = average_price * quantity
                unrealized_p_l              = equity - cost_basis
                unrealized_p_l_percent      = (unrealized_p_l / cost_basis) * 100
                # write to database
                obj.code                    = code
                obj.quantity                = quantity
                obj.average_price           = average_price
                # TODO: get correct open_price
                obj.open_price              = current_price
                obj.current_price           = current_price
                obj.equity                  = equity
                obj.cost_basis              = cost_basis
                obj.unrealized_p_l          = unrealized_p_l
                obj.unrealized_p_l_percent  = unrealized_p_l_percent
                obj.timestamp               = timezone.now()
                obj.save()
                # save database
                equity_total                = equity_total + equity
        # write to summary database
        if not robinhood_summary.objects.all():
            obj = robinhood_summary()
        else:
            obj = robinhood_summary.objects.all()[0]
        obj.crypto_equity = equity_total
        # save summary database
        obj.save()
        return equity_total

    def get_my_buying_power():
        buying_power = profiles.load_account_profile()['buying_power']
        # write to summary database
        if not robinhood_summary.objects.all():
            obj = robinhood_summary()
        else:
            obj = robinhood_summary.objects.all()[0]
        obj.buying_power = buying_power
        # save summary database
        obj.save()
        return buying_power

    def get_my_portfolio_cash():
        portfolio_cash = float(profiles.load_account_profile()['portfolio_cash'])
        # write to summary database
        if not robinhood_summary.objects.all():
            obj = robinhood_summary()
        else:
            obj = robinhood_summary.objects.all()[0]
        obj.portfolio_cash = portfolio_cash
        # save summary database
        obj.save()
        return portfolio_cash
