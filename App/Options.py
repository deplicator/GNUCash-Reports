


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
        Options.config          = options.verbose
        Options.input           = options.input
        Options.verbose         = options.verbose
        Options.assetBalance    = options.assetBalance
        Options.assetCategory   = options.assetCategory
        Options.assetInvestment = options.assetInvestment
        Options.incomeStatement = options.incomeStatement
        Options.GNUCashXML      = options.GNUCashXML
        Options.namespaces      = options.namespaces
