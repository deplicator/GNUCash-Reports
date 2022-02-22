##
# @file
# Parse Data Asset Investment class
#

from datetime import datetime, date

from App.Options                  import Options
from App.ParseData                import ParseData
from App.Common.AccountPaths      import AccountPaths
from App.Common.LimitTransactions import LimitTransactions


## Parse Data - Asset Investment
# @brief Turns GNUCashXML and options object into a data structure.
class ParseData_AssetInvestment(ParseData):

    ## Constructor
    def __init__(self):

        if (Options.verbose):
            print("    Parsing Data")

        # Get a list of accounts to make report for.
        self.accountPaths = AccountPaths(Options.assetInvestment.Accounts)

        # Build report object. List will be ordered by sets of start and end dates defined in the
        # config file.
        self.report = []

        for i in range(0, len(Options.assetInvestment.Dates), 2):
            startDate   = datetime.strptime(Options.assetInvestment.Dates[i], "%Y-%m-%d")
            endDate     = datetime.strptime(Options.assetInvestment.Dates[i+1], "%Y-%m-%d")
            transctions = LimitTransactions(endDate, startDate)

            self.report.append({
                'startDate' : startDate,
                'endDate'   : endDate,
                'data'      : self.buildReport(transctions.get(), endDate)
            })


    ## Build the intial report data object.
    # @brief Populates the necessary elements of the top level results, recursively calls itself for
    #        children. Calculates everything except values, this is done in calculateTotals().
    # @param[in]    accountId       **String**, GUID of account to sum transactions for.
    # @param[in]    transctions     **List**, Transasctions for a set of dates in the report.
    # @param[in]    endDate         **DateTime Object**, used to getCommodityValue().
    # @param[in]    level           **Optional Integer**, current depth account is at realative to
    #                               accountId given.
    # @return                       **Dictonary**, report data with initial account information.
    def buildReportData(self, accountId, transctions, endDate, level = 0):

        accountEl = Options.GNUCashXML.find(".//gnc:account[act:id='{}']".format(accountId), Options.namespaces)
        children = {}

        # Recursive call on children for this account.
        for child in Options.GNUCashXML.findall(".//gnc:account[act:parent='{}']".format(accountId), Options.namespaces):
            childId = child.find('./act:id', Options.namespaces).text
            children[childId] = self.buildReportData(childId, transctions, endDate, level + 1)

        # Setup elements for this report data object.
        name            = accountEl.find('./act:name', Options.namespaces).text
        value, quantity = self.sumTransactionsForAccount(accountId, transctions) # value and quantity from gnucash xml

        # Don't care about commondity info for Asset Investments, we want what was actually paid
        # during the time period.

        # Add new object for each account in report.
        return {'name'      : name,                 # Human readable name.
                'level'     : level,                # Depth this account is relative to top.
                'children'  : children,             # Sub-Object for children.
                'commodity' : None,
                'quantity'  : quantity,             # How many commodities in account (1:1 if USD).
                'total'     : value,
                'totalAccount' : 0.0}               # This account value and its child values
