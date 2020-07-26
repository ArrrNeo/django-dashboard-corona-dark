#!/usr/bin/python3

# misc imports
# import pprint
import os
import csv
import datetime
import dateutil.parser
from operator import itemgetter
from django.utils import timezone

# https://pyrh.readthedocs.io/en/latest/ imports
from pyrh import Robinhood

# https://robin-stocks.readthedocs.io/en/latest/functions.html imports
import robin_stocks as r
import robin_stocks.profiles as profiles

# db imports
from app.models import robinhood_stocks
from app.models import robinhood_options
from app.models import robinhood_summary
from app.models import robinhood_stock_split_events
from app.models import robinhood_stock_order_history
from app.models import robinhood_instrument_symbol_lookup
from app.models import robinhood_stock_order_history_next_urls

"""
stock position element
{
    'url': 'https://api.robinhood.com/positions/5QR11032/8f92e76f-1e0e-4478-8580-16a6ffcfaef5/'
    'instrument': 'https://api.robinhood.com/instruments/8f92e76f-1e0e-4478-8580-16a6ffcfaef5/'
    'account': 'https://api.robinhood.com/accounts/5QR11032/'
    'account_number': '5QR11032'
    'average_buy_price': '321.4969'
    'pending_average_buy_price': '321.4969'
    'quantity': '0.06220900'
    'intraday_average_buy_price': '0.0000'
    'intraday_quantity': '0.00000000'
    'shares_held_for_buys': '0.00000000'
    'shares_held_for_sells': '0.00000000'
    'shares_held_for_stock_grants': '0.00000000'
    'shares_held_for_options_collateral': '0.00000000'
    'shares_held_for_options_events': '0.00000000'
    'shares_pending_from_options_events': '0.00000000'
    'updated_at': '2020-07-15T17:50:58.941303Z'
    'created_at': '2020-07-13T16:47:28.925326Z'
}

stock fundmentals
[
    {
        'average_volume': '10129946.100000',
        'average_volume_2_weeks': '10129946.100000',
        'ceo': 'Jon P. Stonehouse',
        'description': 'BioCryst Pharmaceuticals, Inc. designs and develops '
                       'novel, oral and small-molecule medicines. Its drug '
                       'candidates include Berotralstat, BCX9930, BCX9250, '
                       'RAPIVAB, ALPIVAB, RAPIACTA, PERAMIFLU, Galidesivir and '
                       'Mundesine. The company was founded in 1986 and is '
                       'headquartered in Durham, NC.',
        'dividend_yield': None,
        'float': '173660434.064000',
        'headquarters_city': 'Durham',
        'headquarters_state': 'North Carolina',
        'high': '5.450000',
        'high_52_weeks': '6.286200',
        'industry': 'Biotechnology',
        'instrument': 'https://api.robinhood.com/instruments/024d9f18-182c-463d-9573-2718b19dfea9/',
        'low': '4.940000',
        'low_52_weeks': '1.380000',
        'market_cap': '873184950.000000',
        'num_employees': 140,
        'open': '5.418900',
        'pb_ratio': '229.713000',
        'pe_ratio': None,
        'sector': 'Health Technology',
        'shares_outstanding': '176401000.000000',
        'symbol': 'BCRX',
        'volume': '8108288.000000',
        'year_founded': 1986
    }
]


options_position_data
{
    'account': 'https://api.robinhood.com/accounts/5QR11032/',
    'average_price': '70.0000',
    'chain_id': 'e416e5a0-cf91-4002-88d4-99bac794476a',
    'chain_symbol': 'SPXS',
    'created_at': '2020-04-17T15:10:13.581044Z',
    'id': 'f78ca853-e8b4-4871-b289-b6b1ec88d947',
    'intraday_average_open_price': '0.0000',
    'intraday_quantity': '0.0000',
    'option': 'https://api.robinhood.com/options/instruments/a8b4d270-fd34-4e0f-89fd-7670e4c1df2e/',
    'option_id': 'a8b4d270-fd34-4e0f-89fd-7670e4c1df2e',
    'pending_assignment_quantity': '0.0000',
    'pending_buy_quantity': '0.0000',
    'pending_exercise_quantity': '0.0000',
    'pending_expiration_quantity': '0.0000',
    'pending_expired_quantity': '0.0000',
    'pending_sell_quantity': '0.0000',
    'quantity': '1.0000',
    'trade_value_multiplier': '100.0000',
    'type': 'long',
    'updated_at': '2020-05-07T13:17:10.901353Z',
    'url': 'https://api.robinhood.com/options/positions/f78ca853-e8b4-4871-b289-b6b1ec88d947/'
}

market_data for options
{
    'adjusted_mark_price': '8.950000',
    'ask_price': '10.900000',
    'ask_size': 3,
    'bid_price': '7.000000',
    'bid_size': 10,
    'break_even_price': '358.950000',
    'chance_of_profit_long': '0.113807',
    'chance_of_profit_short': '0.886193',
    'delta': '0.214198',
    'gamma': '0.003403',
    'high_fill_rate_buy_price': '10.170000',
    'high_fill_rate_sell_price': '7.670000',
    'high_price': '12.500000',
    'implied_volatility': '0.275554',
    'instrument': 'https://api.robinhood.com/options/instruments/1b587fbc-7876-4c9a-a2cd-6719e0142434/',
    'last_trade_price': '9.000000',
    'last_trade_size': 5,
    'low_fill_rate_buy_price': '8.690000',
    'low_fill_rate_sell_price': '9.140000',
    'low_price': '8.600000',
    'mark_price': '8.950000',
    'open_interest': 5947,
    'previous_close_date': '2020-07-10',
    'previous_close_price': '11.650000',
    'rho': '0.686109',
    'theta': '-0.022605',
    'vega': '0.906464',
    'volume': 233
}
"""

# pp = pprint.PrettyPrinter(indent=4)
#refresh time in minutes
REFRESH_TIME = 15

class RobinhoodWrapper():
    @staticmethod
    def is_update_needed():
        summary = robinhood_summary.objects.all()
        if not summary:
            summary = robinhood_summary()
            summary.timestamp = timezone.now()
            summary.save()
            return True
        else:
            summary = summary[0]
            # if today date is > timestamp date, reset today_realized_pl
            if timezone.now().date() > summary.timestamp.date():
                summary.today_realized_pl = 0
                summary.today_unrealized_pl = 0

            refresh_time = summary.timestamp + timezone.timedelta(minutes=REFRESH_TIME)
            # check if update is needed
            if timezone.now() < refresh_time:
                return False
            # save the latest update timestamp
            summary.timestamp = timezone.now()
            summary.save()
            return True

    # get symbol from url from db lookup table, if not found save it
    @staticmethod
    def get_symbol_from_instrument_url(url):
        obj = robinhood_instrument_symbol_lookup.objects.filter(instrument_url=url)
        if not obj:
            obj                 = robinhood_instrument_symbol_lookup()
            symbol              = r.get_instrument_by_url(url)['symbol']
            name                = r.get_name_by_symbol(symbol)
            obj.symbol          = symbol
            obj.name            = name
            obj.instrument_url  = url
            obj.save()
        else:
            obj = obj[0]
            symbol              = obj.symbol
            name                = obj.name
        return symbol, name

    @staticmethod
    def get_profile_data(user_id, passwd):
        r.login(username=user_id, password=passwd)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        robinhood_stock_split_events.objects.all().delete()
        stock_splits_csv = csv.reader(open(current_dir + '/stock_splits.csv', 'r'))
        for row in stock_splits_csv:
            print (row)
            obj = robinhood_stock_split_events()
            obj.symbol = row[0]
            obj.date = datetime.datetime.strptime(row[1], "%Y-%m-%d").date()
            obj.ratio = float(row[2])
            obj.new_symbol = row[3]
            obj.save()

        if RobinhoodWrapper.is_update_needed():
            obj = robinhood_summary.objects.all()
            if not obj:
                obj = robinhood_summary()
                obj.timestamp = timezone.now()
            else:
                obj = obj[0]
            obj.buying_power    = float(profiles.load_account_profile()['buying_power'])
            obj.portfolio_cash  = float(profiles.load_account_profile()['portfolio_cash'])
            obj.save()

            # remove current entries
            robinhood_stocks.objects.all().delete()
            # get current owned securites and save to db
            positions_data = r.get_open_stock_positions()
            for item in positions_data:
                quantity = float(item['quantity'])
                if not quantity:
                    continue
                # check if instrument is present in robinhood_instrument_symbol_lookup table
                obj                     = robinhood_stocks()
                obj.symbol, obj.name    = RobinhoodWrapper.get_symbol_from_instrument_url(item['instrument'])
                obj.quantity            = quantity
                obj.average_price       = float(item['average_buy_price'])
                obj.latest_price        = float(r.get_latest_price(obj.symbol)[0])
                obj.open_price          = float(r.get_fundamentals(obj.symbol)[0]['open'])
                obj.save()

            # remove current entries
            robinhood_options.objects.all().delete()
            # get current owned securites and save to db
            options_position_data = r.get_open_option_positions()
            for item in options_position_data:
                quantity = float(item['quantity'])
                if not quantity:
                    continue
                obj                        = robinhood_options()
                obj.option_id              = item['option_id']
                contract_into              = r.get_option_instrument_data_by_id(obj.option_id)
                obj.strike_price           = float(contract_into['strike_price'])
                obj.expiration_date        = contract_into['expiration_date']
                obj.option_type            = contract_into['type']
                obj.chain_symbol           = item['chain_symbol']
                obj.trade_value_multiplier = float(item['trade_value_multiplier'])
                obj.average_price          = float(item['average_price']) / obj.trade_value_multiplier
                obj.quantity               = float(item['quantity'])
                market_data                = r.get_option_market_data_by_id(obj.option_id)
                obj.previous_close_price   = float(market_data['previous_close_price'])
                obj.current_price          = float(market_data['adjusted_mark_price'])
                obj.save()


    @staticmethod
    def get_my_stock_positions():
        equity_total = 0
        today_unrealized_pl = 0
        total_unrealized_pl = 0

        qset = robinhood_stocks.objects.all()
        if not qset:
            return equity_total, today_unrealized_pl, total_unrealized_pl

        for item in qset:
            # if item.symbol present robinhood_stock_split_events, update average from first robinhood_instrument_symbol_lookup
            if robinhood_stock_split_events.objects.filter(new_symbol=item.symbol):
                item.average_price = robinhood_instrument_symbol_lookup.objects.filter(symbol=item.symbol)[0].average_price
            item.equity              = item.latest_price * item.quantity
            item.cost_basis          = item.average_price * item.quantity
            item.unrealized_pl       = item.equity - item.cost_basis
            item.today_unrealized_pl = item.equity - (item.open_price * item.quantity)
            item.save()

            equity_total             = equity_total + item.equity
            total_unrealized_pl      = total_unrealized_pl + item.unrealized_pl
            today_unrealized_pl      = today_unrealized_pl + item.today_unrealized_pl

        return equity_total, today_unrealized_pl, total_unrealized_pl

    @staticmethod
    def get_my_options_positions():
        equity_total = 0
        today_unrealized_pl = 0
        total_unrealized_pl = 0

        qset = robinhood_options.objects.all()
        if not qset:
            return equity_total, today_unrealized_pl, total_unrealized_pl

        for item in qset:
            item.equity               = item.current_price * item.quantity * item.trade_value_multiplier
            item.cost_basis           = item.average_price * item.quantity * item.trade_value_multiplier
            item.unrealized_pl        = item.equity - item.cost_basis
            item.today_unrealized_pl  = item.equity - (item.previous_close_price * item.quantity) * item.trade_value_multiplier
            print ('sym: %6s, exp: %12s, avg: %6.2f, num: %3d, equity: %7.2f, prev: %6.2f, current: %6.2f, total: %8.2f, today: %8.2f' % (item.chain_symbol, item.expiration_date, item.average_price, item.quantity, item.equity, item.previous_close_price, item.current_price, item.unrealized_pl, item.today_unrealized_pl))
            item.save()

            equity_total               = equity_total + item.equity
            total_unrealized_pl        = total_unrealized_pl + item.unrealized_pl
            today_unrealized_pl        = today_unrealized_pl + item.today_unrealized_pl

        return equity_total, today_unrealized_pl, total_unrealized_pl

    @staticmethod
    def get_my_buying_power():
        obj = robinhood_summary.objects.all()
        if not obj:
            return 0
        else:
            return obj[0].buying_power

    @staticmethod
    def get_my_portfolio_cash():
        obj = robinhood_summary.objects.all()
        if not obj:
            return 0
        else:
            return obj[0].portfolio_cash

    @staticmethod
    def get_realized_pl():
        obj = robinhood_summary.objects.all()
        if not obj:
            return 0, 0
        else:
            return obj[0].today_realized_pl, obj[0].total_realized_pl

    @staticmethod
    # using pyrh for get complete order history. following functions for that only
    def fetch_json_by_url(rb_client, url):
        return rb_client.session.get(url).json()

    @staticmethod
    def get_all_history_orders(rb_client):
        orders = []
        history_urls = robinhood_stock_order_history_next_urls.objects.all().order_by('-id')
        if not history_urls:
            past_orders = rb_client.order_history()
        else:
            history_urls = history_urls[0]
            past_orders = RobinhoodWrapper.fetch_json_by_url(rb_client, history_urls.next_url)
        orders.extend(past_orders["results"])
        print("{} order fetched".format(len(orders)))
        while past_orders["next"]:
            next_url = past_orders["next"]
            history_urls = robinhood_stock_order_history_next_urls()
            history_urls.next_url = next_url
            history_urls.save()
            past_orders = RobinhoodWrapper.fetch_json_by_url(rb_client, next_url)
            print("{} order fetched".format(len(orders)))
            orders.extend(past_orders["results"])
        return orders

    @staticmethod
    def get_orders_history(user_id, passwd):
        pyrh_rb = Robinhood()
        pyrh_rb.login(username=user_id, password=passwd, challenge_type="sms")
        past_orders = RobinhoodWrapper.get_all_history_orders(pyrh_rb)
        # keep past orders in reverse chronological order
        past_orders_sorted = sorted(past_orders, key=itemgetter('last_transaction_at'), reverse=True)
        orders_saved_to_db = 0
        for order in past_orders_sorted:
            # check if order already in db
            obj = robinhood_stock_order_history.objects.filter(timestamp=dateutil.parser.parse(order['last_transaction_at']))
            if not obj:
                if order['state'] == 'filled':
                    obj                 = robinhood_stock_order_history()
                    obj.order_type      = order['side']
                    obj.price           = order['average_price']
                    obj.shares          = order['cumulative_quantity']
                    obj.symbol, name    = RobinhoodWrapper.get_symbol_from_instrument_url(order['instrument'])
                    obj.state           = order['state']
                    obj.timestamp       = dateutil.parser.parse(order['last_transaction_at'])
                    obj.save()
                    orders_saved_to_db = orders_saved_to_db + 1
            else:
                break

        print ('orders_saved_to_db: ' + str(orders_saved_to_db))

    @staticmethod
    def calculate_pl():
        # in following dict, key is symbol and value is another dict with quantity/avg_price/equity/realized_pl as keys of nested dict
        stocks = {}

        # for realized_pl today/total
        summary = robinhood_summary.objects.all()
        if summary:
            summary = summary[0]
        else:
            summary = robinhood_summary()
            summary.timestamp = timezone.now()

        orders = robinhood_stock_order_history.objects.filter(processed=False).order_by('timestamp')
        # parse complete robinhood_stock_order_history.
        # TODO: only parse, un-parsed transactions
        # and calcaulate, avg, quantity, equity, realized_pl at end of each transaction
        for order in orders:
            sell_order_exception = False
            prev_ticker = ''
            # if symbol in stock_split:
            split_event = robinhood_stock_split_events.objects.filter(new_symbol=order.symbol)
            if split_event and split_event[0].processed == False:
                split_event = split_event[0]
                if order.timestamp.date() > split_event.date:
                    split_event.processed = True
                    split_event.save()
                    if split_event.ratio != 0:
                        # update previous stock avg and quantity
                        stocks[order.symbol]['total_quantity'] = stocks[order.symbol]['total_quantity'] * split_event.ratio
                        stocks[order.symbol]['average_price']  = stocks[order.symbol]['average_price'] / split_event.ratio
                    else:
                        sell_order_exception = True
                        prev_ticker = split_event.symbol
                        print ('adding exception for old_ticker: ' + split_event.symbol + ' new_ticker: ' + order.symbol)
            if order.order_type == 'buy':
                if order.symbol not in stocks:
                    stocks[order.symbol] = {}
                    stocks[order.symbol]['total_quantity']          = order.shares
                    stocks[order.symbol]['average_price']           = order.price
                    stocks[order.symbol]['total_equity']            = order.shares * order.price
                    stocks[order.symbol]['order_realized_pl']       = 0
                    stocks[order.symbol]['total_realized_pl']       = 0
                    stocks[order.symbol]['today_realized_pl']       = 0
                else:
                    stocks[order.symbol]['total_quantity']          = stocks[order.symbol]['total_quantity'] + order.shares
                    stocks[order.symbol]['total_equity']            = stocks[order.symbol]['total_equity'] + order.shares * order.price
                    stocks[order.symbol]['average_price']           = stocks[order.symbol]['total_equity'] / stocks[order.symbol]['total_quantity']
                    # no change in total_realized_pl/today_realized_pl, but realized_pl = 0 since this was buy order
                    stocks[order.symbol]['order_realized_pl']       = 0
            else:
                # order was sell
                if order.symbol not in stocks:
                    if sell_order_exception is True:
                        stocks[order.symbol] = {}
                        stocks[order.symbol]['total_equity']      = 0
                        stocks[order.symbol]['total_quantity']    = 0
                        stocks[order.symbol]['today_realized_pl'] = 0
                        stocks[order.symbol]['total_realized_pl'] = 0
                        stocks[order.symbol]['average_price']     = stocks[prev_ticker]['total_equity']/order.shares
                        stocks[order.symbol]['order_realized_pl'] = (order.price * order.shares) - stocks[prev_ticker]['total_equity']
                        # delete prev ticker entry for dic
                        print ('deleting prev ticker: ' + prev_ticker)
                        stocks.pop(prev_ticker, None)
                    else:
                        # fatal error
                        print (order.symbol + ': sell without buy, check order history')
                        continue
                else:
                    stocks[order.symbol]['total_quantity'] = stocks[order.symbol]['total_quantity'] - order.shares
                    stocks[order.symbol]['total_equity']   = stocks[order.symbol]['total_quantity'] * stocks[order.symbol]['average_price']
                    # realized_pl is only the profit/loss in this order
                    stocks[order.symbol]['order_realized_pl'] = (order.price - stocks[order.symbol]['average_price']) * order.shares


                stocks[order.symbol]['total_realized_pl']    = stocks[order.symbol]['total_realized_pl'] + stocks[order.symbol]['order_realized_pl']
                if order.timestamp.date() == timezone.now().date():
                    # order was sell and date was today
                    stocks[order.symbol]['today_realized_pl'] = stocks[order.symbol]['today_realized_pl'] + stocks[order.symbol]['order_realized_pl']

            stocks[order.symbol]['last_trade_ts'] = order.timestamp
            # update the same values in the transaction table
            order.average_price       = stocks[order.symbol]['average_price']
            order.total_equity        = stocks[order.symbol]['total_equity']
            order.total_quantity      = stocks[order.symbol]['total_quantity']
            order.order_realized_pl   = stocks[order.symbol]['order_realized_pl']
            order.total_realized_pl   = stocks[order.symbol]['total_realized_pl']
            order.processed           = True
            order.save()

            summary.total_realized_pl = summary.total_realized_pl + stocks[order.symbol]['order_realized_pl']
            summary.today_realized_pl = summary.today_realized_pl + stocks[order.symbol]['today_realized_pl']
            summary.save()
        print ('today_realized_pl: %9.2f, total_realized_pl: %9.2f' % (summary.today_realized_pl, summary.total_realized_pl))

        # parse disctionary created
        # update same fields in robinhood_instrument_symbol_lookup
        for symbol in stocks.keys():
            obj = robinhood_instrument_symbol_lookup.objects.filter(symbol=symbol)
            if not obj:
                # fatal error
                print (symbol + ' not present in lookup table..')
            else:
                obj = obj[0]
                obj.average_price     = stocks[symbol]['average_price']
                obj.quantity          = stocks[symbol]['total_quantity']
                obj.equity            = stocks[symbol]['total_equity']
                obj.total_realized_pl = stocks[symbol]['total_realized_pl']
                obj.today_realized_pl = stocks[symbol]['today_realized_pl']
                obj.last_trade_ts     = stocks[symbol]['last_trade_ts']
                obj.save()
