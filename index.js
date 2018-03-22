
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

$(document).ready(function() {
    function ContentsView() {
        var self = this;
        var sectionsNavList = $("main > nav > ul");
        self.displayedIndex = 0;
        self.sections = [];
        self.switchTo = function changeContentView(index) {
            console.log("! Switch to "+index);
            self.displayedIndex = index;
            $("main section.active").removeClass('active');
            $($("main section.section-"+index)).addClass('active');
        };
        self.init = function() {
            self.__createChart();
            self.__loadMaps();
            self.__installClickHooks();

            $("main section > .section-icon").each(function(index){
               var el = $(this);
               var section = el.parent();
               section.addClass("section-"+index);
               var sectionName = section.find("h2").text();
               var clickableIcon = ($("" +
                   "<li>\n" +
                   "   <h1>\n" +
                   "      <i class=\""+el.data("icon")+"\"></i>\n" +
                   "   </h1>\n" +
                   "</li>"
               ));
               clickableIcon.click(function(){
                   self.switchTo(index);
               });
               sectionsNavList.append(clickableIcon);
               self.sections.push({
                   name: sectionName,
                   element: section
               });
            });
            self.switchTo(self.displayedIndex);
        };
        self.__loadMaps = function() {
            google.charts.load('current', {
                'packages':['geochart', 'corechart'],
                // Note: you will need to get a mapsApiKey for your project.
                // See: https://developers.google.com/chart/interactive/docs/basic_load_libs#load-settings
                'mapsApiKey': 'AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY'
            });
            google.charts.setOnLoadCallback(function(){
                self.__createGeoMap();
                self.__createMainNavigationMap();
                //self.__createGeoSubdivisionMap();
            });
        };
        self.__createGeoSubdivisionMap = function() {

            // <div id="subdivision-map-chart"></div>
            // Create and populate a data table
            var data = new google.visualization.DataTable();
            data.addColumn("string", "City");
            data.addColumn("number", "Value");
            data.addRows([
                ["Rio de Janeiro", 10],
                ["Maricá", 5],
                ["São João de Meriti", 2],
                ["Niterói", 1],
                ["São Gonçalo", 1]
            ]);

            // Instantiate our Geochart GeoJSON object
            var vis = new geochart_geojson.GeoChart(document.getElementById("subdivision-map-chart"));

            // Set Geochart GeoJSON options
            var options = {
                mapsOptions: {
                    center: {lat: -22.15, lng: -42.9},
                    zoom: 8
                },
                geoJson: "./assets/powiaty.geojson",
                geoJsonOptions: {
                    idPropertyName: "name"
                }
            };

            // Draw our Geochart GeoJSON with the data we created locally
            vis.draw(data, options);
        };

        self.__createMainNavigationMap = function() {

              dataToNavigate = [
                  ['Region', 'None']
              ];

              if(VOTING_DATA.voivodeshipSubpageName) {
                  var voivodeshipCode = VOTING_DATA.voivodeshipCodes[VOTING_DATA.voivodeshipSubpageName];
                  if(voivodeshipCode) {
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

                    var voivodeshipFullName = Object.keys(VOTING_DATA.voivodeshipCodes).filter(function(key){
                        return VOTING_DATA.voivodeshipCodes[key] == eventData.region;
                    })[0];

                    if(voivodeshipFullName) {
                        window.location = VOTING_DATA.voivodeshipSubpageUrl + voivodeshipFullName + '.html';
                    };
              };

              function chartReady() {
                  // Hack to mark the desired region without changing opacity
                  $('.main-map-fig path:not([fill="#f5f5f5"])').first().attr('style', 'fill: #cecccc !important;');
              };

              function pageScrolled() {
                  const distanceY = window.pageYOffset || document.documentElement.scrollTop,
                  shrinkOn = 200,
                  mapElement = $('.main-map-fig')
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

        self.__createGeoMap = function() {

              if(!VOTING_DATA.voivodeshipSubpageName) {
                  var frequencyData = [
                        [
                            {
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

                  frequencyData = frequencyData.concat(Object.values(VOTING_DATA.voivodeships).map(function(voivodeship){
                      return [
                            voivodeship.voivodeshipCode,
                            voivodeship.frequencyPerc,
                            "<b>"+voivodeship.name+"</b>" +
                            "<p><b>Frekwencja: </b>&nbsp;"+voivodeship.frequencyPercStr+"</p>" +
                            "<p></p>" +
                            "<p><b>Uprawnionych: </b>&nbsp;"+voivodeship.allowedStr+"</p>" +
                            "<p><b>Wydanych kart: </b>&nbsp;"+voivodeship.cardsReleasedStr+"</p>"
                      ];
                  }));

                  var data = google.visualization.arrayToDataTable(frequencyData);

                  var options = {
                    region: 'PL',
                    resolution: 'provinces',
                    backgroundColor: 'transparent',
                    height: 500,
                    width: 500,
                    tooltip: {
                        isHtml: true
                    },
                    colorAxis: {
                        colors: ['#cecccc', '#754a4a']
                    }
                  };

                  var chart = new google.visualization.GeoChart(document.getElementById('frequency-map-chart'));

                  function clickRegion(eventData) {
                        var voivodeshipFullName = Object.values(VOTING_DATA.voivodeships).filter(function(voivodeship){
                            return voivodeship.voivodeshipCode == eventData.region;
                        })[0];
                        if(voivodeshipFullName) {
                            window.location = VOTING_DATA.voivodeshipSubpageUrl + voivodeshipFullName + '.html';
                        };
                  };
                  google.visualization.events.addListener(chart, 'regionClick', clickRegion);

                  chart.draw(data, options);
              } else if(!VOTING_DATA.divisionSubpageNo) {

                  var chartData = [
                    ['Okręg', 'Frekwencja', { role: 'style' }]
                  ];

                  chartData = chartData.concat(Object.keys(VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName].divisions).map(function(divisionNo, index){
                      return [
                          'Okręg '+divisionNo,
                          VOTING_DATA.divisions[divisionNo].frequencyPerc,
                          PIE_COLORS[index % 2]
                      ]
                  }));

                  var data = google.visualization.arrayToDataTable(chartData);

                  var view = new google.visualization.DataView(data);
                  //view.setColumns([0, 1]);

                  var options = {
                    title: 'Frekwencja',
                    width: 600,
                    height: 400,
                    backgroundColor: 'transparent',
                    bar: {groupWidth: '95%'},
                    legend: {
                        position: 'none'
                    }
                  };
                  var chart = new google.visualization.BarChart(document.getElementById('frequency-map-chart'));
                  chart.draw(view, options);
              } else if(!VOTING_DATA.communeSubpageName) {
                  var chartData = [
                    ['Gmina', 'Frekwencja', { role: 'style' }]
                  ];

                  chartData = chartData.concat(Object.keys(VOTING_DATA.divisions[VOTING_DATA.divisionSubpageNo].communes).map(function(communeName, index){
                      return [
                          communeName,
                          VOTING_DATA.communes[communeName].frequencyPerc,
                          PIE_COLORS[index % 2]
                      ]
                  }));

                  var data = google.visualization.arrayToDataTable(chartData);

                  var view = new google.visualization.DataView(data);
                  //view.setColumns([0, 1]);

                  var options = {
                    width: 830,
                    height: 500,
                    backgroundColor: 'transparent',
                    bar: {groupWidth: '95%'},
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


        self.__createMap = function() {

            var geojson = window.PlGeoMap;

            /*var context = d3.select('#frequency-map-chart')
                .node()
                .getContext('2d');

            var projection = d3.geoEquirectangular();

            var geoGenerator = d3.geoPath()
                .projection(projection)
                .context(context);

            projection.fitExtent([[0, -100], [400, 400]], geojson);
            //projection.translate([0, 0]);

            context.lineWidth = 0.5;
            context.strokeStyle = '#888';

            context.beginPath();
            geoGenerator({type: 'FeatureCollection', features: geojson.features})
            context.stroke();*/

            //var projection = d3.geoMercator()
            //    .scale(400)
            //    .translate([200, 280])
            //    .center([0, 5]);

            var projection = d3.geoEquirectangular();

            projection.fitExtent([[0, -100], [400, 400]], geojson);

            var geoGenerator = d3.geoPath()
                .projection(projection);

            function handleMouseover(d) {

                var pixelArea = geoGenerator.area(d);
                var bounds = geoGenerator.bounds(d);
                var centroid = geoGenerator.centroid(d);
                var measure = geoGenerator.measure(d);

                //d3.select('#frequency-map-chart .info')
                //    .text(d.properties.name + ' (path.area = ' + pixelArea.toFixed(1) + ' path.measure = ' + measure.toFixed(1) + ')');

            }


            var u = d3.select('#frequency-map-chart g.map')
                .selectAll('path')
                .data(geojson.features);

            u.enter()
                .append('path')
                .attr('d', geoGenerator)
                .on('mouseover', handleMouseover);


            $("#frequency-map-chart path").each(function() {
                var pathEl = $(this);
                pathEl.css('fill', 'rgb(151, 82, 89)');
                //pathEl.css('stroke-width', '1px');
                //pathEl.css('stroke', 'black');
            });

        };

        self.installLinkAtDOM = function(el) {
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
        };

        self.__installClickHooks = function() {

            var maputils = self;

            var toSearch = [];
            Object.keys(VOTING_DATA.search.voivodeships).forEach(function(voivodeshipName){
                toSearch.push({
                    textData: 'Województwo '+voivodeshipName,
                    label: voivodeshipName,
                    itemType: 'voivodeship',
                    name: voivodeshipName
                });
            });

            Object.keys(VOTING_DATA.search.divisions).forEach(function(divisionNo){
                toSearch.push({
                    textData: 'Okręg '+divisionNo,
                    label: 'Okręg '+divisionNo,
                    itemType: 'division',
                    name: divisionNo
                });
            });

            Object.keys(VOTING_DATA.search.communes).forEach(function(communeName){
                toSearch.push({
                    textData: 'Gmina '+communeName,
                    label: communeName,
                    itemType: 'commune',
                    name: communeName
                });
            });
            window.VOTE_DATA_SEARCH = toSearch;


            $('body > nav ul li input').each(function(){
                var self = $(this);
                var resultsList = self.parent().find('ol');
                var updatesRequested = 0;

                self.keypress(function(){
                    var content = self.val();
                    var results = [];

                    if(updatesRequested >= 2) {
                        return;
                    } else {
                        ++updatesRequested;
                    }

                    console.log('request fuzzy search');

                    results = fuzzysort.go(content, toSearch, {key: 'textData'}).slice(0, 15).map(function(result) {

                        var resultNode = $('<li></li>');
                        resultNode.text(result.obj.label);

                        if(result.obj.itemType == 'voivodeship') {
                            resultNode.data('link-voivodeship', result.obj.name);
                        } else if(result.obj.itemType == 'division') {
                            resultNode.data('link-division', result.obj.name);
                        } else if(result.obj.itemType == 'commune') {
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
            });

            $('body > nav ul li').each(function(){
                var self = $(this);
                var nestedList = self.find('ul');
                var nestedInput = self.find('input');
                var nestedResultList = self.find('ol');

                var isSelfHovered = false;
                var isNestedListHovered = false;
                var isNestedInputHovered = false;
                var isNestedResultListHovered = false;

                function updateHoverClasses() {
                  if(isSelfHovered || isNestedListHovered || isNestedInputHovered || isNestedResultListHovered) {
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

                nestedResultList.hover(function(){
                    isNestedResultListHovered = true;
                    updateHoverClasses();
                }, function(){
                    isNestedResultListHovered = false;
                    updateHoverClasses();
                });

                nestedInput.hover(function(){
                    isNestedInputHovered = true;
                    updateHoverClasses();
                }, function(){
                    isNestedInputHovered = false;
                    updateHoverClasses();
                });

                nestedList.hover(function(){
                    isNestedListHovered = true;
                    updateHoverClasses();
                }, function(){
                    isNestedListHovered = false;
                    updateHoverClasses();
                });

                self.hover(function(){
                    isSelfHovered = true;
                    updateHoverClasses();
                }, function(){
                    isSelfHovered = false;
                    updateHoverClasses();
                });

                updateHoverClasses();
            })

            $('[data-link-voivodeship],[data-link-division],[data-link-commune]').each(function(){
                self.installLinkAtDOM(this);
            });

            $('.results-table').each(function() {
                var table = $(this);
                table.find('th').each(function(i) {
                    var self = $(this);
                    var tableBody = table.find('tbody');
                    var sortingType = self.data('type') || 'string';
                    var sortingMode = self.data('mode') || 'toggle';

                    var castToType = function (type, value) {
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

                    (function (thIndex, type, mode) {
                        self.click(function () {
                            var currentMode = self.data('current-mode');
                            var sortedRows = tableBody.find('tr').sort(function (rowA, rowB) {
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
                    }(i, sortingType, sortingMode));
                });
            });

        };

        self.getSubpageRegionResolutionData = function() {
            if (VOTING_DATA.voivodeshipSubpageName) {
                return VOTING_DATA.voivodeships[VOTING_DATA.voivodeshipSubpageName];
            } else {
                return VOTING_DATA;
            }
        };

        self.__createChart = function() {


            var pieVotesConfigArray = [];

            Object.values(self.getSubpageRegionResolutionData().candidates).forEach(function(el, index){
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
        };
        return self;
    }
    var view = new ContentsView();
    view.init();
    window.contentsView = view;
})