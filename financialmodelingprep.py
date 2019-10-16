import requests
import pandas as pd
from pandas.io.json import json_normalize
import re
import datetime as dt
import json
from decimal import Decimal
import numpy as np
from itertools import zip_longest

anndateformat = '%Y-%m'
quarterdateformat = '%Y-%m-%d'


class FinancialModelingPrep ():

    def __init__(self, symbols=[]):

        if symbols is not []:
            self.set_symbols(symbols)

        self.base_url = "https://financialmodelingprep.com/api/"

    def set_symbols(self, symbols):

        if type(symbols) is str:
            symbols = [symbols]


        self.symbols = symbols



    def _get_payload(self, url, params, **kwargs):

        def camelize(string):
            l = string.split(" ")

            return "".join([word.capitalize() for word in l])

        def convert_types(d):
            for k, v in d.items():
                #print(k, v, type(v))
                new_v = v
                if type(v) is str:
                    if re.match('^[-+]?[0-9]*\.[0-9]+$', v):  #match for float
                        new_v = float(v)

                    if re.match('^[-+]?\d+?(?!\.)$', v):  #match for integer
                        new_v = int(v)

                    if re.match('^\d+\.?\d*\-\d+\.?\d*$', v): #match for range
                        l = v.split("-")
                        new_v = tuple([float(str) for str in l])
                    '''
                    if re.match('^[()]?\d+\%[()]?', v):   #match for percentage
                        new_v = float(v) '''

                    if re.match('^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))$', v):  #match for date
                        new_v = dt.datetime.strptime(v, quarterdateformat).date()

                    if v == "":
                        new_v = np.nan
                d[k] = new_v
            d = {camelize(k): v for k, v in d.items()}
            return d

        params.update(kwargs)
        r = requests.get(url, params)
        #print(r.url)
        return json.loads(r.text, object_hook=convert_types)

    def _json_normalize(self, jd):

        if type(jd) is not dict:
            print("expecting a dictionary")

        statement_name = list(jd.keys())[0]

        frames = [symbol_data for symbol_data in jd[statement_name]]


    def financial_statements(self, chunksize = 3, type = 'is', ret_df=True, **kwargs ):

        '''Returns an aggregated dataframe of financial statements

        parameters:
        chunksize: integer, default = 3.   Size of batch for each fetch.
        type: string, "bs", "cf" or "is".  Default is "is".
              'is' - income statement
              'cf' - cash flow statement
              'bs' - balance sheet statement
        ret_df: bool, default= True.  return dataframe (True) or json dictionary (False).
        period: string, "quarter" or "annual." Period for reporting data.
        **kwargs - other parameters for the web request (eg. format = "json")
        '''

        type_dict = {'is': 'financials/income-statement',
                    'bs': 'financials/balance-sheet-statement',
                    'cf': 'financials/cash-flow-statement'}


        base_key = 'Financialstatementlist'
        chunks = self._grouper(self.symbols, chunksize)
        self.params = params = kwargs

        l = []
        d = {}
        jd = {}
        for chunk in chunks:
            chunk = [c for c in chunk if c is not None]
            symbollist = (",").join(chunk)
            url =  "{0}v3/{1}/{2}".format(self.base_url, type_dict[type], symbollist)
            self.url = url
            print ("Getting chunk {}".format(chunk))
            d = self._get_payload(url, params)
            try:
                l.extend(d[base_key])
            except:
                #print(jd)
                l.append(d)

        jd.update({base_key:l})
        self._last_jd = {'source': 'financial_statement',
                    'base_key': base_key,
                    'payload': jd}
        if ret_df:
            return self._return_agg_df()
        else:
            return jd

    def company_profile(self, **kwargs):

        d = {}
        self.endpoint = 'v3/company/profile/'
        return self._generic_iter()

    def financial_ratios(self, **kwargs):

        d={}
        self.endpoint = 'financial-ratios/'
        return self._generic_iter()

    def enterprise_value(self, **kwargs):

        d={}
        self.endpoint = 'v3/enterprise-value/'
        return self._generic_iter()

    def company_key_metrics(self, **kwargs):

        d={}
        self.endpoint = 'v3/company-key-metrics/'
        return self._generic_iter()

    def financial_growth(self, **kwargs):

        d={}
        self.endpoint = 'v3/financial-statement-growth/'
        return self._generic_iter()

    def company_rating(self, **kwargs):

        d={}
        self.endpoint = 'v3/company/rating/'
        return self._generic_iter()

    def company_dcf(self, **kwargs):

        d={}
        self.endpoint = 'v3/company/discounted-cash-flow/'
        return self._generic_iter()

    def company_historical_dcf(self, **kwargs):

        d={}
        self.endpoint = 'v3/company/historical-discounted-cash-flow/'
        return self._generic_iter()

    def real_time_price(self, **kwargs):

        d={}
        self.endpoint = 'v3/stock/real-time-price/'
        return self._generic_iter()

    def historical_price(self, **kwargs):

        d={}
        self.endpoint = 'v3/historical-price-full/'
        return self._generic_iter(serietype='line')

    def historical_price_ohlcv(self, **kwargs):

        d={}
        self.endpoint = 'v3/historical-price-full/'
        return self._generic_iter()

    def symbols_list(self, **kwargs):
        self.endpoint = 'v3/company/stock/list'
        url = self.base_url + self.endpoint
        self.url = url
        self.params = params = kwargs
        return self._get_payload(url, params)

    def _generic_iter (self, **kwargs):

        d = {}
        url = self.base_url + self.endpoint
        self.url=url
        self.params = params = kwargs
        for symbol in self.symbols:
            url = url + symbol
            jd = self._get_payload(url, params, datatype='json')
            d.update({symbol: jd})
        return d

    def _grouper(self, iterable, n, fillvalue=None):
        "Collect data into fixed-length chunks or blocks"
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    def _return_agg_df(self):
        jd = self._last_jd['payload']
        base_key = self._last_jd['base_key']
        payload = jd[base_key]

        data = payload[0]['Financials']
        types = {k:type(v) for k, v in data[0].items()}
        change = {Decimal: 'f',
            dt.date: 'M'}

        new_types = {k: change[v] for k, v in types.items() if v in change.keys()}
        types.update(new_types)
        l = []
        for d in payload:
            df = pd.DataFrame.from_dict(d['Financials']).astype(types)
            df.insert(1, 'Symbol', d['Symbol'])
            l.append(df)
        df = pd.concat([frame for frame in l]).sort_values(['Symbol', 'Date'])

        return df.reset_index(drop=True).set_index(['Symbol', 'Date'])




    #def _generic_batch(self, type, **kwargs):
