'''
Wrapper for financialModelingPrep API

written: Lee Prevost, lee@prevost.net
dates: October, 2019
updated: November 2019 to support version 3.1 API (single batch)

@Todo:
    1) need to test single stock for version 3.1   - done
    2) Test other methods beyond main financialstatements method.
'''

import requests
import pandas as pd
import re
import datetime as dt
import json
from decimal import Decimal
import numpy as np
from itertools import zip_longest
import time

anndateformat = '%Y-%m'
quarterdateformat = '%Y-%m-%d'


class FinancialModelingPrep ():

    def __init__(self, symbols=[]):

        if symbols is not []:
            self.set_symbols(symbols)

        self.base_url = "https://financialmodelingprep.com/api/"
        self.versions = [3, 3.1]

    def set_symbols(self, symbols):

        if type(symbols) is str:
            symbols = [symbols]
        symbols = [symbol.upper() for symbol in symbols]

        self.symbols = symbols

    def _camelize_cols(self, col_list):
        new_cols=[]
        for col in col_list:
            l = col.split(" ")
            if len(l)>1:
                col = "".join([item.capitalize() for item in l])
            else: col = l[0]
            col = col[0].lower() + col[1:]
            new_cols.append(col)
        return new_cols


    def _get_payload(self, url, params, **kwargs):

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
            #d = {camelize(k): v for k, v in d.items()}
            return d

        params.update(kwargs)
        retries=1
        while retries < 3:
            print("getting: {}".format(url))
            r = requests.get(url, params)
            if "3.1" in url:
                jd= json.loads(r.text)
            else:
                jd= json.loads(r.text, object_hook=convert_types)
            if "error" not in jd.keys() and r.ok:
                break
            print("We have an error, retrying: {}".format(r.text))
            time.sleep(1*retries*retries)
            retries+=1
        return jd


    def _normalize_jd(self, jd, base_key):
        """ Make sure that all json has a list of dictionaries returned under financialStatementList"""
        if type(jd) is not dict:
            raise TypeError("Expecting a dictionary but got type: {}".format(type(jd)))

        if 'financialStatementList' in jd.keys():
            # case for batch in version 3
            return jd
        elif 'error' in jd.keys():
            # case for error in either versions
            raise ValueError("Error: {} from {}".format(jd['error'], self.url))
        elif 'symbol' in jd.keys() or "Symbol" in jd.keys():
            # case for single shot in ver 3.1
            #just make the return payload a list
            return {base_key: [jd]}

    def financial_statements(self, chunksize = 3, version=3, type = 'is', ret_df=True, **kwargs ):

        '''Returns an aggregated dataframe of financial statements

        parameters:
        chunksize: integer, default = 3.   Size of batch for each fetch.  Note: API version 3.1
            only supports batch size = 1 initially.
        version: integer, version of API for fmp.   Currently support 3 and 3.1 (beta)
        type: string, "bs", "cf" or "is".  Default is "is".
              'is' - income statement
              'cf' - cash flow statement
              'bs' - balance sheet statement
        ret_df: bool, default= True.  return dataframe (True) or json dictionary (False).
        period: string, "quarter" or "annual." Period for reporting data.
        **kwargs - other parameters for the web request (eg. format = "json")

        Added 11/2019 - added support for version 3.1 API.  Initially supports chunksize =1 only.

        Note:  Format of returned json date varies across API versions.   Here are examples:

             Version 3.1 (single) = json structure --
                  {
                      "symbol" : "T",
                      "financials" : [ {
                        "date" : "2018-12-31",
                        "revenue" : 170756000000,
                        "revenueGrowth" : 0.0636,
                        "costOfRevenue" : 79419000000,
                        "grossProfit" : 91337000000,  .......

              Version 3 (batch)
                   {
                      "financialStatementList" : [ {
                        "symbol" : "T",
                        "financials" : [ {
                          "date" : "2018-12-31",
                          "Revenue" : "170756000000.0",
                          "Revenue Growth" : "0.0636",
                          "Cost of Revenue" : "79419000000.0",
                          "Gross Profit" : "91337000000.0", ......

              This function leverages _normalize_jd to normalize data to a list of dictionies with "symbol" and "financials" as keys and with financial
              containing periodic data in a list of dictionaries..

        '''

        type_dict = {'is': 'financials/income-statement',
                    'bs': 'financials/balance-sheet-statement',
                    'cf': 'financials/cash-flow-statement'}

        if version not in self.versions:
            raise ValueError("Version = {} is unsupported".format(str(version)))
        if version == 3.1 and chunksize > 1:
            raise Warning("Initial version of api only supports 1 stock at a time or chunksize = 1")
        base_key = "financialStatementList"

        chunks = self._grouper(self.symbols, chunksize)
        self.params = params = kwargs

        l = []

        for chunk in chunks:
            chunk = [c for c in chunk if c is not None]
            symbollist = (",").join(chunk)
            url = "{0}v{1}/{2}/{3}".format(self.base_url, str(version), type_dict[type], symbollist)
            self.url = url
            print ("Getting chunk {}".format(url))
            print('Getting this symbollist:', symbollist)
            print('Getting this chunk:', chunk)
            print('getting this type', type_dict[type])
            d = self._get_payload(url, params)

            d = self._normalize_jd(d, base_key)
            l.extend(d[base_key])



        self._last_jd = {'source': 'financial_statement',
                    'base_key': base_key,
                    'payload': l}
        if ret_df:
            return self._return_agg_df()
        else:
            return self._last_jd

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
        jd = self._last_jd
        payload = jd['payload']  # should be list of dictionaries with "sybmol" and "financials" in keys.  financials is list of periodic data
        #ex_data = payload[0]['financials'][0]
        #types = {k: type(v) for k,v in ex_data.items()}
        #change = {Decimal: 'f',
        #    dt.date: 'M'}
        #new_types = {k: change[v] for k, v in types.items() if v in change.keys()}
        #types.update(new_types)
        l = []

        for d in payload:
            df = pd.DataFrame.from_dict(d['financials'])#.astype(types)
            df.columns = self._camelize_cols(df.columns)
            df.insert(1, 'symbol', d['symbol'])
            l.append(df)
        df = pd.concat([frame for frame in l]).sort_values(['symbol', 'date'])
        return df.set_index(['symbol', 'date'], drop = True)




    #def _generic_batch(self, type, **kwargs):

#for testing/debug
if __name__ == '__main__':
    test_cases = {'symbols1': ['MSFT', 'T'],
                  'symbols2': "CRM",
                  'symbols3': ['ORCL', 'T', 'HUBS'],
                  'symbols4': ['ORCL', 'T', 'HUBS', 'AVLR']
                  }

    fmp = FinancialModelingPrep()

    results ={}
    for k, v in test_cases.items():
        fmp.set_symbols(v)
        df1 = fmp.financial_statements()
        df2 = fmp.financial_statements(chunksize=1, version=3.1)
        df3 = fmp.financial_statements(chunksize=1, version = 3.1, period='quarter')
        results.update({k: [df1, df2, df3]})
