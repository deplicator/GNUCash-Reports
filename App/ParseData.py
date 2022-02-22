##
# @file
# Parses data from GNUCash XML object to be passed to CreateCSV class.
#

from datetime import datetime, date

from App.Options             import Options


## Parse Data
# @brief Base class for other ParseData* classes.
class ParseData():

    ## Constructor - must be implemented in subclass.
    def __init__(self):
        raise NotImplementedError


    ## Sums transactions value and quantity for given account id.
    # Uses subset of transaction limited by end date.
    # @param[in]    accountId       **String**, GUID of account to sum transactions for.
    # @param[in]    transctions     **List**, Transasctions to get the sum of.
    # @return                       **Tuple**; First element is sum of account's value, second for
    #                               quantity. Both floats.
    def sumTransactionsForAccount(self, accountId, transactions):

        # Return's to calculate.
        value    = 0
        quantity = 0

        # Loop through global transaction subset.
        for each in transactions:

            # Transasctions will have 2 or more splits.
            for split in each.findall('.//trn:split', Options.namespaces):

                account = split.find('./split:account', Options.namespaces).text

                if account == accountId:

                    # Convert value from text, split fraction, and accumulate.
                    splitValue = split.find('./split:value', Options.namespaces).text
                    splitValue = splitValue.split('/') # split fraction
                    value += (int(splitValue[0])) / (int(splitValue[1]))

                    # Convert value from text, split fraction, and accumulate.
                    splitQuatity = split.find('./split:quantity', Options.namespaces).text
                    splitQuatity = splitQuatity.split('/')
                    quantity += (int(splitQuatity[0])) / (int(splitQuatity[1]))

        return value, quantity


    ## Find commodity id for an account.
    # @param[in]    accountId       **String**, GUID of account to sum transactions for.
    # @return                       **String** of this account's commodity name.
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

        accountEl   = Options.GNUCashXML.find(".//gnc:account[act:id='{}']".format(accountId), Options.namespaces)
        commodityId = accountEl.find('./act:commodity/cmdty:id', Options.namespaces)

        return commodityId.text


    ## Find commodity's namespace and user defined symbol (what is displayed instead of $).
    # @param[in]    commodityId     **String**, GUID of commodity.
    # @return                       **Tuple** of Strings for this commodities namespace and symbol.
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

        commodityEl     = Options.GNUCashXML.find(".//gnc:commodity[cmdty:id='{}']".format(commodityId), Options.namespaces)
        commoditySlotsEl = commodityEl.find('./cmdty:slots/slot', Options.namespaces)

        if commodityEl:
            namespace = commodityEl.find('./cmdty:space', Options.namespaces).text

        # Not all commodities have slots
        if commoditySlotsEl:
            symbol = commoditySlotsEl.find('./slot:value', Options.namespaces).text

        return namespace, symbol


    ## Gets commodity value cloest to end date without going into the future.
    # @param[in]    commodityId     **String**, GUID of commodity.
    # @param[in]    endDate         **DateTime Object**, get the commodity price closest to this
    #                               date without going past it.
    # @return                       **Tuple** First element is commodity value as a float. Second is
    #                               the date of the commodity value as a datetime object.
    def getCommodityValue(self, commodityId, endDate):

        # Returns to calculate.
        commodityValue     = 0.0
        commodityValueDate = datetime.min

        # Don't bother if it's USD (an issue for GNUCash files setup to use otheer currencies).
        if (commodityId == 'USD'):
            commodityValue = 1.0
            return commodityValue, commodityValueDate

        for commodity in Options.GNUCashXML.findall(".//price:commodity[cmdty:id='{}']...".format(commodityId), Options.namespaces):

            dateString = commodity.find("./price:time/ts:date", Options.namespaces).text
            dateObject = datetime.strptime(dateString.split()[0], "%Y-%m-%d")

            # limit by dates
            if ((dateObject <= endDate) and (dateObject >= commodityValueDate)):
                commodityValue     = commodity.find("./price:value", Options.namespaces).text
                commodityValueDate = dateObject

        if (isinstance(commodityValue, str)):
            commodityValue = commodityValue.split('/')
            commodityValue = int(commodityValue[0]) / int(commodityValue[1])

        return commodityValue, commodityValueDate


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
        name                                = accountEl.find('./act:name', Options.namespaces).text
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
    # @brief Recursivly get sums from children accounts, when account has no child just copy sum to
    #        total.
    # @param[in]    reportData      **Dictonary** report data for children accounts.
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
    # @param[in]    transctions     **List**, Transasctions for a set of dates in the report.
    # @param[in]    endDate         **DateTime Object**, used to getCommodityValue().
    # @return                       **Dictonary** data for report.
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
