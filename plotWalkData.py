import os
from tcxreader.tcxreader import TCXReader
import folium
import folium.plugins
import math
from branca.element import Template

# import bokeh items
import bokeh.models as models
import bokeh.plotting as plotting
import bokeh.embed as embed

##################################################################
### PROCESSING AND PATH PARAMETERS
##################################################################


# base data folder
dataFolder = 'data'

# year to plot
year = 2024

# find all data files
dataFiles = []
for file in os.listdir(os.path.join(dataFolder, str(year))):
    dataFiles.append(os.path.join(dataFolder, str(year), file))

# specify how many tracks to include
#endIndex = 10 # for testing, only use first
endIndex = len(dataFiles) # all tracks

# heat map downsample rate - reduce number of points to reduce file size
hmDownsample = 10
trackDownsample = 2

# map display parameters
mapHeight = 600 # px
mapWidth = 1200 # px
popupMaxWidth = 400 # px

# plot display paramters
plotHeight = 600
plotWidth = 1200

##################################################################
### Load and process data
##################################################################

# load in data
reader = TCXReader()
dataSets = []
for iii in range(0, endIndex):
    print('Loading track ' + str(iii) + ' of ' + str(len(dataFiles)))
    dataSets.append(reader.read(dataFiles[iii]))
    
# create list of data points
hmData = []
tracks = []
infos = []
dates = []
distances = []
for iii in range(0, endIndex):
    print('Merging track ' + str(iii) + ' of ' + str(len(dataSets)))
    
    # extract track data points
    track = []
    for point in dataSets[iii].trackpoints:
        track.append([point.latitude, point.longitude])
        
    # append to to full list (in downsampled format) for heat map
    hmData += track[0::hmDownsample]
    # store track for individual plotting
    tracks.append(track[0::trackDownsample])
    
    # track dates and distances
    dates.append(dataSets[iii].start_time)
    distances.append(dataSets[iii].distance/1000)
    
    # extract info
    text = 'Description: ' + os.path.basename(dataFiles[iii]).replace('.tcx', '') + '<br>'
    text += 'Date: ' + dataSets[iii].start_time.strftime('%d-%b-%Y') + '<br>'
    text += 'Distance: ' + str(round(dataSets[iii].distance/1000, 2)) + 'km<br>'
    hours = math.floor(dataSets[iii].duration/60/60)
    minutes = math.floor((dataSets[iii].duration - hours * 60 * 60) / 60)
    seconds = round(dataSets[iii].duration - hours * 60 * 60 - minutes * 60, 1)
    text += 'Duration: ' + str(hours) + 'h:' + str(minutes) + 'm:' + str(seconds) + 's<br>'
    text += 'Average Speed: ' + str(round(dataSets[iii].distance/1000 / (dataSets[iii].duration/60/60), 2)) + 'kmph'
    infos.append(text)

# post process distances for plotting
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
monthDist = [0 for m in months]
weeks = list(range(1, 53))
weekDist = [0 for w in weeks]

for iii in range(0, len(dates)):
    month = dates[iii].month
    week = dates[iii].isocalendar().week
    
    # add to month and week distance trackers
    monthDist[month - 1] += distances[iii]
    weekDist[week - 1] += distances[iii]

# calculate cumulative distances
monthCumulative = [monthDist[0]]
for iii in range(1, len(months)):
    monthCumulative.append(monthCumulative[-1] + monthDist[iii])
weekCumulative = [weekDist[0]]
for iii in range(1, len(weeks)):
    weekCumulative.append(weekCumulative[-1] + weekDist[iii])
    
##################################################################
### Create plots
##################################################################

# create monthly plot
dataDict = {'month' : months,
            'distance' : monthDist,
            'cumulative' : monthCumulative,
            }
source = models.ColumnDataSource(data = dataDict)

monthPlot = plotting.figure(x_range=models.FactorRange(*months), height=plotHeight, 
                            width=plotWidth, tools="hover", 
                            tooltips=[('Month', '@month'),
                                      ('Month Distance', '@distance'),
                                      ('Cumulative', '@cumulative'),
                                      ],
                            title = 'Monthly Plot',
                            x_axis_label="Month",
                            y_axis_label="Distance (km)",
                            )

b = monthPlot.vbar(x="month", top="distance", source=source, width=0.8,
                   line_color=None, legend_label='Monthly Distance')
monthPlot.y_range.renderers = [b]
monthPlot.extra_y_ranges = {"yCum": models.DataRange1d()}
monthPlot.add_layout(models.LinearAxis(y_range_name="yCum", axis_label='Cumulative Distance (km)'), 'right')
monthPlot.line(x="month", y="cumulative", source=source, color='black', line_width=2,
               legend_label='Cumulative Distance', y_range_name="yCum")
monthPlot.scatter(x="month", y="cumulative", source=source, size=5, fill_color = "black",
                  line_color="black", legend_label='Cumulative Distance', y_range_name="yCum")
monthPlot.add_layout(monthPlot.legend[0], 'right')

# create weekly plot
dataDict = {'week' : weeks,
            'distance' : weekDist,
            'cumulative' : weekCumulative,
            }
source = models.ColumnDataSource(data = dataDict)

weekPlot = plotting.figure(height=plotHeight, 
                            width=plotWidth, tools="hover", 
                            tooltips=[('Week', '@week'),
                                      ('Week Distance', '@distance'),
                                      ('Cumulative', '@cumulative'),
                                      ],
                            title = 'Weekly Plot',
                            x_axis_label="Week Number",
                            y_axis_label="Distance (km)",
                            )

b = weekPlot.vbar(x="week", top="distance", source=source, width=0.8,
                  line_color=None, legend_label='Weekly Distance')
weekPlot.y_range.renderers = [b]
weekPlot.extra_y_ranges = {"yCum": models.DataRange1d()}
weekPlot.add_layout(models.LinearAxis(y_range_name="yCum", axis_label='Cumulative Distance (km)'), 'right')
weekPlot.line(x="week", y="cumulative", source=source, color='black', line_width=2,
               legend_label='Cumulative Distance', y_range_name="yCum")
weekPlot.scatter(x="week", y="cumulative", source=source, size=5, fill_color = "black",
                  line_color="black", legend_label='Cumulative Distance', y_range_name="yCum")
weekPlot.add_layout(weekPlot.legend[0], 'right')

##################################################################
### Create map
##################################################################

# create map view of all walks
m = folium.Map([48.0, 5.0], zoom_start=6)

# heat map based on all data
folium.plugins.HeatMap(hmData, name="Heat Map",
                       min_opacity = 0.5,
                       radius = 15,
                       ).add_to(m)

# Edit ployline behaviour to change color on hover
templateText = \
"""
            {% macro script(this, kwargs) %}
                var {{ this.get_name() }} = L.polyline(
                    {{ this.locations|tojson }},
                    {{ this.options|tojson }}
                    )

                {{ this.get_name() }}.on('mouseover', function(e) {
                    var layer = e.target;

                    layer.setStyle({
                        color: 'magenta',
                        opacity: 1,
                        weight: 2
                    });
                    
                    layer.bringToFront();
                });
                
                {{ this.get_name() }}.on('popupopen', function(e) {
                    var layer = e.target;

                    layer.setStyle({
                        color: 'magenta',
                        opacity: 1,
                        weight: 2
                    });
                    
                    layer.bringToFront();
                });
                
                {{ this.get_name() }}.on('mouseout', function(e) {
                    var layer = e.target;
                    
                    if (!layer.isPopupOpen()){
                        layer.setStyle({
                            color: 'black',
                            opacity: 1,
                            weight: 2
                        });
                    }
                });
                
                {{ this.get_name() }}.on('popupclose', function(e) {
                    var layer = e.target;

                    layer.setStyle({
                        color: 'black',
                        opacity: 1,
                        weight: 2
                    });
                });
                
                {{ this.get_name() }}.addTo({{this._parent.get_name()}});
            {% endmacro %}
"""

trackGroup = folium.FeatureGroup(name="Tracks").add_to(m)
for iii in range(0, len(tracks)):
    track = tracks[iii]
    
    # create line object
    line = folium.PolyLine(
        locations=track,
        color="black",
        weight=2,
        tooltip=infos[iii],
        popup=folium.Popup(infos[iii], max_width=popupMaxWidth),
    )
    # update template to add hover behaviour
    line._template = Template(templateText)
    
    # add line to track group - this will show as single item in legend
    line.add_to(trackGroup)

# add legend and layer selection
folium.LayerControl().add_to(m)

# fit map to data, this adjusts default zoom
m.fit_bounds(m.get_bounds(), padding=(30, 30))

##################################################################
### Create HTML Doc
##################################################################

# set map to display in an iframe with set width and height
m.get_root().width = str(mapWidth) + "px"
m.get_root().height = str(mapHeight) + "px"
iframe = m.get_root()._repr_html_()

# prepare for embedding bokeh plots
plotDict = {'monthPlot' : monthPlot,
            'weekPlot' : weekPlot,
            }
            
script, divs = embed.components(plotDict)

htmlText  = """
<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="w3.css">
        <link rel="stylesheet" href="sidebar.css">
        
        <script src="https://cdn.bokeh.org/bokeh/release/bokeh-3.6.2.min.js"
            crossorigin="anonymous">
        </script> """ +\
        script +\
        """
    </head>
    
    <style>
        .content {
            max-width: """ + str(max(plotWidth, mapWidth)) + """px;
            margin: auto;
        }
    </style>

    <body>
        <!-- Side navigation -->
        <div class="sidenav">
          <a href="#notes">Notes</a>
          <a href="#map">Map</a>
          <a href="#plots">Plots</a>
          <a href="#nerds">For Nerds</a>
        </div>
        
        <div class="main">
            <h1 id="notes">Notes</h1>
                <p>In the first few months of 2024, I decided that I would like to try and walk 1000km in 2024.
                This included only "going out for a walk", so not just distance walked around at work, walking
                to the pub, lunchtime walks at work, etc. I tracked all the activities that I wanted to count
                and have plotted the results here. This ended up being a bit of a Britain farewell tour as at
                the beginning of 2025 I left the UK for a new adventure. In the end, I logged <b>
                """ + str(round(max(monthCumulative), 1)) + """km </b> of walking/hiking in 2024!
                </p>
                <p>Walks included significant sections of the following notable long distance paths:</p>
                <ul>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Macmillan+Way+-+Shakespeare%27s+Way" target="_blank">Shakespeare's Way</a>
                        section from Stratford-upon-Avon to Maidensgrove.
                        <ul>
                            <li>This was a group walk spread across 2024 with the 
                                <a href="https://www.chilterns2030s.org.uk/" target="_blank">Chiltern Young Walkers</a> Ramblers group
                            </li>
                            <li>Due to timings and other commitments, I missed the sections from Maidensgrove to Shakespeare's Globe in London</li>
                        </ul>
                    </li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=ridgeway+national+trail" target="_blank">The Ridgeway Nation Trail</a>
                        from Goring to Ivinghoe Beacon.
                        <ul>
                            <li>I had done the first half of the trail between Christmas 2023 and New Years 2024</li>
                            <li>Due to foot issues, the second half was left for 2024</li>
                            <li>This was a solo walk, the complete 138.5km was completed in two outings over 4 days</li>
                        </ul>
                    </li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Oxford+Green+Belt+Way" target="_blank">Oxford Green Belt Way<a>
                        <ul>
                            <li>This was largely a solo walk split over many days starting and ending at home</li>
                            <li>The entire route was completed, however I roughly doubled the distance by starting and ending at home!</li>
                        </ul>
                    </li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Hadrian%27s+Wall+Path+National+Trail" target="_blank">Hadrian's Wall Path National Trail</a>
                        <ul>
                            <li>Some sections in the middle, more interesting section of the trail</li>
                            <li>This was done over two visits, one with Mary and one with my Mom & brother</li>
                        </ul>
                    </li>
                </ul>
                <p>Some short section of other long distance paths were also explored as a section of a shorter walk, these included:</p>
                <ul>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Offa%27s+Dyke+Path+National+Trail" target="_blank">Offa's Dyke Path National Trail</a></li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Beacons+Way+%28Brecon%29" target="_blank">Beacons Way (Brecon)</a></li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Cambrian+Way" target="_blank">Cambrian Way</a></li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=White+Horse+Trail" target="_blank">White Horse Trail</a></li>
                    <li><a href="https://ldwa.org.uk/ldp/members/show_path.php?path_name=Pennine+Way+National+Trail" target="_blank">Pennine Way National Trail</a></li>
                    <li>And probably others I have forgotten...</li>
                </ul>
                <p>Notes on functionality:</p>
                <ul>
                    <li>Hovering over a track on the map will give more information.</li>
                    <li>Hovering over a track will also bring it to the front of the map and highlight it.</li>
                    <li>Clicking a track will keep the popup visible.</li>
                    <li>The heat map or tracks can be hidden in the layer control at the top right of the map.</li>
                    <li>In the plot section, hovering over lines will give more information.</li>
                </ul>
            <h1 id="map">Map of Walks</h1>\n\t\t""" + \
                iframe + "\n" + \
            """<h1 id="plots">Data Plots</h1>\n""" + \
                "\t\t" + divs['monthPlot'] + "\n" + \
                "\t\t" + divs['weekPlot'] + "\n" + \
"""         <h1 id="nerds">Info for Nerds</h1>
                <p>This section has a bit of info about how this page was made</p>
                <ul>
                    <li>Data was tracked in MapMyRun as I had used this previously. 
                        Any tracking that allows Garmin TCX files to be exported is compatible.
                    </li>
                    <li>I wrote a python script to download all data from my MapMyRun account following the process here:
                        <a href="https://www.reddit.com/r/running/comments/16p743j/download_all_tcx_running_history_from_mapmyrun/?rdt=65271" target = "_blank">Reddit: Download All TCX Running History from Mapmyrun</a>
                    </li>
                    <li>I was too lazy to write my own TCX parser, so I used this
                        <a href="https://pypi.org/project/tcxreader/0.3.12/" target="_blank">TCXReader Module</a>
                    </li>
                    <li>Maps are created using <a href="https://python-visualization.github.io/folium/latest/index.html" target="_blank">Folium</a>
                        <ul>
                            <li>Some customisation was required to get track behaviour to work how I wanted it</li>
                            <li>This requires writing javascript to interact with the <a href="https://leafletjs.com/" target="_blank">LeafletJS</a> that folium generates</li>
                        </ul>
                    </li>
                    <li>Plots are generate using <a href="https://docs.bokeh.org/en/latest/index.html" target="_blank">Bokeh</a>
                        <ul>
                            <li>I had used bokeh quite a lot for work in the past</li>
                            <li>Functionality here is very basic, it would probably be possible to link between bokeh and leaflet on the JS side if I cared to figure it out.</li>
                        </ul>
                    </li>
                </ul>
        </div>
    </body>
</html>
"""

with open('test.html', 'w') as f:
    f.write(htmlText)

# not used - for debug only. Old method of saving fullscreen map

# full screen map    
#m.save('test.html')

#tmp = reader.read(file)
#print(tmp.trackpoints[-1].longitude)
# print(script)