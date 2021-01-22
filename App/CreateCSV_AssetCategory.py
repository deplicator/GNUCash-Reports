##
# @file
# Creates CSV file for Asset Category report, it's a little different than the generic reports.
#

import csv

## Create CSV - Asset Category
# @brief The intent of this report is to give the current value of assets per category (Stocks,
#        Bonds, Bullion, etc...). This will create a CSV file with rows for date range and columns
#        for category. The column headers are determined using GNUCash's security namespaces, so it
#        will require those to be set up in GNUCash.
class CreateCSV_AssetCategory():

    ## Constructor
    # @param[in]    GNUCashXML          **Object**, GNUCash XML parsed by ElementTree, needed to get
    #                                   list of security namespaces.
    # @param[in]    XMLnamespaces       **Object**, namespaces used in GNUCash XML, not to be
    #                                   confused swith ecurity namespaces.
    # @param[in]    assetBalanceReport  **List**, Asset Balance Report from ParseData.
    # @param[in]    options             **Object**, options from config file.
    # @param[in]    verbose             **Optonal Boolean**, prints status when true.
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

        # Call sumRowTotals for each date range.
        for report in self.reports:
            self.sumRowTotals(report)

        self.createFile()


    ## Parse categoeis from GNUCash XML.
    # @brief Creates a dictonary with categories from GNUCash's security namespaces as keys and
    #        float as values. A copy will be added for each row (date range).
    # @return                       **Dictonary** of categories to use as headers.
    def createHeaders(self):
        if (self.verbose):
            print("      Creating categoris from security namespaces.")

        categories = {}

        for commodity in self.GNUCashXML.findall(".//gnc:commodity", self.ns):
            category = commodity.find("./cmdty:space", self.ns).text

            if category not in categories:
                categories[category] = 0.0

        return categories


    ## Setup rows from end date.
    # @brief A row is made for each end date defined in the report (indexed as string with format
    #        "yyyy-mm-dd"). Each has a copy of the self.columns dictionary from createHeaders().
    # @return                       **Dictonary** of rows by date.
    def createRows(self):
        rows = {}

        for report in self.reports:
            date = report['endDate'].strftime("%Y-%m-%d")
            rows[date] = self.columns.copy()

        return rows


    ## Sums accounts by category for the give date.
    # @brief Adds the given account's total to the correct category. Recursively calls again if that
    #        account has children.
    # @param[in]    dateIndex           **String**, date to use as index format "yyyy-mm-dd".
    # @param[in]    account             **Object**, account to sum.
    def addAccountTotalsToCategory(self, dateIndex, account):
        category = account['commodity']['namespace']
        ammount  = account['total']

        self.rows[dateIndex][category] += ammount

        for child in account['children']:
            self.addAccountTotalsToCategory(dateIndex, account['children'][child])


    ## Sums accounts by category for single report (date range).
    # @brief Calls addAccountTotalsToCategory for each date range.
    # @param[in]    singleReport        **Object**, element of assetBalanceReport.
    def sumRowTotals(self, singleReport):
        # Converted to stirng so it looks nice in the CSV.
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
        with open(self.outputFile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(allRows)
