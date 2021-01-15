##
# @file
# Generates Asset Balance Report from GNUCash file.
#
import argparse
import configparser
import sys
import xml.etree.ElementTree as ET

from types import SimpleNamespace

from App.ParseData import ParseData
from App.CreateCSV import CreateCSV


## Get command line arguments.
# @return   Argparse object.
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


## Get arguments from config file if -c option.
# @param    configFile  Config file object from argparse.
# @return               An object similar to the argparse object build from configparser.
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
    assetInvestmentRunReport = config['ASSET'].getboolean('investmentReport')
    assetBalanceOutput       = None if (not assetBalanceRunReport) else open(config['ASSET']['balanceOutput'], 'w')
    assetInvestmentOutput    = None if (not assetInvestmentRunReport) else open(config['ASSET']['investmentOutput'], 'w')
    assetAccounts            = list(filter(None, map(lambda account: account.strip(), config['ASSET']['accounts'].split(','))))
    assetDepth               = int(config['ASSET']['depth']) if (int(config['ASSET']['depth'])) else None
    assetEndDates            = list(filter(None, map(lambda date: date.strip(), config['ASSET']['dates'].split(','))))

    # Income Statement report options.
    incomeStatementRunReport  = config['INCOME STATEMENT'].getboolean('report')
    incomeStatementOutput     = None if (not incomeStatementRunReport) else open(config['INCOME STATEMENT']['output'], 'w')
    incomeStatementAccounts   = list(filter(None, map(lambda account: account.strip(), config['INCOME STATEMENT']['accounts'].split(','))))
    incomeStatementDepth      = int(config['INCOME STATEMENT']['depth']) if (int(config['INCOME STATEMENT']['depth'])) else None
    incomeStatementDates      = list(filter(None, map(lambda date: date.strip(), config['INCOME STATEMENT']['dates'].split(','))))

    # Some quick and simple error checking.
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
                                                             Dates                 = assetEndDates),
                           assetInvestment = SimpleNamespace(ReportType            = 'Asset Investment',
                                                             RunReport             = assetInvestmentRunReport,
                                                             OutputFile            = assetInvestmentOutput,
                                                             Accounts              = assetAccounts,
                                                             Depth                 = assetDepth,
                                                             Dates                 = assetEndDates),
                           incomeStatement = SimpleNamespace(ReportType            = 'Income Statement',
                                                             RunReport             = incomeStatementRunReport,
                                                             OutputFile            = incomeStatementOutput,
                                                             Accounts              = incomeStatementAccounts,
                                                             Depth                 = incomeStatementDepth,
                                                             Dates                 = incomeStatementDates))


## Returns the GNUCash XML as an ElementTree object.
# @param    filename    Name of uncompressed GNUCash xml file.
# @return               ElementTree object.
def getParsedXML(filename):
    tree = ET.parse(filename)
    return tree.getroot()


## Return an object of namespaces.
# @return               Dictonary suitable for use with ElementTree.
def getNamespaces():

    # I was unable to get element tree to give the root attributes. Not sure why but these shouldn't
    # change often.
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

    # Report options set by config file.
    opts = getArguments()
    opts = getConfigFile(opts)

    GNUCashXML = getParsedXML(opts.input.name)  # GNUCash fils as XML object.
    namespaces = getNamespaces()                # Dictionary of XML namespaces used in GNUCash file.

    #
    # Run Asset Balance Report
    #
    if (opts.assetBalance.RunReport):
        if (opts.verbose):
            print("Running Asset Balance")
        AssetBalanceObj = ParseData(GNUCashXML, namespaces, opts.assetBalance, opts.verbose)
        CreateCSV(AssetBalanceObj, opts.assetBalance, opts.verbose)

    #
    # Run Asset Investment Report
    #
    if (opts.assetInvestment.RunReport):
        if (opts.verbose):
            print("Running Asset Investment")
        AssetBalanceObj = ParseData(GNUCashXML, namespaces, opts.assetInvestment, opts.verbose)
        CreateCSV(AssetBalanceObj, opts.assetInvestment, opts.verbose)

    #
    # Run Income Statement Report
    #
    if (opts.incomeStatement.RunReport):
        if (opts.verbose):
            print("Running Income Statement")
        incomeStatementObj = ParseData(GNUCashXML, namespaces, opts.incomeStatement, opts.verbose)
        CreateCSV(incomeStatementObj, opts.incomeStatement, opts.verbose)
