import csv

## Summary
# Writes Asset Balance Reports to a CSV file.
class CreateCSV():

    ## Asset Balance Constructor
    # @param    reports         A list of reports to create summary of.
    # @param    outputFile      Where to put the results.
    # @param    displayOpts     Display options object.
    # @param    verbose         Print out some things if true.
    def __init__(self, reportObj, options, verbose):

        if (verbose):
            print("  Creating CSV")

        self.reports    = reportObj.report
        self.outputFile = options.OutputFile
        self.depth      = options.Depth

        self.createSummary()


    ## Get header for single report
    # Reports will usually have the same headers, but not always. Reconsiling the headers will allow
    # for leaving an account blank for a report where it didn't exist.
    # @param    report
    # @param    headers
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


    ##
    #
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


    ## Creates Summary of Asset Balance reports.
    def createSummary(self):

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

            # Use report date as key for row.
            rows[report['endDate']] = [None for i in range(headerLen)]

            # Fill in totals for this row.
            self.getTotals(report['data'],
                           headers[self.depth],
                           rows[report['endDate']])

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
        with open(self.outputFile.name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(allRows)
