# GNUCash Reports

## Purpose
GNUCash does a decent job giving reports for a specified date range, but not so great at generating
reports for several date ranges. It can also be difficult to move those reports to a spreadsheet to
make pretty charts.

This has only been tested with files made by GNUCash 3.10.

A [short blog](http://geekwagon.net/index.php/2021/multiple-gnucash-reports/) post about this project.

## Use
This will run the report using the options defined in the example_config.ini. The config file will
define which uncompressed XML *.gnucash file to use, the types of reports to run, date ranges for
the reports, and where to save output CSV files. See example_config.ini for details.

    python GNUCashReport.py -c example_config.ini


## Output
The example will put the scripts output in a directory named output. There will be a CSV file
created for each report type. The rows in the CSVs are for each date range specified in the config
file.

Here is an [example of what can be done in Google Spreadsheets](https://docs.google.com/spreadsheets/d/1jA7ocKEdnhieeoL5E42myhpOdEFeFzZzqeruaxXmLdY) from the CSV output.



## Report Types

### Asset Balance
The balance of all accounts defined for this report. The value is derived from the closest security prices available.

### Asset Category
The current value of assets broken down by category. The category is derived from security
namespaces.

### Asset Investment
The amount that has been invested into the accounts in the given date range.

### Income Statement
This is the same as GNUCash's Income Statement report, but it gives multiple date ranges.


## Documentation
To generate documentation run,

    doxygen Doxyfile


## Future
The obvious feature to add is to use the Google Sheets API to make the spreadsheets. This first step
is much easier than manually running reports in GNUCash and hand copying the results. Her is a short
list of what needs updating or fixing.

 * Better verbose output, particularly something that shows what dates the ParseData is working on.
   Also, flush stdout so the print out doesn't come all at once at the end.
 * CreateCSV - getCommodityValue method uses closest commodity value date without going into the
   future. Should use closest date.
 * CreateCSV - May have issues with duplicate header names. This is possible because it's only
   putting values in for the given account depth, but those values can have the same name albeit
   with different paths.
 * Demo GNUCash file needs better example for income and expense report.
