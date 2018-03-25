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
        return list(self.globalGenerator.voivodeshipsCodes.keys())

    def prepareData(self, data, fileName, fileIndex):
        return self.globalGenerator.generateScopedData(data, fileName)