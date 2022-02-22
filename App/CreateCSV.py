##
# @file
# Creates CSV file for generic reports.
#

import csv

from App.Options import Options


## Create CSV
# @brief Creates a CSV report from a ParseData object.
class CreateCSV():

    ## Constructor
    # @param[in]    reportObj       **List**, output from ParseData class, reports to create the CSV for.
    # @param[in]    options         **Object**, options from config file.
    def __init__(self, reportObj, options):

        if (Options.verbose):
            print("    Creating {} CSV".format(options.ReportType))

        self.reports    = reportObj.report
        self.outputFile = options.OutputFile
        self.depth      = options.Depth

        self.createFile()


    # Get number of children for current account at a certain depth.
    # @param[in]    account         **Object**, An account from a report.
    # @param[in]    depth           **Integer**, Depth to count children at
    def countChildrenToDepth(self, account, depth):
        if (account['level'] == depth):
            return 1

        subcount = 0
        if (account['level'] < depth):
            for child in account['children']:
                subcount += self.countChildrenToDepth(account['children'][child], depth)
            return subcount


    ## Make headers for report.
    # @brief
    # @param[in]    account         **Object**, An account from a report, first call is the top level account.
    # @param[in]    depth           **Integer**, Depth for this report.
    # @param[out]   headers         **Dictonary**, Represents headers to be created.
    def makeHeaders(self, account, depth, headers):

        # Ignore children called below this depth.
        if (account['level'] <= depth):

            # New row
            if (account['level'] not in headers):
                headers[account['level']] = []

            # New account
            if (account['name'] not in headers[account['level']]):
                headers[account['level']].append(account['name'])

                # Add column and space for children if needed.
                colWidth = self.countChildrenToDepth(account, depth) - 1;
                for i in range(0, colWidth):
                    headers[account['level']].append(None)

            # Call again if this account has children.
            if (account['children']):
                for child in account['children']:
                    self.makeHeaders(account['children'][child], depth, headers)


    ## Recursively sum total for single report
    # @param[in]    account         **Object**, an account, first call is a top level account.
    # @param[in]    headers         **Dictonary**, Headers to use.
    # @param[in]    row             **String**, index for row.
    def getTotals(self, account, headers, row, depth):

        # No totals to update, just call on children.
        if (account['level'] < depth):
            for child in account['children']:
                self.getTotals(account['children'][child], headers, row, depth)

        # This is the depth for building out this row.
        elif (account['level'] == depth):

            # Make sure this name is in the header, and get where it is.
            index = headers.index(account['name'])

            # This will leave None's where this account is not in this batch of reports.
            formattedAmount = '${:,.2f}'.format(account['totalAccount'])
            row[index] = formattedAmount


    ## Creates CSV File.
    def createFile(self):

        #
        # Build headers.
        #
        headers = {}
        for report in self.reports: # break report up by dates
            for index, topLevelAccounts in enumerate(report['data']): # break report up by top level accounts
                self.makeHeaders(report['data'][topLevelAccounts], self.depth[index], headers)

        # Add empty column before each header row for date.
        for each in headers:
            headers[each].insert(0, None)

        #
        # Build rows
        #
        rows = {}
        for report in self.reports:
            # Use date as string so it looks nice in CSV.
            dateIndex = report['endDate'].strftime("%Y-%m-%d")

            # Use report date as key for row, create row with max length of header.
            rows[dateIndex] = [None] * (len(headers[max(headers, key=headers.get)]) - 1)
            rows[dateIndex].insert(0, dateIndex)

            # Loop through topLevelAccounts
            for index, topLevelAccounts in enumerate(report['data']):

                # Fill in totals for this row.
                self.getTotals(report['data'][topLevelAccounts],
                               headers[self.depth[index]], # pass in the header for these topLevelAccounts
                               rows[dateIndex],
                               self.depth[index])

# {0:                    [None, 'Assets', None, None, None, None, None, 'Liabilities'],
#  1:                    [None, 'Investments',               None,     'Bank', 'Speculative Investments',             None,     None,        'Credit Card'],
#  2:                    [None,    'Fidelity',         'Vanguard', 'Checking',                 'Bitcoin',         'Silver',    'Gold']}
# {'2020-09-30': ['2020-09-30',       2523.96,        2581.175315,    2285.82,                 1557.6522,       767.437209,      0.0,             -758.33, None],
#  '2021-10-31': ['2021-10-31',  10202.040042, 10514.049847999999,    10087.2,        13100.581000000002, 845.5634100000001, 1893.66, -21.020000000000003, None]}

        #
        # Write it to a CSV.
        #
        allRows = []

        for header in headers:
            allRows.append(headers[header])

        for row in rows:
            allRows.append(rows[row])

        # Write it
        with open(self.outputFile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(allRows)
