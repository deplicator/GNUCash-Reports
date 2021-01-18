##
# @file
# Creates CSV for Asset Category report, it's a little different than the generic reports.
#

import csv

## Create CSV - Asset Category
# @brief The intent of this report will give the current value of assets for Stocks, Bonds, Bullion,
#        etc... This will create a CSV file with rows for date range and columns for category. The
#        column headers are determined using GNUCash's security namespaces, so it will require those
#        to be set up correctly in GNUCash.
class CreateCSV_AssetCategory():

    ## Constructor for CreateCSV_AssetCategory Class.
    # @param[in]    GNUCashXML          Object, GNUCash XML parsed by ElementTree, needed to get
    #                                   list of security namespaces.
    # @param[in]    XMLnamespaces       Namespaces used in GNUCash XML, not to be confused with
    #                                   security namespaces.
    # @param[in]    assetBalanceReport  List, Asset Balance Report from ParseData.
    # @param[in]    options             Object, options from config file.
    # @param[in]    [verbose]           Boolean, prints status when true.
    def __init__(self, GNUCashXML, XMLnamespaces, assetBalanceReport, options, verbose = False):

        self.verbose = verbose

        if (self.verbose):
            print("    Creating Asset Category CSV")

        self.GNUCashXML = GNUCashXML
        self.ns         = XMLnamespaces
        self.reports    = assetBalanceReport.report
        self.outputFile = options.OutputFile
        self.depth      = options.Depth

        self.columns = self.createHeaders()
        self.rows    = self.createRows()

        for report in self.reports:
            self.sumRowTotals(report)

        self.createFile()


    ## Creates a dictonary with categories from GNUCash's security namespaces as keys and float as
    # values. A copy will be added for each row.
    def createHeaders(self):
        if (self.verbose):
            print("      Creating categoris from security namespaces.")

        categories = {}

        for commodity in self.GNUCashXML.findall(".//gnc:commodity", self.ns):
            category = commodity.find("./cmdty:space", self.ns).text

            if category not in categories:
                categories[category] = 0.0

        return categories


    ## A row is made for each end date defined in the report (indexed as string with format
    # "yyyy-mm-dd"). It will contain a copy of the self.columns dictionary from createHeaders.
    def createRows(self):
        rows = {}

        for report in self.reports:
            date = report['endDate'].strftime("%Y-%m-%d")
            rows[date] = self.columns.copy()

        return rows


    ## Adds an account's total to the correct category. Recursively calls again if that account has
    # children.
    def addAccountTotalsToCategory(self, dateIndex, account):
        category = account['commodity']['namespace']
        ammount  = account['total']

        self.rows[dateIndex][category] += ammount

        for child in account['children']:
            self.addAccountTotalsToCategory(dateIndex, account['children'][child])


    ## Sums accounts by category for a date.
    def sumRowTotals(self, singleReport):
        dateIndex = singleReport['endDate'].strftime("%Y-%m-%d")

        if (self.verbose):
            print("      Totaling for {}".format(dateIndex))

        for account in singleReport['data']:
            self.addAccountTotalsToCategory(dateIndex, singleReport['data'][account])


    ## Write date to CSV file.
    def createFile(self):
        if (self.verbose):
            print("      Making CSV.")

        allRows = []

        # Format headers
        headerRow = list(self.columns.keys()) # All the category dictionary have to be the same.
        headerRow.insert(0, None)             # Insert blank in front (lines up with date).
        allRows.append(headerRow)

        # Format rows
        for each in self.rows:
            totalRow = []
            totalRow.append(each) # Date is first.
            for value in self.rows[each]:
                formattedAmount = '${:,.2f}'.format(self.rows[each][value]) # Format to display like currency.
                totalRow.append(formattedAmount)
            allRows.append(totalRow)

        # Write it
        with open(self.outputFile.name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(allRows)
