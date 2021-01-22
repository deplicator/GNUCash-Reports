##
# @file
# AccountPaths class.
#


## Account Paths
# @brief Creates an obeject of verified account paths at .pathsByGUID from the list of account paths
#        strings passed in. Only tested with default GNUCash path seperatros.
class AccountPaths():

    ## Constructor
    # @param[in]    GNUCashXML      **Object**, GNUCash XML parsed by ElementTree.
    # @param[in]    namespaces      **Object**, namespaces used in GNUCash XML.
    # @param[in]    accounts        **List** of strings representing GNUCash account paths.
    def __init__(self, GNUCashXML, namespaces, accounts):
        self.GNUCashXML   = GNUCashXML
        self.ns           = namespaces
        self.accounts     = accounts

        self.verified    = False                # Set to true when paths are good.
        self.pathsByGUID = self.verifyPaths()


    ## Verifies a single path string.
    # @brief Expects path as string with account names seperated by colon.
    #        Example "Assets:Current Assets:Savings"
    # @param[in]    path            **String** of account names.
    # @return                       **List** of account GUIDs as a string for each account in path,
    #                               in element order for given path.
    def verifyPath(self, path):

        # List of GUID's to return if all account names are found with correct parent/child relations.
        listOfGUIDs = []

        # Keep count of accounts found to verify the accounts found and length of path is the same.
        accountsFound = 0

        # Path's always start with the top level account in GNUCash (not shown in GNUCash, hopefully
        # always named Root Account).
        rootElem = self.GNUCashXML.find(".//gnc:account[act:name='Root Account']", self.ns)
        rootGUID = rootElem.find('act:id', self.ns).text

        # Id that will be used to verify this is a child of parent.
        previousGUID = rootGUID

        # Root GUID is always the first account in list.
        listOfGUIDs.append(rootGUID)

        # Split account paths into account names.
        accountPath = path.split(':')

        # Loop through account path given.
        for accountName in accountPath:

            # Find accounts by parentId
            for account in self.GNUCashXML.findall(".//gnc:account[act:parent='{}']".format(previousGUID), self.ns):

                name     = account.find('./act:name', self.ns).text
                parentId = account.find('./act:parent', self.ns).text

                # But is this the account we're looking for?
                if accountName == name:

                    # Append this GUID to list.
                    listOfGUIDs.append(account.find('./act:id', self.ns).text)

                    # Update previous for next go around.
                    previousGUID  = account.find('./act:id', self.ns).text

                    # Account was found with this name, increment counter.
                    accountsFound += 1

                    # Move on to next account name in this path.
                    break

        # Verify this path makes sense.
        if accountsFound == len(accountPath):
            return listOfGUIDs

        else:
            return None


    ## Verifies a all path strings passed to class.
    # @return                       **List** of verified paths.
    def verifyPaths(self):

        # Paths to return.
        accountPathGUIDs = []

        # Check each path passed into class.
        for accountPath in self.accounts:
            pathGUIDs = self.verifyPath(accountPath)
            accountPathGUIDs.append(pathGUIDs)

        if None not in accountPathGUIDs:
            self.verified = True
        else:
            print("Account path could not be verified.")

        return accountPathGUIDs
