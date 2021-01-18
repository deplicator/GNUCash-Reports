##
# @file
# Parses data from GNUCash XML object to be passed to Create CSV.
#

from datetime import datetime, date

from App.AccountPaths import AccountPaths


## Parse Data
# Turns GNUCashXML and options object into a useable data structure.
class ParseData():

    ## Parse Data Constructor
    # @param    GNUCashXML  [object]    GNUCash XML parsed by ElementTree.
    # @param    namespaces  [object]    Namespaces used in GNUCash XML.
    # @param    options     [object]    Options from config file.
    # @param    verbose     [boolean]   Prints status when true.
    def __init__(self, GNUCashXML, namespaces, options, verbose):

        if (verbose):
            print("    Parsing Data")

        self.GNUCashXML = GNUCashXML
        self.ns         = namespaces
        self.accounts   = options.Accounts

        # A way to differentiate Asset Balance reports from the others. So far it's the only type
        # of report that limits transactions with only and end date.
        transactionWindow = True
        if options.ReportType == 'Asset Balance':
            transactionWindow = False

        # Get a list of accounts to make report for.
        self.accountPaths = AccountPaths(self.GNUCashXML, self.ns, self.accounts)

        # Build report object. List will be ordered by sets of start and end dates defined in the
        # config file.
        self.report = []

        for i in range(0, len(options.Dates), 2):
            startDate   = datetime.strptime(options.Dates[i], "%Y-%m-%d")
            endDate     = datetime.strptime(options.Dates[i+1], "%Y-%m-%d")
            transctions = self.limitTransactions(startDate, endDate, transactionWindow)

            self.report.append({
                'startDate'    : startDate,
                'endDate'      : endDate,
                'data'         : self.buildReport(transctions, endDate)
            })


    ## Create a list of transactions limited between dates.
    # @param    startDate       Beginning date for transaction window.
    # @param    endDate         Ending date for transaction window.
    # @param    window          Optional, if false the start date is ignored and the  transaction
    #                           window is from the beginning of the GNUCash file to the end date.
    # @return                   Returns the transctions as a list of xml objects.
    def limitTransactions(self, startDate, endDate, window = True):

        transactions = []

        # Go through all transactions in the XML.
        for transaction in self.GNUCashXML.findall('.//gnc:transaction', self.ns):

            # Find the transaction date.
            dateString = transaction.find('./trn:date-posted/ts:date', self.ns).text
            dateObject = datetime.strptime(dateString.split()[0], "%Y-%m-%d")

            # Filter by dates.
            # Asset Investment needs start and end date, it's interested in the balance change over
            # the period. Asset Balance and Income Statements only need end date, they need totals
            # for the accounts.
            if (window):
                if ((dateObject >= startDate) and (dateObject <= endDate)):
                    transactions.append(transaction)

            else:
                if (dateObject <= endDate):
                    transactions.append(transaction)

        return transactions


    ## Sums transactions value and quantity for given account id.
    # Uses subset of transaction limited by end date.
    # @param    accountId       GUID of account to sum transactions for.
    # @param    transctions     The list of limited transactions to get the sum of.
    # @return                   First for sum of account's value, second for quantity. Both floats.
    def sumTransactionsForAccount(self, accountId, transactions):

        # Return's to calculate.
        value    = 0
        quantity = 0

        # Loop through global transaction subset.
        for each in transactions:

            # Transasctions will have 2 or more splits.
            for split in each.findall('.//trn:split', self.ns):

                account = split.find('./split:account', self.ns).text

                if account == accountId:

                    # Convert value from text, split fraction, and accumulate.
                    splitValue = split.find('./split:value', self.ns).text
                    splitValue = splitValue.split('/') # split fraction
                    value += (int(splitValue[0])) / (int(splitValue[1]))

                    # Convert value from text, split fraction, and accumulate.
                    splitQuatity = split.find('./split:quantity', self.ns).text
                    splitQuatity = splitQuatity.split('/')
                    quantity += (int(splitQuatity[0])) / (int(splitQuatity[1]))

        return value, quantity


    ## Find commodity id for an account.
    # @param    accountId   [string]    GUID of account to get commodities of.
    # @return               [string]    This account's commodity name.
    def getCommodityId(self, accountId):
        # <gnc:account version="2.0.0">
        #     <act:name>FXNAX</act:name>
        #     <act:id type="guid">605101f68a79462eb06344feb4c85b5c</act:id>
        #     <act:type>STOCK</act:type>
        #     <act:commodity>
        #         <cmdty:space>MUTF</cmdty:space>
        #         <cmdty:id>FXNAX</cmdty:id>
        #     </act:commodity>
        #     <act:commodity-scu>10000</act:commodity-scu>
        #     <act:description>Fidelity U.S. Bond Index Fund</act:description>
        #     <act:parent type="guid">3af4bc34b6af4dda845cb156340c3b53</act:parent>
        # </gnc:account>

        accountEl   = self.GNUCashXML.find(".//gnc:account[act:id='{}']".format(accountId), self.ns)
        commodityId = accountEl.find('./act:commodity/cmdty:id', self.ns)

        return commodityId.text


    ## Find commodity's namespace and user defined symbol (what is displayed instead of $).
    # @param    commodityId     GUID of commodity.
    # @return                   Tuple of Strings for this commodities namespace and symbol.
    def getCommodityData(self, commodityId):
        # <gnc:commodity version="2.0.0">
        #     <cmdty:space>NYSE</cmdty:space>
        #     <cmdty:id>GPC</cmdty:id>
        #     <cmdty:name>Genuine Parts Company</cmdty:name>
        #     <cmdty:fraction>10000</cmdty:fraction>
        #     <cmdty:slots>
        #         <slot>
        #             <slot:key>user_symbol</slot:key>
        #             <slot:value type="string">GPC</slot:value>
        #         </slot>
        #     </cmdty:slots>
        # </gnc:commodity>

        namespace = None
        symbol    = None

        commodityEl     = self.GNUCashXML.find(".//gnc:commodity[cmdty:id='{}']".format(commodityId), self.ns)
        commoditySlotsEl = commodityEl.find('./cmdty:slots/slot', self.ns)

        if commodityEl:
            namespace = commodityEl.find('./cmdty:space', self.ns).text

        # Not all commodities have slots
        if commoditySlotsEl:
            symbol = commoditySlotsEl.find('./slot:value', self.ns).text

        return namespace, symbol


    ## Gets commodity value cloest to end date without going into the future.
    # @param    commodityId     GUID of commodity.
    # @param    endDate         The commodity price closest to this date without going past it.
    # @return                   Tuple of commodity value First, commodity value as a float. Second, the date of the commodity
    #                           value as a datetime object.
    def getCommodityValue(self, commodityId, endDate):

        # Returns to calculate.
        commodityValue     = 0.0
        commodityValueDate = datetime.min

        # Don't bother if it's USD (an issue for GNUCash files setup to use otheer currencies).
        if (commodityId == 'USD'):
            commodityValue = 1.0
            return commodityValue, commodityValueDate

        for commodity in self.GNUCashXML.findall(".//price:commodity[cmdty:id='{}']...".format(commodityId), self.ns):

            dateString = commodity.find("./price:time/ts:date", self.ns).text
            dateObject = datetime.strptime(dateString.split()[0], "%Y-%m-%d")

            # limit by dates
            if ((dateObject <= endDate) and (dateObject >= commodityValueDate)):
                commodityValue     = commodity.find("./price:value", self.ns).text
                commodityValueDate = dateObject

        if (isinstance(commodityValue, str)):
            commodityValue = commodityValue.split('/')
            commodityValue = int(commodityValue[0]) / int(commodityValue[1])

        return commodityValue, commodityValueDate


    ## Build the intial report data object.
    # Populates the necessary elements of the top level results, recursively calls itself for
    # children. Calculates everything except values.
    # @param    accountId       Account Id as a string of account to build report object for.
    # @param    transctions     The list of limited transactions for a set of dates in the report.
    # @param    endDate         The commodity price closest to this date without going past it.
    # @param    level           Optional, current depth account is at realative to accountId given.
    # @return                   Report data object with initial account information.
    def buildReportData(self, accountId, transctions, endDate, level = 0):

        accountEl = self.GNUCashXML.find(".//gnc:account[act:id='{}']".format(accountId), self.ns)
        children = {}

        # Recursive call on children for this account.
        for child in self.GNUCashXML.findall(".//gnc:account[act:parent='{}']".format(accountId), self.ns):
            childId = child.find('./act:id', self.ns).text
            children[childId] = self.buildReportData(childId, transctions, endDate, level + 1)

        # Setup elements for this report data object.
        name                                = accountEl.find('./act:name', self.ns).text
        value, quantity                     = self.sumTransactionsForAccount(accountId, transctions) # value and quantity from gnucash xml
        commodityId                         = self.getCommodityId(accountId)
        commodityNamespace, commoditySymbol = self.getCommodityData(commodityId)
        commodityValue, commodityValueDate  = self.getCommodityValue(commodityId, endDate)

        # Commodity information object.
        commodity = {'id'        : commodityId,         # What is this account made of?
                     'namespace' : commodityNamespace,  # Category for this commodity.
                     'symbol'    : commoditySymbol,     # Display symbol of commodity.
                     'value'     : commodityValue,      # Commodity value at commodityValueDate.
                     'date'      : commodityValueDate}  # Date used to determine commodity Value

        # Add new object for each account in report.
        return {'name'      : name,                 # Human readable name.
                'level'     : level,                # Depth this account is relative to top.
                'children'  : children,             # Sub-Object for children.
                'commodity' : commodity,            # Object describing this account's commodity.
                'quantity'  : quantity,             # How many commodities in account (1:1 if USD).
                'total'     : quantity * commodityValue,
                'totalAccount' : 0.0}               # This account value and its child values


    ## Total up sums of child accounts.
    # Recursivly get sums from children accounts, when account has no child just copy sum to total.
    # @param    reportData      needed to pass at this level so it can update totals.
    def calculateTotals(self, reportData):

        # Total up sums of children if it has children.
        if (reportData['children']):

            # Start with this accounts sum.
            tempTotal = reportData['total']

            # Get total from children.
            for child in reportData['children']:

                # If this child has children of its own, do this at that level first.
                self.calculateTotals(reportData['children'][child])

                # Add this child's tottal to running total.
                tempTotal += reportData['children'][child]['totalAccount']

            # After getting all the childrens totals assign this value back to this total.
            reportData['totalAccount'] = tempTotal

        # This has no children, just assign value to totalAccountValue.
        else:
            reportData['totalAccount'] = reportData['total']


    ## Build out the report object.
    # @param    transctions     The list of limited transactions for a set of dates in the report.
    # @param    endDate         The commodity price closest to this date without going past it.
    # @return                   Report data object.
    def buildReport(self, transctions, endDate):

        row = {}

        # Create reports for all accounts passed in, add them to Results.
        for account in self.accountPaths.pathsByGUID:
            reportLevelGUID      = account[-1]
            row[reportLevelGUID] = self.buildReportData(reportLevelGUID, transctions, endDate)

        # Calculate the totals for all accounts.
        for each in row:

            # Children
            if row[each]['children']:
                self.calculateTotals(row[each])

            # No children, just assign totalAccountValue to value.
            else:
                row[each]['totalAccount'] = row[each]['total']

        return row
