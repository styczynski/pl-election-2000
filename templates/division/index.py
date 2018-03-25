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
        return list(data['voting']['divisions'].keys())

    def prepareData(self, data, fileName, fileIndex):
        data = self.globalGenerator.generateScopedData(data, None, fileName)

        voivodeshipName = data['voting']['divisions'][int(fileName)]['voivodeshipName']
        return self.globalGenerator.generateScopedData(data, voivodeshipName, fileName)