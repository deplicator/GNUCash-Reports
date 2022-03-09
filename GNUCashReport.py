##
# @file
# Generates reports from GNUCash file.
#
import argparse
import configparser
import sys
import xml.etree.ElementTree as ET

from pathlib import Path
from types   import SimpleNamespace

from App.Options import Options

from App.ParseData_Balances import ParseData_Balance
from App.ParseData_Changes  import ParseData_Changes

from App.CreateCSV               import CreateCSV
from App.CreateCSV_AssetCategory import CreateCSV_AssetCategory # This report type is unique.


## Get command line arguments.
# @return                   Argparse object.
def getArguments():
    parser = argparse.ArgumentParser(description='Create simple reports from an uncompressed GNUCash file.')

    parser.add_argument('-c', '--config',
                        required = True,
                        metavar  = 'path_to_file',
                        type     = argparse.FileType('r'),
                        help     = 'Uncompressed GNUCash file, required file to configure report options.')

    parser.add_argument('-v', '--verbose',
                        dest     = 'verbose',
                        action   = 'store_true',
                        help     = 'Shows some terminal output while running.')

    # Update display flags.
    options = parser.parse_args()

    return options


## Open the files to write teh CSVs to.
# @brief Create path if it doesn't exist. These should get closed in the CreateCSV* class.
# @param[in]    filePath    String for file path.
# @return                   Object, file to use.
def openOutputFile(filePath):
    filePathList = filePath.split('/')                      # Convert to list, split on path delimeter.
    del filePathList[-1]                                    # Last element will be filename.
    filePathString = '/'.join(filePathList)                 # Create string of path without file.
    Path(filePathString).mkdir(parents=True, exist_ok=True) # Create directories.

    return filePath


## Get arguments from config file if -c option.
# @param[in]    options     Config file object from argparse.
# @return                   An object with options for each report.
def getConfigFile(options):

    print(options)

    # Build options from the config file
    config = configparser.ConfigParser()
    config.read(options.config.name)

    # GNUCash XML file path
    input = open(config['GENERAL']['input'], 'r')

    # Show output in terminal?
    verbose = options.verbose or config['GENERAL'].getboolean('verbose')

    # Which reports to run
    runAccountBalances  = config['GENERAL'].getboolean('accountBalances')
    runAccountChanges   = config['GENERAL'].getboolean('accountChanges')
    runAssetsByCategory = config['GENERAL'].getboolean('assetsByCategory')
    runIncomeStatement  = config['GENERAL'].getboolean('incomeStatment')

    # Where to save report CSVs
    accountBalancesOutput  = openOutputFile(config['GENERAL']['accountBalancesOutput'])  if (runAccountBalances)  else None
    accountChangesOutput   = openOutputFile(config['GENERAL']['accountChangesOutput'])   if (runAccountChanges)   else None
    assetsByCategoryOutput = openOutputFile(config['GENERAL']['assetsByCategoryOutput']) if (runAssetsByCategory) else None
    incomeStatementOutput  = openOutputFile(config['GENERAL']['incomeStatmentOutput'])   if (runIncomeStatement)  else None

    # Report dates, should be in pairs
    reportDates = list(filter(None, map(lambda date: date.strip(), config['GENERAL']['dates'].split(','))))
    if (len(reportDates) %2 != 0):
        print("Unexpected number of dates in config file, they should be in pairs.")
        sys.exit()

    # Balance report account paths
    assetAccounts = list(filter(None, map(lambda account: account.strip(), config['BALANCE REPORTS']['accounts'].split(',')[::2])))
    assetDepths   = list(filter(None, map(lambda account: account.strip(), config['BALANCE REPORTS']['accounts'].split(',')[1::2])))
    assetDepths   = [int(numeric_string) for numeric_string in assetDepths]

    # Income report account paths
    incomeAccounts   = list(filter(None, map(lambda account: account.strip(), config['INCOME REPORTS']['accounts'].split(',')[::2])))
    incomeDepth      = list(filter(None, map(lambda account: account.strip(), config['INCOME REPORTS']['accounts'].split(',')[1::2])))
    incomeDepth      = [int(numeric_string) for numeric_string in incomeDepth]

    return SimpleNamespace(config          = options.config,
                           input           = input,
                           verbose         = verbose,
                           accountBalances  = SimpleNamespace(ReportType = 'Account Balances',
                                                              RunReport  = runAccountBalances,
                                                              OutputFile = accountBalancesOutput,
                                                              Accounts   = assetAccounts,
                                                              Depth      = assetDepths,
                                                              Dates      = reportDates),
                           accountChanges   = SimpleNamespace(ReportType = 'Account Changes',
                                                              RunReport  = runAccountChanges,
                                                              OutputFile = accountChangesOutput,
                                                              Accounts   = assetAccounts,
                                                              Depth      = assetDepths,
                                                              Dates      = reportDates),
                           assetsByCategory = SimpleNamespace(ReportType = 'Assets by Category',
                                                              RunReport  = runAssetsByCategory,
                                                              OutputFile = assetsByCategoryOutput,
                                                              Accounts   = assetAccounts,
                                                              Depth      = assetDepths,
                                                              Dates      = reportDates),
                           incomeStatement  = SimpleNamespace(ReportType = 'Income Statement',
                                                              RunReport  = runIncomeStatement,
                                                              OutputFile = incomeStatementOutput,
                                                              Accounts   = incomeAccounts,
                                                              Depth      = incomeDepth,
                                                              Dates      = reportDates),
                           GNUCashXML = getParsedXML(input.name),
                           namespaces = getNamespaces() )


## Returns the GNUCash XML as an ElementTree object.
# @param[in]    filename    Name of uncompressed GNUCash xml file.
# @return                   ElementTree object.
def getParsedXML(filename):
    try:
        tree = ET.parse(filename)
    except ET.ParseError as err:
        print("ERROR: Unable to read GNUCash file. Is it saved as an uncompressed XML?")
        sys.exit()

    return tree.getroot()


## Return an object of namespaces.
# @return                   Dictonary suitable for use with ElementTree.
def getNamespaces():

    # Wasn't able to get element tree to return the root attributes. These shouldn't change often.
    return {
        'gnc'        : 'http://www.gnucash.org/XML/gnc',
        'act'        : 'http://www.gnucash.org/XML/act',
        'book'       : 'http://www.gnucash.org/XML/book',
        'cd'         : 'http://www.gnucash.org/XML/cd',
        'cmdty'      : 'http://www.gnucash.org/XML/cmdty',
        'price'      : 'http://www.gnucash.org/XML/price',
        'slot'       : 'http://www.gnucash.org/XML/slot',
        'split'      : 'http://www.gnucash.org/XML/split',
        'sx'         : 'http://www.gnucash.org/XML/sx',
        'trn'        : 'http://www.gnucash.org/XML/trn',
        'ts'         : 'http://www.gnucash.org/XML/ts',
        'fs'         : 'http://www.gnucash.org/XML/fs',
        'bgt'        : 'http://www.gnucash.org/XML/bgt',
        'recurrence' : 'http://www.gnucash.org/XML/recurrence',
        'lot'        : 'http://www.gnucash.org/XML/lot',
        'addr'       : 'http://www.gnucash.org/XML/addr',
        'billterm'   : 'http://www.gnucash.org/XML/billterm',
        'bt-days'    : 'http://www.gnucash.org/XML/bt-days',
        'bt-prox'    : 'http://www.gnucash.org/XML/bt-prox',
        'cust'       : 'http://www.gnucash.org/XML/cust',
        'employee'   : 'http://www.gnucash.org/XML/employee',
        'entry'      : 'http://www.gnucash.org/XML/entry',
        'invoice'    : 'http://www.gnucash.org/XML/invoice',
        'job'        : 'http://www.gnucash.org/XML/job',
        'order'      : 'http://www.gnucash.org/XML/order',
        'owner'      : 'http://www.gnucash.org/XML/owner',
        'taxtable'   : 'http://www.gnucash.org/XML/taxtable',
        'tte'        : 'http://www.gnucash.org/XML/tte',
        'vendor'     : 'http://www.gnucash.org/XML/vendor'
    }


# Start here.
if __name__ == '__main__':

    # Report options set by commonad line and/or config file.
    opts = getArguments()
    opts = getConfigFile(opts)
    Options.set(opts)   # Make these "global".

    # Obj contains GNUCash data from use beginnig of file to end date.
    BalanceObj = None
    if (opts.accountBalances.RunReport or opts.assetsByCategory.RunReport):
        BalanceObj = ParseData_Balance(opts.accountBalances.Accounts)

    # Create Account Balances report
    if (opts.accountBalances.RunReport):
        if (opts.verbose):
            print("\n== Running Account Balances ==")
        CreateCSV(BalanceObj, opts.accountBalances)

    # Create Account Changes report, uses begining and end date.
    if (opts.accountChanges.RunReport):
        if (opts.verbose):
            print("\n== Running Account Changes ==")
        CreateCSV(ParseData_Changes(), opts.accountChanges)

    # Create Assets by Category report
    if (opts.assetsByCategory.RunReport):
        if (opts.verbose):
            print("\n== Running Assets by Category ==")
        CreateCSV_AssetCategory(BalanceObj, opts.assetsByCategory)

    # Create Income Statement report
    if (opts.incomeStatement.RunReport):
        if (opts.verbose):
            print("\n== Running Income Statement ==")
        CreateCSV(ParseData_Balance(opts.incomeStatement.Accounts), opts.incomeStatement)
