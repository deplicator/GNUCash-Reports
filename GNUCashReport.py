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

from App.ParseData               import ParseData
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

    # Do we want to see stuff in the terminal?
    verbose = options.verbose or config['OPTIONS'].getboolean('verbose')

    # Get the GNUCash XML file path.
    input = open(config['OPTIONS']['input'], 'r')

    # Asset Balance and Asset Investment report options.
    assetBalanceRunReport    = config['ASSET'].getboolean('balanceReport')
    assetCategoryRunReport   = config['ASSET'].getboolean('categoryReport')
    assetInvestmentRunReport = config['ASSET'].getboolean('investmentReport')
    assetBalanceOutput       = None if (not assetBalanceRunReport) else openOutputFile(config['ASSET']['balanceOutput'])
    assetCategoryOutput      = None if (not assetCategoryRunReport) else openOutputFile(config['ASSET']['categoryOutput'])
    assetInvestmentOutput    = None if (not assetInvestmentRunReport) else openOutputFile(config['ASSET']['investmentOutput'])
    assetAccounts            = list(filter(None, map(lambda account: account.strip(), config['ASSET']['accounts'].split(','))))
    assetDepth               = int(config['ASSET']['depth']) if (int(config['ASSET']['depth'])) else None
    assetDates               = list(filter(None, map(lambda date: date.strip(), config['ASSET']['dates'].split(','))))

    # Income Statement report options.
    incomeStatementRunReport  = config['INCOME STATEMENT'].getboolean('report')
    incomeStatementOutput     = None if (not incomeStatementRunReport) else openOutputFile(config['INCOME STATEMENT']['output'])
    incomeStatementAccounts   = list(filter(None, map(lambda account: account.strip(), config['INCOME STATEMENT']['accounts'].split(','))))
    incomeStatementDepth      = int(config['INCOME STATEMENT']['depth']) if (int(config['INCOME STATEMENT']['depth'])) else None
    incomeStatementDates      = list(filter(None, map(lambda date: date.strip(), config['INCOME STATEMENT']['dates'].split(','))))

    # Some quick and simple error checking.
    if (len(assetDates) %2 != 0):
        print("Unexpected number of dates in config file under [ASSET], they should be in pairs.")
        sys.exit()

    if (len(incomeStatementDates) %2 != 0):
        print("Unexpected number of dates in config file under [INCOME STATEMENT], they should be in pairs.")
        sys.exit()

    return SimpleNamespace(config          = options.config.name,
                           verbose         = verbose,
                           input           = input,
                           assetBalance    = SimpleNamespace(ReportType            = 'Asset Balance',
                                                             RunReport             = assetBalanceRunReport,
                                                             OutputFile            = assetBalanceOutput,
                                                             Accounts              = assetAccounts,
                                                             Depth                 = assetDepth,
                                                             Dates                 = assetDates),
                           assetCategory   = SimpleNamespace(ReportType            = 'Asset Category',
                                                             RunReport             = assetCategoryRunReport,
                                                             OutputFile            = assetCategoryOutput,
                                                             Accounts              = assetAccounts,
                                                             Depth                 = assetDepth,
                                                             Dates                 = assetDates),
                           assetInvestment = SimpleNamespace(ReportType            = 'Asset Investment',
                                                             RunReport             = assetInvestmentRunReport,
                                                             OutputFile            = assetInvestmentOutput,
                                                             Accounts              = assetAccounts,
                                                             Depth                 = assetDepth,
                                                             Dates                 = assetDates),
                           incomeStatement = SimpleNamespace(ReportType            = 'Income Statement',
                                                             RunReport             = incomeStatementRunReport,
                                                             OutputFile            = incomeStatementOutput,
                                                             Accounts              = incomeStatementAccounts,
                                                             Depth                 = incomeStatementDepth,
                                                             Dates                 = incomeStatementDates))


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

    GNUCashXML = getParsedXML(opts.input.name)  # GNUCash fils as XML object.
    namespaces = getNamespaces()                # Dictionary of XML namespaces used in GNUCash file.

    #
    # Run Asset Balance Report
    #
    AssetBalanceObj = None

    if (opts.assetBalance.RunReport):
        if (opts.verbose):
            print("== Running Asset Balance ==")

        AssetBalanceObj = ParseData(GNUCashXML, namespaces, opts.assetBalance, opts.verbose)

        if (opts.assetBalance.RunReport):
            CreateCSV(AssetBalanceObj, opts.assetBalance, opts.verbose)

    #
    # Run Asset Values by Type Report
    #
    AssetCategoryObj = None

    if (opts.assetCategory.RunReport):
        if (opts.verbose):
            print("== Running Asset Category ==")

        # Need asset balance to create asset category.
        if (None == AssetBalanceObj):
            AssetBalanceObj = ParseData(GNUCashXML, namespaces, opts.assetBalance, opts.verbose)

        CreateCSV_AssetCategory(GNUCashXML, namespaces, AssetBalanceObj, opts.assetCategory, opts.verbose)

    #
    # Run Asset Investment Report
    #
    AssetInvestmentObj = None

    if (opts.assetInvestment.RunReport):
        if (opts.verbose):
            print("== Running Asset Investment ==")

        AssetInvestmentObj = ParseData(GNUCashXML, namespaces, opts.assetInvestment, opts.verbose)

        CreateCSV(AssetInvestmentObj, opts.assetInvestment, opts.verbose)

    #
    # Run Income Statement Report
    #
    IncomeStatementObj = None

    if (opts.incomeStatement.RunReport):
        if (opts.verbose):
            print("== Running Income Statement ==")

        IncomeStatementObj = ParseData(GNUCashXML, namespaces, opts.incomeStatement, opts.verbose)

        CreateCSV(IncomeStatementObj, opts.incomeStatement, opts.verbose)
