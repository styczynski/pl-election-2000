import json
import csv

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

class DataGenerator:

    def __init__(self, path):
        self.path = path

    def prepareData(self, data, fileName, fileIndex):
        with open('./pkw2000.csv', newline='', encoding='utf-8') as csvFile:
            dataReader = csv.reader(csvFile, delimiter=',')

            regions = {}
            totals = {
                'sum': 0
            }

            dataHead = next(dataReader)
            candidateNames = dataHead[11:]

            for row in dataReader:
                voivodeshipName = row[0]
                if voivodeshipName not in regions:
                    regions[voivodeshipName] = {
                        'allowed': 0,
                        'cardsReleased': 0
                    }
                    for candidate in candidateNames:
                        regions[voivodeshipName][candidate] = 0
                regions[voivodeshipName]['allowed'] += int(row[6])
                regions[voivodeshipName]['cardsReleased'] += int(row[7])

                candidateRowIndex = 11
                for candidate in candidateNames:
                    votes = int(row[candidateRowIndex])
                    regions[voivodeshipName][candidate] += votes
                    if candidate not in totals:
                        totals[candidate] = 0
                    totals[candidate] += votes
                    totals['sum'] += votes
                    candidateRowIndex = candidateRowIndex+1

            for regionName, regionData in regions.items():
                frequencyPerc = regionData['cardsReleased'] / regionData['allowed'] * 100.0
                regionData['frequencyPerc'] = frequencyPerc
                regionData['frequencyPercStr'] = f'{format(frequencyPerc, ".2f")}%'
                regionData['allowedStr'] = format(regionData['allowed'], '6,d')
                regionData['cardsReleasedStr'] = format(regionData['cardsReleased'], '6,d')
                regions[regionName] = regionData


            totalsData = []
            for candidate, candidateData in totals.items():
                if candidate is not 'sum':
                    totalsData.append({
                        'name': candidate,
                        'votes': candidateData / totals['sum'],
                        'votesPercStr': format(candidateData / totals['sum'] * 100, '.2f') + '%',
                        'votesCountStr': format(candidateData, '6,d'),
                        'votesCount': candidateData
                    })

            totalsData = sorted(totalsData, reverse=True, key=lambda x: x['votesCount'])

            # 'Uprawnionych (os.)', 'Wydane karty (szt.)'
            frequencyRegionData = [
                [
                    {'label': 'Region', 'id': 'region', 'type': 'string'},
                    {'label': 'Frekwencja (%)', 'id': 'frequency', 'type': 'number'},
                    {'role': 'tooltip', 'type': 'string', 'p': {'html': True}}
                ]
            ]

            for regionName, regionData in regions.items():
                frequencyRegionData.append([
                    voivodeshipsCodes[regionName],
                    regionData['frequencyPerc'],
                    f'''
                    <b>{regionName}</b>
                    <p><b>Frekwencja: </b>&nbsp;{regionData['frequencyPercStr']}</p>
                    <p></p>
                    <p><b>Uprawnionych: </b>&nbsp;{regionData['allowedStr']}</p>
                    <p><b>Wydanych kart: </b>&nbsp;{regionData['cardsReleasedStr']}</p>
                    '''
                ])

            frequencyRegionDataJSON = json.dumps(frequencyRegionData, indent=4, separators=(',', ': '))
            data['VoteDataVoivodeshipsFrequencyJSON'] = frequencyRegionDataJSON
            data['VoteDataVoivodeshipsFrequency'] = regions

            totalsDataJSON = json.dumps(totalsData, indent=4, separators=(',', ': '))
            data['VoteDataTotalVotesPerCandidateJSON'] = totalsDataJSON
            data['VoteDataTotalVotesPerCandidate'] = totalsData

            voivodeshipCodesJSON = json.dumps(voivodeshipsCodes, indent=4, separators=(',', ': '))
            data['VoivodeshipsCodesJSON'] = voivodeshipCodesJSON

        return data