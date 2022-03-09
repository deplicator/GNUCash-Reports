# GNUCash Reports

## Purpose
GNUCash can create reports for a specified date range, but not for a set of date
ranges. This will generate a csv file for different reports, each row is a date
range. Suitable for [pasting into a spreadsheet to make
charts](https://docs.google.com/spreadsheets/d/1jA7ocKEdnhieeoL5E42myhpOdEFeFzZzqeruaxXmLdY).


This has only been tested with files made by GNUCash 3.10.

A [short blog](http://geekwagon.net/index.php/2021/multiple-gnucash-reports/)
post about this project.

## Use
This will run the report using the options defined in the `example_config.ini`.

    python GNUCashReport.py -c example_config.ini

The config file defines which uncompressed XML gnucash file to use, the types of
reports to run, date ranges for the reports, and where to save output CSV files.
See `example_config.ini` for details.

## Report Types
There are four reports divided in two categories, balance and Income. **Balance
Reports** are intended to be used with Asset and Liability Account Types defined
by GNUCash. These will use account paths under `[BALANCE REPORTS]` in the config
file. **Income Reports** are intended to be used with Income and Expense Account
Types. These will use accounts under `[INCOME REPORTS]`.

### Balance Reports

#### Account Balances
The balance of accounts at the end dates specifed in the config. The value is
derived from the closest security prices available.

#### Account Changes
The amount the account has change for each date range.

#### Assets by Category
The current value of assets broken down by category. The category is derived
from security namespaces.

### Income Reports

#### Income Statement
This is the same as GNUCash's Income Statement report, but for multiple date
ranges.
