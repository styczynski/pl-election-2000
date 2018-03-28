# 
# Remastered voting site
# https://github.com/styczynski/pl-election-2000
#
# Piotr Styczyński @styczynski
# MIT License
#

"""
    Commune data generator.

    Piotr Styczyński @styczynski
    MIT License
"""
class DataGenerator:

    def __init__(self, path, config, globalGenerator):
        """
            Create new generator for given path, config and top-level generator.
            The top-level gen. will be captured to have access to the data-generating functions.
            (defined in index.py)
        """
        self.path = path
        self.globalGenerator = globalGenerator

    def getFileNames(self):
        """
            Generate page for each voivodeship.
        """
        data = self.globalGenerator.generateScopedData()
        return list(data['voting']['communes'].keys())

    def prepareData(self, data, fileName, fileIndex):
        """
            Generate data for template using provided top-level generator instance.
        """
        # This is used only to retrieve voivodeship name
        # for the generated commune subpage
        data = self.globalGenerator.generateScopedData(data, None, None, fileName)

        voivodeshipName = data['voting']['communes'][fileName]['voivodeshipName']
        votingDivisionNo = data['voting']['communes'][fileName]['votingDivisionNo']

        return self.globalGenerator.generateScopedData(data, voivodeshipName, votingDivisionNo, fileName)
