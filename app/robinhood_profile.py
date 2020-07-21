#!/usr/bin/python3

# misc imports
# import pprint
import dateutil.parser
from django.utils import timezone
from operator import itemgetter

# https://pyrh.readthedocs.io/en/latest/ imports
from pyrh import Robinhood

# https://robin-stocks.readthedocs.io/en/latest/functions.html imports
import robin_stocks as r
import robin_stocks.profiles as profiles

# db imports
from app.models import robinhood_stocks
from app.models import robinhood_crypto
from app.models import robinhood_options
from app.models import robinhood_summary
from app.models import robinhood_db_timestamps
from app.models import robinhood_stock_order_history
from app.models import robinhood_instrument_symbol_lookup

"""
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
    def login(user, passwd):
        login = r.login(username=user, password=passwd)

    @staticmethod
    def is_update_needed(instrument_type):
        obj = robinhood_db_timestamps.objects.filter(instrument_type=instrument_type)
        if not obj:
            obj = robinhood_db_timestamps()
            obj.timestamp = timezone.now()
            obj.instrument_type = instrument_type
            obj.save()
            return True
        else:
            obj = obj[0]
            refresh_time = obj.timestamp + timezone.timedelta(minutes=REFRESH_TIME)
            # check if update is needed
            if timezone.now() < refresh_time:
                return False
            # save the latest update timestamp
            obj.timestamp = timezone.now()
            obj.save()
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
    def get_my_stock_positions():
        equity_total = 0
        today_p_l_total = 0
        unrealized_p_l_total = 0

        if RobinhoodWrapper.is_update_needed('stocks'):
            # TODO: remove following line and find a way to delete sold securities from db
            robinhood_stocks.objects.all().delete()
            # get current owned securites and save to db
            positions_data = r.get_open_stock_positions()
            for item in positions_data:
                # check if instrument is present in robinhood_instrument_symbol_lookup table
                symbol, name = RobinhoodWrapper.get_symbol_from_instrument_url(item['instrument'])
                # check if stock is already in database
                obj = robinhood_stocks.objects.filter(symbol=symbol)
                if not obj:
                    # create and update: fixed info
                    obj                 = robinhood_stocks()
                    obj.symbol          = symbol
                    obj.name            = name
                else:
                    obj = obj[0]
                # update: dynamic info
                average_price           = float(item['average_buy_price'])
                quantity                = float(item['quantity'])
                latest_price            = float(r.get_latest_price(symbol)[0])
                open_price              = float(r.get_fundamentals(symbol)[0]['open'])
                equity                  = latest_price * quantity
                cost_basis              = average_price * quantity
                if not quantity:
                    unrealized_p_l = 0
                    unrealized_p_l_percent = 0
                    today_p_l = 0
                    today_p_l_percent = 0
                else:
                    unrealized_p_l          = equity - cost_basis
                    unrealized_p_l_percent  = (unrealized_p_l / cost_basis) * 100
                    today_p_l               = (latest_price - open_price) * quantity
                    today_p_l_percent       = (latest_price - open_price) / open_price * 100
                # write to database
                obj.average_price           = average_price
                obj.quantity                = quantity
                # TODO: get correct open_price
                obj.latest_price            = latest_price
                obj.equity                  = equity
                obj.cost_basis              = cost_basis
                obj.open_price              = open_price
                obj.today_p_l               = today_p_l
                obj.today_p_l_percent       = today_p_l_percent
                obj.unrealized_p_l          = unrealized_p_l
                obj.unrealized_p_l_percent  = unrealized_p_l_percent
                # save database
                obj.save()
                equity_total                = equity_total + equity
                today_p_l_total             = today_p_l_total + today_p_l
                unrealized_p_l_total        = unrealized_p_l_total + unrealized_p_l
            # write to summary database
            if not robinhood_summary.objects.all():
                obj = robinhood_summary()
            else:
                obj = robinhood_summary.objects.all()[0]
            obj.stocks_equity = equity_total
            # save database
            obj.save()
        else:
            qset = robinhood_stocks.objects.all()
            if qset:
                for item in qset:
                    equity_total         = equity_total         + item.equity
                    today_p_l_total      = today_p_l_total      + item.today_p_l
                    unrealized_p_l_total = unrealized_p_l_total + item.unrealized_p_l
        return equity_total, today_p_l_total, unrealized_p_l_total

    @staticmethod
    def get_my_options_positions():
        equity_total = 0
        today_p_l_total = 0
        unrealized_p_l_total = 0

        if RobinhoodWrapper.is_update_needed('options'):
            # TODO: remove following line and find a way to delete sold securities from db
            robinhood_options.objects.all().delete()
            # get current owned securites and save to db
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
                # update: dynamic info
                average_price        = float(item['average_price']) / float(item['trade_value_multiplier'])
                quantity             = float(item['quantity'])
                market_data          = r.get_option_market_data_by_id(option_id)
                previous_close_price = float(market_data['previous_close_price'])
                current_price        = float(market_data['adjusted_mark_price'])
                equity               = current_price * quantity * float(item['trade_value_multiplier'])
                cost_basis           = average_price * quantity * float(item['trade_value_multiplier'])
                if not quantity:
                    unrealized_p_l = 0
                    unrealized_p_l_percent = 0
                    today_p_l = 0
                    today_p_l_percent = 0
                else:
                    unrealized_p_l         = equity - cost_basis
                    unrealized_p_l_percent = (unrealized_p_l / cost_basis) * 100
                    today_p_l = (current_price - previous_close_price) * quantity * float(item['trade_value_multiplier'])
                    today_p_l_percent = (current_price - previous_close_price) / previous_close_price * 100
                # write to database
                obj.average_price          = average_price
                obj.quantity               = quantity
                obj.current_price          = current_price
                obj.equity                 = equity
                obj.cost_basis             = cost_basis
                obj.previous_close_price   = previous_close_price
                obj.today_p_l              = today_p_l
                obj.today_p_l_percent      = today_p_l_percent
                obj.unrealized_p_l         = unrealized_p_l
                obj.unrealized_p_l_percent = unrealized_p_l_percent
                obj.timestamp              = timezone.now()
                # save database
                obj.save()
                equity_total               = equity_total + equity
                today_p_l_total            = today_p_l_total + today_p_l
                unrealized_p_l_total       = unrealized_p_l_total + unrealized_p_l
            # write to summary database
            if not robinhood_summary.objects.all():
                obj = robinhood_summary()
            else:
                obj = robinhood_summary.objects.all()[0]
            obj.options_equity = equity_total
            # save database
            obj.save()
        else:
            qset = robinhood_options.objects.all()
            if qset:
                for item in qset:
                    equity_total         = equity_total         + item.equity
                    today_p_l_total      = today_p_l_total      + item.today_p_l
                    unrealized_p_l_total = unrealized_p_l_total + item.unrealized_p_l
        return equity_total, today_p_l_total, unrealized_p_l_total

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    # using pyrh for get complete order history. following functions for that only
    def fetch_json_by_url(rb_client, url):
        return rb_client.session.get(url).json()

    @staticmethod
    def get_all_history_orders(rb_client):
        orders = []
        past_orders = rb_client.order_history()
        orders.extend(past_orders["results"])
        while past_orders["next"]:
            print("{} order fetched".format(len(orders)))
            next_url = past_orders["next"]
            past_orders = RobinhoodWrapper.fetch_json_by_url(rb_client, next_url)
            orders.extend(past_orders["results"])
        print("{} order fetched".format(len(orders)))
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
