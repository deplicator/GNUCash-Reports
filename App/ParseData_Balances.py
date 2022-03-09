##
# @file
# Holds Parse Data Balances class
#

from datetime import datetime, date

from App.Options                  import Options
from App.ParseData                import ParseData
from App.Common.AccountPaths      import AccountPaths
from App.Common.LimitTransactions import LimitTransactions


## Parse Data - Balances
# @brief Turns GNUCashXML and options object into a data structure.
class ParseData_Balance(ParseData):

    ## Constructor
    def __init__(self, accounts):

        if (Options.verbose):
            print("    Parsing Data")

        # Get a list of accounts to make report for.
        self.accountPaths = AccountPaths(accounts)

        # Build report object. List will be ordered by sets of start and end dates defined in the
        # config file.
        self.report = []

        for i in range(0, len(Options.accountBalances.Dates), 2):
            startDate   = datetime.strptime(Options.accountBalances.Dates[i], "%Y-%m-%d")
            endDate     = datetime.strptime(Options.accountBalances.Dates[i+1], "%Y-%m-%d")
            transctions = LimitTransactions(endDate)

            self.report.append({
                'startDate' : startDate,
                'endDate'   : endDate,
                'data'      : self.buildReport(transctions.get(), endDate)
            })
