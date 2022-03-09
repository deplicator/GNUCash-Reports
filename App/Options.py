##
# @file
# Holds Options class.
#


## Options
# @brief Common data needed throughout the program. This class is not intended to be instantiated.
class Options:
    config          = None
    input           = None
    verbose         = False
    assetBalance    = None
    assetCategory   = None
    assetInvestment = None
    incomeStatement = None
    GNUCashXML      = None
    namespaces      = None


    @staticmethod
    def set(options):
        Options.config           = options.verbose
        Options.input            = options.input
        Options.verbose          = options.verbose
        Options.accountBalances  = options.accountBalances
        Options.accountChanges   = options.accountChanges
        Options.assetsByCategory = options.assetsByCategory
        Options.incomeStatement  = options.incomeStatement
        Options.GNUCashXML       = options.GNUCashXML
        Options.namespaces       = options.namespaces
