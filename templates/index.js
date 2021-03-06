/*
 * Remastered voting site
 * https://github.com/styczynski/pl-election-2000
 *
 * Piotr Styczyński @styczynski
 * MIT License
 */
(function(){
    /*
     * Colors used by charts.
     */
    var PIE_COLORS = [
        "#944a4a",
        "#6e5454",
        "#c79191",
        "#cecccc",
        "#ba8b8b",
        "#975259",
        "#c6b6b6",
        "#a15656",
        "#a8928a",
        "#754a4a",
        "#c5afaf"
    ];

    /*
     * Variable to capture voting data object (passed from voting_data.js).
     */
    let VOTING_DATA = null;

    /*
     * Variable to capture current page resultion data.
     * (i.e. voivodeship name / voting division no. / commune name)
     */
    let LOCATION_HINTS = null;

    /*
     * Listeners queue (listeners waiting for access to location hints/voting data)
     */
    let VOTING_DATA_QUEUE = [];

    /*
     * Notify queue that voting data is available.
     */
    var notifyVotingData = function() {
        if (VOTING_DATA && LOCATION_HINTS) {
            VOTING_DATA.voivodeshipSubpageName = LOCATION_HINTS.voivodeshipSubpageName;
            VOTING_DATA.divisionSubpageNo = LOCATION_HINTS.divisionSubpageNo;
            VOTING_DATA.communeSubpageName = LOCATION_HINTS.communeSubpageName;
            VOTING_DATA_QUEUE.forEach(function(fn) {
                fn(VOTING_DATA);
            });
            VOTING_DATA_QUEUE = [];
        }
    };

    /*
     * Set voting data and notify queue that voting data is available.
     */
    var provideVotingData = function(data) {
        if (!VOTING_DATA && data) {
            VOTING_DATA = data;
            notifyVotingData();
        }
    };
    

    /*
     * Add listener that waits for voting data/loc. hints to be available.
     * (both must be available for code to execute)
     */
    var requireVotingData = function(fn) {
        if (VOTING_DATA && LOCATION_HINTS) {
            fn(VOTING_DATA);
        } else {
            VOTING_DATA_QUEUE.push(fn);
        }
    };

    /*
     * Set loc. hints and notify queue that data is available.
     */
    var setLocationHints = function(x, y, z) {
        console.log('Set location hints');
        if (!LOCATION_HINTS) {
            LOCATION_HINTS = {};
            LOCATION_HINTS.voivodeshipSubpageName = x;
            LOCATION_HINTS.divisionSubpageNo = y;
            LOCATION_HINTS.communeSubpageName = z;
            notifyVotingData();
        }
    };

    /*
     * Export functions (globals)
     */
    window.provideVotingData = provideVotingData;
    window.setLocationHints = setLocationHints;
    
    
    
    /*
     * Wait for DOM to be ready.
     */
    $(document).ready(function() {
        
        /*
         * Main object that controlls interface interactions.
         */
        function ContentsView() {
            
            /*
             * Set contents view variables and methods.
             */
            var self = this;
            var sectionsNavList = $("main > nav > ul");
            self.displayedIndex = 0;
            self.sections = [];
            self.redrawMaps = null;
            self.switchTo = function changeContentView(index) {
                console.log("! Switch to " + index);
                self.displayedIndex = index;
                $("main section.active").removeClass('active');
                $($("main section.section-" + index)).addClass('active');
                if (self.redrawMaps) {
                    self.redrawMaps();
                }
            };
            
            /*
             * Function invoked to initialize contents handler.
             */
            self.init = function() {

                self.redrawMaps = (function() {
                    console.log('Redraw maps...');
                    self.__createCandidatesChart();
                    self.__loadMaps();
                });

                /*
                 * Redraw maps is called on resize to provideVotingData
                 * responsive scalling charts.
                 */
                $(window).resize(function() {
                    self.redrawMaps();
                });

                /*
                 * Initially draw all maps and install DOM hooks
                 * (i.e. click handlers etc.)
                 */
                self.redrawMaps();
                self.__installClickHooks();

                /*
                 * Initialize only-one-shown behaviour for sections and
                 * sections- navigation buttons.
                 */
                $("main section > i").each(function(index) {
                    var el = $(this);
                    var section = el.parent();
                    section.addClass("section-" + index);
                    var sectionName = section.find("h2").text();
                    var clickableIcon = ($("" +
                        "<li>\n" +
                        "   <figure>\n" +
                        "      <i class=\"" + el.data("icon") + "\"></i>\n" +
                        "   </figure>\n" +
                        "</li>"
                    ));
                    clickableIcon.click(function() {
                        self.switchTo(index);
                    });
                    sectionsNavList.append(clickableIcon);
                    self.sections.push({
                        name: sectionName,
                        element: section
                    });
                });
                
                // Switch to default section
                self.switchTo(self.displayedIndex);
            };
            
            /*
             * Setup all maps.
             */
            self.__loadMaps = function() {
                google.charts.load('current', {
                    'packages': ['geochart', 'corechart'],
                    'mapsApiKey': 'AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY'
                });
                google.charts.setOnLoadCallback(function() {
                    requireVotingData(function() {
                        /*
                         * Initialize all maps when Google Charts are ready
                         */
                        self.__createFrequencyMap();
                        self.__createMainNavigationMap();
                        self.__createGeneralStatsChartVotesByRegion();
                        self.__createGeneralStatsChartVotesInvalidRate();
                    });
                });
            };

            /*
             * Used to generate general cote statistics.
             */
            self.__createGeneralStatsChartVotesByRegion = function() {

                $('#votes-by-region-chart .loading-spinner').remove();

                var votesByRegionCols = [
                    [{
                            'label': 'Region',
                            'id': 'region',
                            'type': 'string'
                        },
                        {
                            'label': 'Głosy zebrane z urn',
                            'id': 'collected-votes',
                            'type': 'number'
                        },
                        {
                            role: 'style'
                        }
                    ]
                ];

                var votesByRegionData = google.visualization.arrayToDataTable(votesByRegionCols);

                // For country scope
                if (!VOTING_DATA.voivodeshipSubpageName) {

                    votesByRegionData.addRows(
                        Object.keys(VOTING_DATA.voivodeships).map(function(voivodeshipName, i) {
                            const regionData = VOTING_DATA.voivodeships[voivodeshipName];
                            return [
                                regionData.name,
                                regionData.totalVotes,
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                // For voivodeship scope
                } else if (!VOTING_DATA.divisionSubpageNo) {

                    votesByRegionData.addRows(
                        Object.keys(VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName].divisions).map(function(divisionNo, i) {
                            const regionData = VOTING_DATA.divisions[divisionNo];
                            return [
                                'Okręg ' + divisionNo,
                                regionData.totalVotes,
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                // For division and commune scope
                } else {

                    votesByRegionData.addRows(
                        Object.keys(VOTING_DATA.divisions[VOTING_DATA.divisionSubpageNo].communes).map(function(communeName, i) {
                            const regionData = VOTING_DATA.communes[communeName];
                            return [
                                communeName,
                                regionData.totalVotes,
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                }

                var votesByRegionOptions = {
                    'title': 'Głosy zebrane\nwg. regionów',
                    'titleTextStyle': {
                        fontName: "'PT Sans', sans-serif",
                        bold: true,
                        color: '#575755'
                    },
                    'width': '100%',
                    'height': '100%',
                    'colors': PIE_COLORS,
                    'legend': {
                        position: "none"
                    },
                    'backgroundColor': 'transparent'
                };

                var votesByRegionChart = new google.visualization.PieChart(document.getElementById('votes-by-region-chart'));
                votesByRegionChart.draw(votesByRegionData, votesByRegionOptions);

            };

            /*
             * Setup invalid votes chart.
             */
            self.__createGeneralStatsChartVotesInvalidRate = function() {

                $('#votes-invalid-rate-chart .loading-spinner').remove();

                // Create the data table.
                var votesInvalidRateData = new google.visualization.DataTable();
                votesInvalidRateData.addColumn('string', 'Region');
                votesInvalidRateData.addColumn('number', 'Procent głosów\nnieważnych');

                var votesInvalidRateCols = [
                    [{
                            'label': 'Region',
                            'id': 'region',
                            'type': 'string'
                        },
                        {
                            'label': 'Procent głosów nieważnych',
                            'id': 'invalid-votes-rate',
                            'type': 'number'
                        },
                        {
                            role: 'style'
                        }
                    ]
                ];

                var votesInvalidRateData = google.visualization.arrayToDataTable(votesInvalidRateCols);

                // For country-scope
                if (!VOTING_DATA.voivodeshipSubpageName) {

                    votesInvalidRateData.addRows(
                        Object.keys(VOTING_DATA.voivodeships).map(function(voivodeshipName, i) {
                            const regionData = VOTING_DATA.voivodeships[voivodeshipName];
                            return [
                                regionData.name,
                                (regionData.votesInvalid / regionData.totalVotes),
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                // For voivodeship-scope
                } else if (!VOTING_DATA.divisionSubpageNo) {

                    votesInvalidRateData.addRows(
                        Object.keys(VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName].divisions).map(function(divisionNo, i) {
                            const regionData = VOTING_DATA.divisions[divisionNo];
                            return [
                                'Okręg ' + divisionNo,
                                (regionData.votesInvalid / regionData.totalVotes),
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                // For division/commune-scope
                } else {

                    votesInvalidRateData.addRows(
                        Object.keys(VOTING_DATA.divisions[VOTING_DATA.divisionSubpageNo].communes).map(function(communeName, i) {
                            const regionData = VOTING_DATA.communes[communeName];
                            return [
                                communeName,
                                (regionData.votesInvalid / regionData.totalVotes),
                                'color: ' + PIE_COLORS[i % 2]
                            ];
                        })
                    );

                }

                var votesInvalidRateOptions = {
                    'title': 'Procent głosów niewaznych',
                    'titleTextStyle': {
                        fontName: "'PT Sans', sans-serif",
                        bold: true,
                        color: '#575755'
                    },
                    'width': '100%',
                    'height': '100%',
                    'legend': {
                        position: "none"
                    },
                    'hAxis': {
                        format: "percent"
                    },
                    'backgroundColor': 'transparent'
                };

                var votesInvalidRateChart = new google.visualization.BarChart(document.getElementById('votes-invalid-rate-chart'));
                votesInvalidRateChart.draw(votesInvalidRateData, votesInvalidRateOptions);

            };

            /*
             * Create clickable navigation map.
             */
            self.__createMainNavigationMap = function() {

                dataToNavigate = [
                    ['Region', 'None']
                ];

                if (VOTING_DATA.voivodeshipSubpageName) {
                    var voivodeshipCode = VOTING_DATA.voivodeshipCodes[VOTING_DATA.voivodeshipSubpageName];
                    if (voivodeshipCode) {
                        dataToNavigate.push([
                            voivodeshipCode, 100
                        ]);
                    }
                }

                var data = google.visualization.arrayToDataTable(dataToNavigate);

                var options = {
                    region: 'PL',
                    resolution: 'provinces',
                    backgroundColor: 'transparent',
                    height: 500,
                    width: 500,
                    legend: 'none',
                    tooltip: {
                        isHtml: true,
                        trigger: 'none'
                    },
                    colorAxis: {
                        colors: ['#cecccc', '#754a4a']
                    }
                };

                var chart = null;

                function clickRegion(eventData) {

                    console.log(eventData.region);

                    var voivodeshipFullName = Object.keys(VOTING_DATA.voivodeshipCodes).filter(function(key) {
                        return VOTING_DATA.voivodeshipCodes[key] == eventData.region;
                    })[0];

                    if (voivodeshipFullName) {
                        window.location = VOTING_DATA.voivodeshipSubpageUrl + voivodeshipFullName + '.html';
                    };
                };

                function chartReady() {
                    // Hack to mark the desired region without changing opacity
                    $('#main-map-chart path:not([fill="#f5f5f5"])').first().attr('style', 'fill: #cecccc !important;');
                };

                function pageScrolled() {
                    const distanceY = window.pageYOffset || document.documentElement.scrollTop,
                        shrinkOn = 200,
                        mapElement = $('#main-map-chart')
                    asideElement = $('aside')

                    if (distanceY > shrinkOn) {
                        mapElement.addClass('minimized');
                        asideElement.addClass('active');
                    } else {
                        mapElement.removeClass('minimized');
                        asideElement.removeClass('active');
                    }
                }

                chart = new google.visualization.GeoChart(document.getElementById('main-map-chart'));

                google.visualization.events.addListener(chart, 'regionClick', clickRegion);
                google.visualization.events.addListener(chart, 'ready', chartReady);


                window.addEventListener('scroll', pageScrolled);


                chart.draw(data, options);

            };

            /*
             * Create frequency map.
             */
            self.__createFrequencyMap = function() {

                $('#frequency-map-chart .loading-spinner').remove();

                // Country scope
                if (!VOTING_DATA.voivodeshipSubpageName) {
                    var frequencyData = [
                        [{
                                'label': 'Region',
                                'id': 'region',
                                'type': 'string'
                            },
                            {
                                'label': 'Frekwencja (%)',
                                'id': 'frequency',
                                'type': 'number'
                            },
                            {
                                'role': 'tooltip',
                                'type': 'string',
                                'p': {
                                    'html': true
                                }
                            }
                        ]
                    ];

                    frequencyData = frequencyData.concat(Object.values(VOTING_DATA.voivodeships).map(function(voivodeship) {
                        return [
                            voivodeship.voivodeshipCode,
                            voivodeship.frequencyPerc,
                            "<b>" + voivodeship.name + "</b>" +
                            "<p><b>Frekwencja: </b>&nbsp;" + voivodeship.frequencyPercStr + "</p>" +
                            "<p></p>" +
                            "<p><b>Uprawnionych: </b>&nbsp;" + voivodeship.allowedStr + "</p>" +
                            "<p><b>Wydanych kart: </b>&nbsp;" + voivodeship.cardsReleasedStr + "</p>"
                        ];
                    }));

                    var data = google.visualization.arrayToDataTable(frequencyData);

                    var options = {
                        region: 'PL',
                        resolution: 'provinces',
                        backgroundColor: 'transparent',
                        height: '100%',
                        width: '100%',
                        tooltip: {
                            isHtml: true
                        },
                        colorAxis: {
                            colors: ['#cecccc', '#754a4a']
                        }
                    };

                    var chart = new google.visualization.GeoChart(document.getElementById('frequency-map-chart'));

                    function clickRegion(eventData) {
                        var voivodeshipFullName = Object.values(VOTING_DATA.voivodeships).filter(function(voivodeship) {
                            return voivodeship.voivodeshipCode == eventData.region;
                        })[0];

                        if (voivodeshipFullName) {
                            window.location = VOTING_DATA.voivodeshipSubpageUrl + voivodeshipFullName.name + '.html';
                        };
                    };
                    google.visualization.events.addListener(chart, 'regionClick', clickRegion);

                    chart.draw(data, options);
                    
                // Voivodeship scope
                } else if (!VOTING_DATA.divisionSubpageNo) {

                    var chartData = [
                        ['Okręg', 'Frekwencja', {
                            role: 'style'
                        }]
                    ];

                    chartData = chartData.concat(Object.keys(VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName].divisions).map(function(divisionNo, index) {
                        return [
                            'Okręg ' + divisionNo,
                            VOTING_DATA.divisions[divisionNo].frequencyPerc,
                            PIE_COLORS[index % 2]
                        ]
                    }));

                    var data = google.visualization.arrayToDataTable(chartData);

                    var view = new google.visualization.DataView(data);

                    var options = {
                        title: 'Frekwencja',
                        width: '100%',
                        height: '100%',
                        backgroundColor: 'transparent',
                        bar: {
                            groupWidth: '95%'
                        },
                        legend: {
                            position: 'none'
                        }
                    };
                    var chart = new google.visualization.BarChart(document.getElementById('frequency-map-chart'));
                    chart.draw(view, options);
                    
                // Voting division scope
                } else if (!VOTING_DATA.communeSubpageName) {
                    var chartData = [
                        ['Gmina', 'Frekwencja', {
                            role: 'style'
                        }]
                    ];

                    chartData = chartData.concat(Object.keys(VOTING_DATA.divisions[VOTING_DATA.divisionSubpageNo].communes).map(function(communeName, index) {
                        return [
                            communeName,
                            VOTING_DATA.communes[communeName].frequencyPerc,
                            PIE_COLORS[index % 2]
                        ]
                    }));

                    var data = google.visualization.arrayToDataTable(chartData);

                    var view = new google.visualization.DataView(data);

                    var options = {
                        width: '100%',
                        height: '100%',
                        backgroundColor: 'transparent',
                        bar: {
                            groupWidth: '95%'
                        },
                        legend: {
                            position: 'none'
                        },
                        chartArea: {
                            width: '850px'
                        },
                        hAxis: {
                            slantedText: true,
                            slantedTextAngle: 90
                        }
                    };
                    var chart = new google.visualization.ColumnChart(document.getElementById('frequency-map-chart'));
                    chart.draw(view, options);
                }

            };

            /*
             * Create links for all dom elements with data-link-... data attributes.
             */
            self.installLinkAtDOM = function(el) {
                requireVotingData(function() {
                    var self = $(el);
                    self.click(function() {
                        var voivodeshipFullName = self.data('link-voivodeship');
                        var divisionNo = self.data('link-division');
                        var communeName = self.data('link-commune');

                        if (voivodeshipFullName !== null && voivodeshipFullName !== undefined) {
                            if (VOTING_DATA.voivodeshipCodes[voivodeshipFullName]) {
                                window.location = VOTING_DATA.voivodeshipSubpageUrl + voivodeshipFullName + '.html';
                            }
                        } else if (divisionNo !== null && divisionNo !== undefined) {
                            window.location = VOTING_DATA.divisionSubpageUrl + divisionNo + '.html';
                        } else if (communeName !== null && communeName !== undefined) {
                            window.location = VOTING_DATA.communeSubpageUrl + communeName + '.html';
                        }
                    });
                });
            };
            
            /*
             * Install click hooks.
             * (clickable tables etc.)
             */
            self.__installClickHooks = function() {

                requireVotingData(function() {
                    var maputils = self;

                    var toSearch = [];
                    Object.keys(VOTING_DATA.search.voivodeships).forEach(function(voivodeshipName) {
                        toSearch.push({
                            textData: 'Województwo ' + voivodeshipName,
                            label: voivodeshipName,
                            itemType: 'voivodeship',
                            name: voivodeshipName
                        });
                    });

                    Object.keys(VOTING_DATA.search.divisions).forEach(function(divisionNo) {
                        toSearch.push({
                            textData: 'Okręg ' + divisionNo,
                            label: 'Okręg ' + divisionNo,
                            itemType: 'division',
                            name: divisionNo
                        });
                    });

                    Object.keys(VOTING_DATA.search.communes).forEach(function(communeName) {
                        toSearch.push({
                            textData: 'Gmina ' + communeName,
                            label: communeName,
                            itemType: 'commune',
                            name: communeName
                        });
                    });
                    window.VOTE_DATA_SEARCH = toSearch;


                    $('body > nav ul li input').each(function() {
                        var self = $(this);
                        var resultsList = self.parent().find('ol');
                        var updatesRequested = 0;

                        var changeHandler = (function() {
                            var content = self.val();
                            var results = [];

                            if (updatesRequested >= 2) {
                                return;
                            } else {
                                ++updatesRequested;
                            }

                            console.log('request fuzzy search');

                            results = fuzzysort.go(content, toSearch, {
                                key: 'textData'
                            }).slice(0, 15).map(function(result) {

                                var resultNode = $('<li></li>');
                                resultNode.text(result.obj.label);

                                if (result.obj.itemType == 'voivodeship') {
                                    resultNode.data('link-voivodeship', result.obj.name);
                                } else if (result.obj.itemType == 'division') {
                                    resultNode.data('link-division', result.obj.name);
                                } else if (result.obj.itemType == 'commune') {
                                    resultNode.data('link-commune', result.obj.name);
                                }

                                return resultNode;
                            });

                            --updatesRequested;

                            resultsList.children().remove();
                            results.forEach(function(item) {
                                maputils.installLinkAtDOM(item);
                                item.appendTo(resultsList);
                            });
                        });

                        self.keydown(changeHandler);
                        self.on('input propertychange', changeHandler);
                    });

                    $('body > nav ul li').each(function() {
                        var self = $(this);
                        var nestedList = self.find('ul');
                        var nestedInput = self.find('input');
                        var nestedResultList = self.find('ol');

                        var isSelfHovered = false;
                        var isNestedListHovered = false;
                        var isNestedInputHovered = false;
                        var isNestedResultListHovered = false;

                        function updateHoverClasses() {
                            if (isSelfHovered || isNestedListHovered || isNestedInputHovered || isNestedResultListHovered) {
                                self.addClass('active');
                                nestedList.addClass('active');
                                nestedInput.addClass('active');
                                nestedResultList.addClass('active');
                            } else {
                                self.removeClass('active');
                                nestedList.removeClass('active');
                                nestedInput.removeClass('active');
                                nestedResultList.removeClass('active');
                            }
                        };

                        nestedResultList.hover(function() {
                            isNestedResultListHovered = true;
                            updateHoverClasses();
                        }, function() {
                            isNestedResultListHovered = false;
                            updateHoverClasses();
                        });

                        nestedInput.hover(function() {
                            isNestedInputHovered = true;
                            updateHoverClasses();
                        }, function() {
                            isNestedInputHovered = false;
                            updateHoverClasses();
                        });

                        nestedList.hover(function() {
                            isNestedListHovered = true;
                            updateHoverClasses();
                        }, function() {
                            isNestedListHovered = false;
                            updateHoverClasses();
                        });

                        self.hover(function() {
                            isSelfHovered = true;
                            updateHoverClasses();
                        }, function() {
                            isSelfHovered = false;
                            updateHoverClasses();
                        });

                        updateHoverClasses();
                    })

                    $('[data-link-voivodeship],[data-link-division],[data-link-commune]').each(function() {
                        self.installLinkAtDOM(this);
                    });

                    $('table').each(function() {
                        var table = $(this);
                        table.find('th').each(function(i) {
                            var self = $(this);
                            var tableBody = table.find('tbody');
                            var sortingType = self.data('type') || 'string';
                            var sortingMode = self.data('mode') || 'toggle';

                            var castToType = function(type, value) {
                                if (type == 'string') {
                                    return value.toString();
                                } else if (type == 'integer') {
                                    return parseInt(value.toString().replace(/[,\.]/ig, ''));
                                } else if (type == 'float') {
                                    return parseFloat(value.toString().replace(/[,\.]/ig, '.'));
                                } else if (type == 'percentage') {
                                    return parseFloat(value.toString().replace(/%/ig, '').replace(/[,\.]/ig, '.'));
                                }
                                return value;
                            };

                            (function(thIndex, type, mode) {
                                var sortOnClick = (function() {
                                    var currentMode = self.data('current-mode');
                                    var sortedRows = tableBody.find('tr').sort(function(rowA, rowB) {
                                        var colA = $($(rowA).children()[thIndex]).text();
                                        console.log("textA = " + colA);
                                        var colB = $($(rowB).children()[thIndex]).text();
                                        colA = castToType(type, colA);
                                        colB = castToType(type, colB);
                                        console.log([colA, colB]);
                                        if (mode == 'toggle') {
                                            if (currentMode == 'asc') {
                                                return colA > colB ? -1 : colA < colB ? 1 : 0;
                                            }
                                            return colA > colB ? 1 : colA < colB ? -1 : 0;
                                        } else if (mode == 'asc') {
                                            return colA > colB ? -1 : colA < colB ? 1 : 0;
                                        }
                                        return colA > colB ? 1 : colA < colB ? -1 : 0;
                                    });
                                    table.find('th').removeClass('sort-asc').removeClass('sort-desc');

                                    if (mode == 'toggle') {
                                        if (currentMode == 'asc') {
                                            self.data('current-mode', 'desc');
                                            self.addClass('sort-desc');
                                        } else {
                                            self.data('current-mode', 'asc');
                                            self.addClass('sort-asc');
                                        }
                                    } else if (mode == 'asc') {
                                        self.data('current-mode', 'asc');
                                        self.addClass('sort-asc');
                                    } else if (mode == 'desc') {
                                        self.data('current-mode', 'desc');
                                        self.addClass('sort-desc');
                                    }
                                    sortedRows.appendTo(tableBody);
                                });
                                self.click(sortOnClick);
                                
                                // Initially sorts the data
                                sortOnClick();
                            }(i, sortingType, sortingMode));
                        });
                    });
                });
            };

            /*
             * Get data scoped for current subpage region.
             */
            self.getSubpageRegionResolutionData = function() {
                if(!VOTING_DATA.voivodeshipSubpageName) {
                    return VOTING_DATA;
                } else if (!VOTING_DATA.divisionSubpageNo) {
                    return VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName];
                } else if(!VOTING_DATA.communeSubpageName) {
                    return VOTING_DATA.divisions[VOTING_DATA.divisionSubpageNo];
                } else {
                    return VOTING_DATA.communes[VOTING_DATA.communeSubpageName];
                }
            };

            /*
             * Draw votes-per-candidates chart.
             */
            self.__createCandidatesChart = function() {

                requireVotingData(function() {

                    $('#votes-per-cand-chart .loading-spinner').remove();

                    $("#votes-per-cand-chart").children().remove();

                    var pieVotesConfigArray = [];

                    Object.values(self.getSubpageRegionResolutionData().candidates).forEach(function(el, index) {
                        pieVotesConfigArray.push({
                            label: el.name,
                            value: el.votes,
                            color: PIE_COLORS[index % PIE_COLORS.length]
                        });
                    });

                    var pie = new d3pie("votes-per-cand-chart", {
                        "header": {
                            "title": {
                                "text": "Wyniki wyobrów 2000r.",
                                "fontSize": 16,
                                "font": "open sans"
                            },
                            "subtitle": {
                                "text": "",
                                "color": "#999999",
                                "fontSize": 12,
                                "font": "open sans"
                            },
                            "titleSubtitlePadding": 9
                        },
                        "footer": {
                            "color": "#999999",
                            "fontSize": 10,
                            "font": "open sans",
                            "location": "bottom-left"
                        },
                        "size": {
                            "canvasWidth": 790,
                            "pieInnerRadius": "48%",
                            "pieOuterRadius": "90%"
                        },
                        "data": {
                            "sortOrder": "value-desc",
                            "content": pieVotesConfigArray
                        },
                        "labels": {
                            "outer": {
                                "pieDistance": 32
                            },
                            "inner": {
                                "hideWhenLessThanPercentage": 3
                            },
                            "mainLabel": {
                                "fontSize": 11
                            },
                            "percentage": {
                                "color": "#ffffff",
                                "decimalPlaces": 0
                            },
                            "value": {
                                "color": "#adadad",
                                "fontSize": 11
                            },
                            "lines": {
                                "enabled": true
                            },
                            "truncation": {
                                "enabled": true
                            }
                        },
                        "effects": {
                            "pullOutSegmentOnClick": {
                                "effect": "linear",
                                "speed": 400,
                                "size": 8
                            }
                        },
                        "misc": {
                            "gradient": {
                                "enabled": true,
                                "percentage": 100
                            }
                        }
                    });

                    $("#votes-per-cand-chart svg")
                        .attr('width', '100%')
                        .attr('height', '100%')
                        .attr('viewBox', '0 0 850 450');

                });

            };
            return self;
        }
        var view = new ContentsView();
        view.init();
        window.contentsView = view;
    });

})();