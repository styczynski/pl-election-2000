# 
# Remastered voting site
# https://github.com/styczynski/pl-election-2000
#
# Piotr Styczyński @styczynski
# MIT License
#

import json
import csv
import copy

"""
    Top-level index data generator.

    Piotr Styczyński @styczynski
    MIT License
"""
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
    """
        Mapping between voivodeships and their standard region codes.
    """

    def __init__(self, path, config):
        """
            Create new generator for given path and config.
        """
        self.path = path
        self.cache = None
        self.config = config

    def getJSFileNames(self):
        """
            Generate common js file.
        """
        return [ 'voting_data' ]
        
    def aggregateVotingStats(self, dataReader=None, aggregators=[], resolution=None, postParsers=[]):
        """
            Used to aggregate loaded CSV data with given list of aggregators and resolution.
            The function returns scoped data depending on resolution:
            
                - 'voivodeship' - aggregate data for whole voivodeships
                - 'division'    - aggregate data for whole divisions
                - 'commune'     - aggregate data for whole communes
                
            The function runs aggregator functions provided by aggregators parameter
            supplying them with CSV row and data. Then the aggregator can add any field that
            will be stored under specific field (depending on selected resolution).
            
            The user can optionally specify postParsers - function that will be operating on
            already generated data (for derived properties).
        """
    
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

        # Parse each row of CSV data executing aggregators
        for row in dataReader:
            voivodeShipName = row[0]
            votingDivisionNo = int(row[1])
            votingCommuneName = row[3]

            tgtObj = totalsDetails

            # Scope data properly
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

            # Eexecute each aggregator
            for aggregator in aggregators:
                aggregator(tgtObj, row, dataHead)

        # Execute post parsers
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
        """
            Generates voting data for required resolution (voivodeship/commune/division).
        """
    
        def formatIntegerNumber(num):
            """
                For formatting integer values.
            """
            return format(num, '6,d')

        def formatPercents(num):
            """
                For formatting percentage values.
            """
            return f'{format(num, ".2f")}%'

        def voivodeshipCodeAgregator(results, row, header):
            """
                Aggregator:
                    Adds voivodeship code to the data.
            """
            results['voivodeshipCode'] = self.voivodeshipsCodes[row[0]]

        def allowedVotesAgregator(results, row, header):
            """
                Aggregator:
                    Counts total number of citizens allowed to vote.
            """
            results['allowed'] = results.get('allowed', 0) + int(row[6])
            results['allowedStr'] = formatIntegerNumber(results['allowed'])

        def cardsReleasedAgregator(results, row, header):
            """
                Aggregator:
                    Counts total number of released voting cards.
            """
            results['cardsReleased'] = results.get('cardsReleased', 0) + int(row[7])
            results['cardsReleasedStr'] = formatIntegerNumber(results['cardsReleased'])

        def cardsCollectedAgregator(results, row, header):
            """
                Aggregator:
                    Counts total number of collected voting cards.
            """
            results['cardsCollected'] = results.get('cardsCollected', 0) + int(row[8])
            results['cardsCollectedStr'] = formatIntegerNumber(results['cardsCollected'])

        def votesValidAgregator(results, row, header):
            """
                Aggregator:
                    Counts valid votes.
            """
            results['votesValid'] = results.get('votesValid', 0) + int(row[10])
            results['votesValidStr'] = formatIntegerNumber(results['votesValid'])

        def votesInvalidAgregator(results, row, header):
            """
                Aggregator:
                    Counts invalid votes.
            """
            results['votesInvalid'] = results.get('votesInvalid', 0) + int(row[9])
            results['votesInvalidStr'] = formatIntegerNumber(results['votesInvalid'])

        def candidateVotesAgregator(results, row, header):
            """
                Aggregator:
                    Generates votes per candidate.
            """
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
            """
                Post parser:
                    Generates frequency data for the collected votes.
            """
            frequencyPerc = results.get('cardsReleased', 0) / results.get('allowed', 0) * 100.0
            results['frequencyPerc'] = frequencyPerc
            results['frequencyPercStr'] = formatPercents(frequencyPerc)

        def candidateVotesPostParser(results):
            """
                Post parser:
                    Generates percentage results for all of the candidates
            """
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


        # List of aggregators
        aggregators = [
            voivodeshipCodeAgregator,
            allowedVotesAgregator,
            cardsReleasedAgregator,
            cardsCollectedAgregator,
            votesValidAgregator,
            votesInvalidAgregator,
            candidateVotesAgregator
        ]

        # List of post parsers
        postParsers = [
            frequencyPostParser,
            candidateVotesPostParser
        ]

        #
        # Read csv file
        #
        with open('./pkw2000.csv', newline='', encoding='utf-8') as csvFile:
            dataReader = csv.reader(csvFile, delimiter=',')

            return self.aggregateVotingStats(dataReader, aggregators, resolution, postParsers)


    def generateData(self):
        """
           Generates full data object.
           This function is called in the subpages' generators.
           It is cached so there's no problem with the code efficiency.
        """
    
        # Use cache if available
        if self.cache is not None:
            return self.cache

        data = {}

        #
        # Generate and merge scoped data
        #
        generatedDataSearch = self.generateVotingData('search')
        generatedDataCommunes = self.generateVotingData('commune')
        generatedDataDivisions = self.generateVotingData('division')
        generatedDataVoivodeships = self.generateVotingData('voivodeship')
        generatedDataGeneral = self.generateVotingData()

        pageUrl = self.config['DEPLOY_URL']

        # Final data representation
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

        data['votingJSONFull'] = json.dumps(data['voting'])
        
        self.cache = data
        return data

    
    def generateScopedData(self, data={}, voivodeshipName=None, divisionNo=None, communeName=None):
        """
            Generates data scoped for specific voivodeship, division and commune.
            It utilizes caching capabilities of generateData() so no time inefficiency takes place.
        """
        
        if voivodeshipName is None:
            voivodeshipName = ''
        if divisionNo is None:
            divisionNo = ''
        if communeName is None:
            communeName = ''
            
        # Integrate default cached data into the result
        data = {
            **data,
            **self.generateData()
        }

        # Provide scope-dependent data
        data['voting']['voivodeshipSubpageName'] = voivodeshipName
        data['voting']['divisionSubpageNo'] = divisionNo
        data['voting']['communeSubpageName'] = communeName

        return data

    def prepareData(self, data, fileName, fileIndex):
        """
            Prepare data for the HTML template
        """
        return self.generateScopedData(data, None)