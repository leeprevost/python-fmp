# Python FMP

A python class implementation leveraging the Finanicial Modeling Prep API [docs](https://financialmodelingprep.com/developer/docs/).

## Getting Started

Clone this repository.

import the class into your python app.

Examples:

	 from financialmodelingprep import FinancialModelingPrep

	 symbols = ["CRM", "HUBS", "ADBE", "MSFT"]
	 #instantiate class
	 fmp = FinancialModelingPrep(symbols)
	 
	 #get financial statments and convert to pandas Dataframe
	 inc_stmt = fmp.financial_statements(period="quarter")
	 bal_sht = fmp.financial_statements(period="quarter", type = 'bs')
	 cf_stmt = fmp.financial_statements(period = "quarter", type = 'cf')
	 
	 #get financial statement and return as python dictionary
	 inc_statmt_dic = fmp.financial_statements(period='quarter', ret_df = False)
	 
	 # other methods in class support Company Profile, Company Financial Statments (batch -- default is 3 at a time), 
	 # company financial ratios, company Enterprise Value, Company Key Metrics, Company Financial Growth, Company rating, 
	 # and others as documented on FinanicalModelingPrep API
	 

### Prerequisites

* pandas
* requests
* itertools
* re
* python 3 or later
```
```

### Installing

   1) Clone this repository to your machine
   2) import the class object as in example above.
```
```


### Future

This is currently based on FinancialModelingPrep API version 3.   The comapny is making some adjustments to their API which we hope will result in the following:

* Clean industry standard JSON.  Currently the API wraps all data in quotes including numeric data.  This requires some post processing to convert from strings to integer or float objects.

* Currently the batch prootocols put out a different nesting strucutre than the single symbols protocols which require post processing changes in order to convert to pandas dataframes.

* The maximum batch currently is 3 symbols per batch.  This wrapper is written to support a larger batch as that comes available.



```
```

## Updates
11/12/2019 - added partial support for version 3.1 API now in beta.   Still seeing some instability (server throtting errors).  Had to add a json ditionary normalizer to compensate for the differences in the returned formats between version 3 and 3.1 as well as batch vs. single stock endpoints.  Also, have tested the main financial_statements method fairly extensively.  Other methods are not used in my application and are not thoroughly tested.

## Contributing

Please reach out or make contributions.  This is a single person project currently.


## Authors

* **Lee Prevost** - 



## License

This project is licensed under the Apache License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Awesome requests module as well as pandas project.

