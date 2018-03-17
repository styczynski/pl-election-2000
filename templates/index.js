
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
        var sectionsNavList = $(".sections > ul");
        self.displayedIndex = 0;
        self.sections = [];
        self.switchTo = function changeContentView(index) {
            console.log("! Switch to "+index)
            self.displayedIndex = index;
            $(".content-view").children().appendTo("main");
            $($("main section.section-"+index)).appendTo($(".content-view"));
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
                'packages':['geochart'],
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
                geoJson: "{{assets}}/powiaty.geojson",
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

              if(MARKED_VOIVODESHIP_NAME) {
                  var voivodeshipCode = VOIVODESHIP_CODES[MARKED_VOIVODESHIP_NAME];
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

                    var voivodeshipFullName = Object.keys(VOIVODESHIP_CODES).filter(function(key){
                        return VOIVODESHIP_CODES[key] == eventData.region;
                    })[0];

                    if(voivodeshipFullName) {
                        window.location = VOIVODESHIP_SUBPAGE_URL + voivodeshipFullName + '.html';
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

                  if (distanceY > shrinkOn) {
                    mapElement.addClass('minimized');
                  } else {
                      mapElement.removeClass('minimized');
                  }
              }

              chart = new google.visualization.GeoChart(document.getElementById('main-map-chart'));

              google.visualization.events.addListener(chart, 'regionClick', clickRegion);
              google.visualization.events.addListener(chart, 'ready', chartReady);


              window.addEventListener('scroll', pageScrolled);


              chart.draw(data, options);

        };

        self.__createGeoMap = function() {

              var data = google.visualization.arrayToDataTable(VOTE_DATA_FREQUENCY);

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
                    var voivodeshipFullName = Object.keys(VOIVODESHIP_CODES).filter(function(key){
                        return VOIVODESHIP_CODES[key] == eventData.region;
                    })[0];
                    if(voivodeshipFullName) {
                        window.location = VOIVODESHIP_SUBPAGE_URL + voivodeshipFullName + '.html';
                    };
              };
              google.visualization.events.addListener(chart, 'regionClick', clickRegion);

              chart.draw(data, options);

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
        self.__installClickHooks = function() {
            $('.results-table.voting-frequency tr').click(function() {
                var self = $(this);
                var voivodeshipFullName = self.data('voivodeship');

                if (VOIVODESHIP_CODES[voivodeshipFullName]) {
                    window.location = VOIVODESHIP_SUBPAGE_URL + voivodeshipFullName + '.html';
                }

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
        self.__createChart = function() {


            var pieVotesConfigArray = [];
            VOTES_PER_CANDIDATE.forEach(function(el, index){
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