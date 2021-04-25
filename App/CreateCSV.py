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
    # @param[in]    verbose         **Optional Boolean**, prints status when true.
    def __init__(self, reportObj, options):

        if (Options.verbose):
            print("    Creating {} CSV".format(options.ReportType))

        self.reports    = reportObj.report
        self.outputFile = options.OutputFile
        self.depth      = options.Depth

        self.createFile()


    ## Get header for single report.
    # @brief Headers can change based on date range. Reconsiling the headers will allow leave an
    #        account blank for a report when it didn't exist.
    # @param[in]    report          **Object**, Data from report.
    # @param[out]   headers         **Dictonary**, Headers to be created.
    def getReportHeader(self, report, headers):

        # Loop through each account in report.
        for account in report:

            if (report[account]['level'] <= self.depth):

                if (report[account]['level'] not in headers):
                    headers[report[account]['level']] = []
                    headers[report[account]['level']].append(report[account]['name'])
                else:
                    if (report[account]['name'] not in headers[report[account]['level']]):
                        headers[report[account]['level']].append(report[account]['name'])

                if (report[account]['children']):
                    self.getReportHeader(report[account]['children'], headers)


    ## Recursively sum total for single report
    # @param[in]    report          **Object**, Data from report.
    # @param[in]    headers         **Dictonary**, Headers to use.
    # @param[in]    row             **String**, index for row.
    def getTotals(self, report, headers, row):

        # Loop through each account in report.
        for account in report:
            accountdata = report[account]

            # No totals to update, just call on children.
            if (accountdata['level'] < self.depth):
                self.getTotals(accountdata['children'], headers, row)

            # This is the depth for building out this row.
            elif (accountdata['level'] == self.depth):

                # Make sure this name is in the header, and get where it is.
                index = headers.index(accountdata['name'])

                # This will leave None's where this account is not in this batch of reports.
                row[index] = accountdata['totalAccount']


    ## Creates CSV File.
    def createFile(self):

        #
        # Build headers.
        #
        headers = {}
        for report in self.reports:
            self.getReportHeader(report['data'], headers)

        # Number of headers at the depth for report.
        headerLen = len(headers[self.depth])

        # The header will have a dictonary entry for all headers found in all reports above the
        # display depth used. For now the sumary will only use the header at the display depth. It
        # will look something like this: [subaccount1, subaccount2, subaccount3] and completely
        # ignore parent accounts. The downside is it does not handle duplicates (which is possible
        # as long as their parents paths are unique).

        #
        # Build rows
        #
        rows = {}
        for report in self.reports:

            # Use date as string so it looks nice in CSV.
            dateIndex = report['endDate'].strftime("%Y-%m-%d")

            # Use report date as key for row.
            rows[dateIndex] = [None for i in range(headerLen)]

            # Fill in totals for this row.
            self.getTotals(report['data'],
                           headers[self.depth],
                           rows[dateIndex])

        #
        # Write it to a CSV.
        #
        allRows = []

        # Format header
        headerRow = headers[self.depth]
        headerRow.insert(0, None) # Insert blank in front (lines up with date).
        allRows.append(headerRow)

        # Format rows
        for each in rows:
            totalRow = []
            totalRow.append(each)
            for amount in rows[each]:
                formattedAmount = '${:,.2f}'.format(amount) # Format to display like currency.
                totalRow.append(formattedAmount)

            allRows.append(totalRow)

        # Write it
        with open(self.outputFile, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(allRows)
