##
# @file
# Generates chosen reports from GNUCash file.
#
import argparse
import configparser
import sys
import xml.etree.ElementTree as ET

from pathlib import Path
from types   import SimpleNamespace

from App.Options import Options

from App.ParseData_AssetBalance    import ParseData_AssetBalance
from App.ParseData_AssetInvestment import ParseData_AssetInvestment
from App.ParseData_IncomeStatement import ParseData_IncomeStatement

from App.CreateCSV               import CreateCSV
from App.CreateCSV_AssetCategory import CreateCSV_AssetCategory # This report type is unique.


## Get command line arguments.
# @return                   Argparse object.
def getArguments():
    parser = argparse.ArgumentParser(description='Create simple asset balance reports from \
                                                  uncompressed GNUCash file.')

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
# @return                   An object similar to the argparse object build from configparser.
def getConfigFile(options):

    # Build the options from the config file.
    config = configparser.ConfigParser()
    config.read(options.config.name)

    # Get the GNUCash XML file path.
    input = open(config['OPTIONS']['input'], 'r')

    # Do we want to see stuff in the terminal?
    verbose = options.verbose or config['OPTIONS'].getboolean('verbose')

    # Asset Balance and Asset Investment report options.
    assetBalanceRunReport    = config['ASSET'].getboolean('balanceReport')
    assetCategoryRunReport   = config['ASSET'].getboolean('categoryReport')
    assetInvestmentRunReport = config['ASSET'].getboolean('investmentReport')
    assetBalanceOutput       = None if (not assetBalanceRunReport) else openOutputFile(config['ASSET']['balanceOutput'])
    assetCategoryOutput      = None if (not assetCategoryRunReport) else openOutputFile(config['ASSET']['categoryOutput'])
    assetInvestmentOutput    = None if (not assetInvestmentRunReport) else openOutputFile(config['ASSET']['investmentOutput'])
    assetAccounts            = list(filter(None, map(lambda account: account.strip(), config['ASSET']['accounts'].split(',')[::2])))
    assetDepths              = list(filter(None, map(lambda account: account.strip(), config['ASSET']['accounts'].split(',')[1::2])))
    assetDepths              = [int(numeric_string) for numeric_string in assetDepths]
    assetExcluded            = [] if not config.has_option('ASSET', 'excluded') else list(filter(None, map(lambda account: account.strip(), config['ASSET']['excluded'].split(','))))
    assetDates               = list(filter(None, map(lambda date: date.strip(), config['ASSET']['dates'].split(','))))

    # Income Statement report options.
    incomeStatementRunReport  = config['INCOME STATEMENT'].getboolean('report')
    incomeStatementOutput     = None if (not incomeStatementRunReport) else openOutputFile(config['INCOME STATEMENT']['output'])
    incomeStatementAccounts   = list(filter(None, map(lambda account: account.strip(), config['INCOME STATEMENT']['accounts'].split(',')[::2])))
    incomeStatementDepth      = list(filter(None, map(lambda account: account.strip(), config['INCOME STATEMENT']['accounts'].split(',')[1::2])))
    incomeStatementDepth      = [int(numeric_string) for numeric_string in assetDepths]
    incomeStatementDates      = list(filter(None, map(lambda date: date.strip(), config['INCOME STATEMENT']['dates'].split(','))))

    # Some quick and simple error checking.
    if (len(assetDates) %2 != 0):
        print("Unexpected number of dates in config file under [ASSET], they should be in pairs.")
        sys.exit()

    if (len(incomeStatementDates) %2 != 0):
        print("Unexpected number of dates in config file under [INCOME STATEMENT], they should be in pairs.")
        sys.exit()

    return SimpleNamespace(config          = options.config,
                           input           = input,
                           verbose         = verbose,
                           assetBalance    = SimpleNamespace(ReportType = 'Asset Balance',
                                                             RunReport  = assetBalanceRunReport,
                                                             OutputFile = assetBalanceOutput,
                                                             Accounts   = assetAccounts,
                                                             Depth      = assetDepths,
                                                             Excluded   = assetExcluded,
                                                             Dates      = assetDates),
                           assetCategory   = SimpleNamespace(ReportType = 'Asset Category',
                                                             RunReport  = assetCategoryRunReport,
                                                             OutputFile = assetCategoryOutput,
                                                             Accounts   = assetAccounts,
                                                             Depth      = assetDepths,
                                                             Excluded   = assetExcluded,
                                                             Dates      = assetDates),
                           assetInvestment = SimpleNamespace(ReportType = 'Asset Investment',
                                                             RunReport  = assetInvestmentRunReport,
                                                             OutputFile = assetInvestmentOutput,
                                                             Accounts   = assetAccounts,
                                                             Depth      = assetDepths,
                                                             Excluded   = assetExcluded,
                                                             Dates      = assetDates),
                           incomeStatement = SimpleNamespace(ReportType = 'Income Statement',
                                                             RunReport  = incomeStatementRunReport,
                                                             OutputFile = incomeStatementOutput,
                                                             Accounts   = incomeStatementAccounts,
                                                             Depth      = incomeStatementDepth,
                                                             Dates      = incomeStatementDates),
                           GNUCashXML = getParsedXML(input.name),
                           namespaces = getNamespaces()
                                                             )


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
    Options.set(opts)   # Make these things "global".

    #
    # Run Asset Balance Report - Asset balance by accounts defined in GNUCash.
    #
    AssetBalanceObj = None

    if (Options.assetBalance.RunReport):
        if (Options.verbose):
            print("\n== Running Asset Balance ==")

        AssetBalanceObj = ParseData_AssetBalance()

        CreateCSV(AssetBalanceObj, opts.assetBalance)

    #
    # Run Asset Values Report - Asset blances by security namespace defined in GNUCash.
    #
    AssetCategoryObj = None

    if (Options.assetCategory.RunReport):
        if (Options.verbose):
            print("\n== Running Asset Category ==")

        # Need asset balance data is used for both of these.
        if (None == AssetBalanceObj):
            AssetBalanceObj = ParseData_AssetBalance()

        CreateCSV_AssetCategory(AssetBalanceObj, opts.assetCategory)

    #
    # Run Asset Investment Report - Amount invested into accounts between dates.
    #
    AssetInvestmentObj = None

    if (Options.assetInvestment.RunReport):
        if (Options.verbose):
            print("\n== Running Asset Investment ==")

        AssetInvestmentObj = ParseData_AssetInvestment()

        CreateCSV(AssetInvestmentObj, opts.assetInvestment)

    #
    # Run Income Statement Report
    #
    IncomeStatementObj = None

    if (Options.incomeStatement.RunReport):
        if (Options.verbose):
            print("\n== Running Income Statement ==")

        IncomeStatementObj = ParseData_IncomeStatement()

        CreateCSV(IncomeStatementObj, opts.incomeStatement)
