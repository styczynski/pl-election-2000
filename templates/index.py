import json
import csv
import copy

class DataGenerator:

    voivodeshipsCodes = {
        "DOLNOŚLĄSKIE": 'PL-DS',
        "KUJAWSKO-POMORSKIE": 'PL-KP',
        "LUBELSKIE": 'PL-LU',
        "LUBUSKIE": 'PL-LB',
        "ŁÓDZKIE": 'PL-LD',
        "MAŁOPOLSKIE": 'PL-MA',
        "MAZOWIECKIE": 'PL-MZ',
        "OPOLSKIE": 'PL-OP',
        "PODKARPACKIE": 'PL-PK',
        "PODLASKIE": 'PL-PD',
        "POMORSKIE": 'PL-PM',
        "ŚLĄSKIE": 'PL-SL',
        "ŚWIĘTOKRZYSKIE": 'PL-SK',
        "WARMIŃSKO-MAZURSKIE": 'PL-WN',
        "WIELKOPOLSKIE": 'PL-WP',
        "ZACHODNIOPOMORSKIE": 'PL-ZP'
    }

    def __init__(self, path, config):
        self.path = path
        self.cache = None
        self.config = config

    def aggregateVotingStats(self, dataReader=None, aggregators=[], resolution=None, postParsers=[]):

        if dataReader is None:
            return {}

        totalsDetails = {}

        dataHead = next(dataReader)

        if resolution == 'search':
            searchStats = {
                'voivodeships': {},
                'divisions': {},
                'communes': {}
            }
            for row in dataReader:
                voivodeShipName = row[0]
                votingDivisionNo = int(row[1])
                votingCommuneName = row[3]

                searchStats['voivodeships'][voivodeShipName] = voivodeShipName
                searchStats['divisions'][votingDivisionNo] = votingDivisionNo
                searchStats['communes'][votingCommuneName] = votingCommuneName
            return searchStats

        for row in dataReader:
            voivodeShipName = row[0]
            votingDivisionNo = int(row[1])
            votingCommuneName = row[3]

            tgtObj = totalsDetails

            if resolution is None:
                tgtObj = totalsDetails
            elif resolution == 'voivodeship':
                if not voivodeShipName in totalsDetails:
                    totalsDetails[voivodeShipName] = {
                        'name': voivodeShipName,
                        'divisions': {}
                    }
                totalsDetails[voivodeShipName]['divisions'][votingDivisionNo] = True
                tgtObj = totalsDetails[voivodeShipName]
            elif resolution == 'division':
                if not votingDivisionNo in totalsDetails:
                    totalsDetails[votingDivisionNo] = {
                        'votingDivisionNo': votingDivisionNo,
                        'voivodeshipName': voivodeShipName,
                        'communes': {}
                    }
                totalsDetails[votingDivisionNo]['communes'][votingCommuneName] = True
                tgtObj = totalsDetails[votingDivisionNo]

            elif resolution == 'commune':
                if not votingCommuneName in totalsDetails:
                    totalsDetails[votingCommuneName] = {
                        'votingDivisionNo': votingDivisionNo,
                        'voivodeshipName': voivodeShipName,
                        'votingCommuneName': votingCommuneName
                    }
                tgtObj = totalsDetails[votingCommuneName]

            for aggregator in aggregators:
                aggregator(tgtObj, row, dataHead)

        for postParser in postParsers:
            if resolution is None:
                postParser(totalsDetails)
            elif resolution == 'voivodeship':
                for voivodeShipName, voivodeShipData in totalsDetails.items():
                    postParser(voivodeShipData)
            elif resolution == 'division':
                 for votingDivisionNo, votingDivisionData in totalsDetails.items():
                    postParser(votingDivisionData)
            elif resolution == 'commune':
                for votingCommuneName, votingCommuneData in totalsDetails.items():
                    postParser(votingCommuneData)

        return totalsDetails


    def generateVotingData(self, resolution=None):

        def formatIntegerNumber(num):
            return format(num, '6,d')

        def formatPercents(num):
            return f'{format(num, ".2f")}%'

        def voivodeshipCodeAgregator(results, row, header):
            results['voivodeshipCode'] = self.voivodeshipsCodes[row[0]]

        def allowedVotesAgregator(results, row, header):
            results['allowed'] = results.get('allowed', 0) + int(row[6])
            results['allowedStr'] = formatIntegerNumber(results['allowed'])

        def cardsReleasedAgregator(results, row, header):
            results['cardsReleased'] = results.get('cardsReleased', 0) + int(row[7])
            results['cardsReleasedStr'] = formatIntegerNumber(results['cardsReleased'])

        def cardsCollectedAgregator(results, row, header):
            results['cardsCollected'] = results.get('cardsCollected', 0) + int(row[8])
            results['cardsCollectedStr'] = formatIntegerNumber(results['cardsCollected'])

        def votesValidAgregator(results, row, header):
            results['votesValid'] = results.get('votesValid', 0) + int(row[10])
            results['votesValidStr'] = formatIntegerNumber(results['votesValid'])

        def votesInvalidAgregator(results, row, header):
            results['votesInvalid'] = results.get('votesInvalid', 0) + int(row[9])
            results['votesInvalidStr'] = formatIntegerNumber(results['votesInvalid'])

        def candidateVotesAgregator(results, row, header):
            results['candidates'] = results.get('candidates', {})
            results['totalVotes'] = results.get('totalVotes', 0)

            candidateNames = header[11:]
            candidateRowIndex = 11
            for candidate in candidateNames:
                votes = int(row[candidateRowIndex])
                results['candidates'][candidate] = results['candidates'].get(candidate, {})

                results['candidates'][candidate]['name'] = candidate
                results['candidates'][candidate]['votes'] = results['candidates'][candidate].get('votes', 0) + votes
                results['candidates'][candidate]['votesStr'] = formatIntegerNumber(results['candidates'][candidate]['votes'])

                results['totalVotes'] += votes
                results['totalVotesStr'] = formatIntegerNumber(results['totalVotes'])
                candidateRowIndex = candidateRowIndex + 1

        def frequencyPostParser(results):
            frequencyPerc = results.get('cardsReleased', 0) / results.get('allowed', 0) * 100.0
            results['frequencyPerc'] = frequencyPerc
            results['frequencyPercStr'] = formatPercents(frequencyPerc)

        def candidateVotesPostParser(results):
            candidateBests = []
            for candidate, candidateData in results['candidates'].items():
                candidateData['percentage'] = candidateData.get('votes', 0) / results.get('totalVotes', 0) * 100.0
                candidateData['percentageStr'] = formatPercents(candidateData['percentage'])
                candidateBests.append((candidateData['percentage'], candidate))
            candidateBests.sort(reverse=True)
            results['bestCandidates'] = []
            for candidateObj in candidateBests[:2]:
                results['bestCandidates'].append({
                    'name': candidateObj[1],
                    'label':  ' '.join(filter(lambda x: x.isupper(), candidateObj[1].split())).lower().capitalize()
                })


        aggregators = [
            voivodeshipCodeAgregator,
            allowedVotesAgregator,
            cardsReleasedAgregator,
            cardsCollectedAgregator,
            votesValidAgregator,
            votesInvalidAgregator,
            candidateVotesAgregator
        ]

        postParsers = [
            frequencyPostParser,
            candidateVotesPostParser
        ]

        with open('./pkw2000.csv', newline='', encoding='utf-8') as csvFile:
            dataReader = csv.reader(csvFile, delimiter=',')

            return self.aggregateVotingStats(dataReader, aggregators, resolution, postParsers)


    def generateData(self):

        if self.cache is not None:
            return self.cache

        data = {}

        generatedDataSearch = self.generateVotingData('search')
        generatedDataCommunes = self.generateVotingData('commune')
        generatedDataDivisions = self.generateVotingData('division')
        generatedDataVoivodeships = self.generateVotingData('voivodeship')
        generatedDataGeneral = self.generateVotingData()

        pageUrl = self.config['DEPLOY_URL']

        data['voting'] = {
            'voivodeshipCodes': self.voivodeshipsCodes,
            'pageUrl': pageUrl,
            'voivodeshipSubpageUrl': f'{pageUrl}/subpage_',
            'divisionSubpageUrl': f'{pageUrl}/division_',
            'communeSubpageUrl': f'{pageUrl}/commune_',
            **generatedDataGeneral,
            'voivodeships': generatedDataVoivodeships,
            'divisions': generatedDataDivisions,
            'communes': generatedDataCommunes,
            'search': generatedDataSearch
        }

        self.cache = data
        return data

    def generateScopedData(self, data={}, voivodeshipName=None, divisionNo=None, communeName=None):
        if voivodeshipName is None:
            voivodeshipName = ''
        if divisionNo is None:
            divisionNo = ''
        if communeName is None:
            communeName = ''
        data = {
            **data,
            **self.generateData()
        }

        data['voting']['voivodeshipSubpageName'] = voivodeshipName
        data['voting']['divisionSubpageNo'] = divisionNo
        data['voting']['communeSubpageName'] = communeName

        divisionCap = {}
        communeCap = {}

        if divisionNo is not '':
            divisionCap = data['voting']['divisions']
            data['voting']['divisions'] = {}
            data['voting']['divisions'][int(divisionNo)] = divisionCap[int(divisionNo)]
        else:
            divisionCap = data['voting']['divisions']
            data['voting']['divisions'] = {k: v for (k, v) in divisionCap.items() if v['voivodeshipName'] == voivodeshipName}

        if communeName is not '':
            communeCap = data['voting']['communes']
            data['voting']['communes'] = {}
            data['voting']['communes'][communeName] = communeCap[communeName]
        else:
            communeCap = data['voting']['communes']
            data['voting']['communes'] = {k: v for (k, v) in communeCap.items() if v['voivodeshipName'] == voivodeshipName and v['votingDivisionNo'] == divisionNo}

        data['votingJSON'] = json.dumps(data['voting'], indent=4, separators=(',', ': '))

        data['voting']['divisions'] = divisionCap
        data['voting']['communes'] = communeCap


        #voting.voivodeships.divisions[voting.divisionSubpageNo]

        return data

    def prepareData(self, data, fileName, fileIndex):
        return self.generateScopedData(data, None)