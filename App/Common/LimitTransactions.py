##
# @file
# Holds LimitTransactions class.
#

from datetime import datetime, date

from App.Options import Options

## LimitTransactions
# @brief Create a list of transactions limited between dates.
class LimitTransactions():

    ## Constructor
    # @param[in]    endDate     **DateTime Object**, ending date for transaction window.
    # @param[in]    startDate   **Optional DateTime Object**, beginning date for transaction window.
    #                           If not given start will be from begining of file. This is useful for
    #                           calculating total value of an asset.
    def __init__(self, endDate, startDate = None):

        if (Options.verbose):
            if (None == startDate):
                print("      Limiting Transactions to {}".format(endDate.strftime("%#d %b %Y")))
            else:
                print("      Limiting Transactions between {} and {}"
                    .format(startDate.strftime("%#d %b %Y"), endDate.strftime("%#d %b %Y")))

        self.transactions = []

        # Go through all transactions in the XML.
        for transaction in Options.GNUCashXML.findall('.//gnc:transaction', Options.namespaces):

            # Find the transaction date.
            dateString = transaction.find('./trn:date-posted/ts:date', Options.namespaces).text
            dateObject = datetime.strptime(dateString.split()[0], "%Y-%m-%d")

            # Filter by start and end dates.
            if (None != startDate):
                if ((dateObject >= startDate) and (dateObject <= endDate)):
                    self.transactions.append(transaction)

            # Or just by an end date (including all transactions up to this point).
            else:
                if (dateObject <= endDate):
                    self.transactions.append(transaction)

    ## Returns list of transactions.
    # @return                   **List** of XML object transactions between given dates.
    def get(self):
        return self.transactions
