#
#  Piotr Styczyński @styczynski
#  March 2018 MIT LICENSE
#
#

class DataGenerator:

    def __init__(self, path, config, globalGenerator):
        self.path = path
        self.globalGenerator = globalGenerator

    def getFileNames(self):
        data = self.globalGenerator.generateScopedData()
        return list(data['voting']['communes'].keys())[:5]

    def prepareData(self, data, fileName, fileIndex):
        data = self.globalGenerator.generateScopedData(data, None, None, fileName)

        voivodeshipName = data['voting']['communes'][fileName]['voivodeshipName']
        votingDivisionNo = data['voting']['communes'][fileName]['votingDivisionNo']

        return self.globalGenerator.generateScopedData(data, voivodeshipName, votingDivisionNo, fileName)