import operator
import urllib

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from random import shuffle, sample
from datetime import timedelta
from dateutil import parser
from matplotlib.dates import DateFormatter, date2num, num2date
from copy import deepcopy
from time import sleep

from CGVis import *
from mpl_toolkits.basemap import Basemap, cm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.animation as animation

ebolaData = {'name':'Ebola Tracker',
             'file':"/Users/jamesschlitt/visualization/ChatterGrabberVis/ebolaTracker_CollectedTweets.csv",
             'cats':'null'}

africaBox = {'lat1':-35.1,'lat2':38.9,'lon1':-18.3,'lon2':51.7}

allData = {ebolaData['name']:ebolaData}

for exp in allData.keys():
    allData[exp]['data'] = pd.DataFrame.from_csv(allData[exp]['file'],index_col='id')
    
def mapSubject(box,dataset,subject,level,binCts,call):
    if call == 'animate':
        plt.clf()
    else:
        fig = plt.figure(figsize=(10,10))
        
        
    if box == 'tight':
        box = {'lat1':min(dataset['data']['lat']),
               'lat2':max(dataset['data']['lat']),
               'lon1':min(dataset['data']['lat']),
               'lon2':max(dataset['data']['lon'])}
        
    mapped = Basemap(projection='mill', 
                     llcrnrlon=box['lon1'],
                     llcrnrlat=box['lat1'],
                     urcrnrlon=box['lon2'],
                     urcrnrlat=box['lat2'])
    
    lats = dataset['data']['lat']
    lons = dataset['data']['lon']
    times = dataset['data']['created_at']
    
    # ######################################################################
    # bin the epicenters (adapted from 
    # http://stackoverflow.com/questions/11507575/basemap-and-density-plots)
    latCt = binCts[0]
    lonCt = binCts[1]
    lon_bins = np.linspace(box['lon1'], box['lon2'], lonCt+1)
    lat_bins = np.linspace(box['lat1'], box['lat2'], latCt+1)
        
    density, _, _ = np.histogram2d(lats, lons, [lat_bins, lon_bins])
    
    # Turn the lon/lat of the bins into 2 dimensional arrays ready
    # for conversion into projected coordinates
    lon_bins_2d, lat_bins_2d = np.meshgrid(lon_bins, lat_bins)
    
    # convert the bin mesh to map coordinates:
    xs, ys = mapped(lon_bins_2d, lat_bins_2d) # will be plotted using pcolormesh
    # ######################################################################
            
    plt.pcolormesh(xs, ys, density, cmap = 'YlOrRd')

    mapped.drawcoastlines()
    mapped.drawstates()
    mapped.drawcountries()
    parallels = np.arange(-90.,90.,5.)
    mapped.drawparallels(parallels,labels=[1,0,0,0],fontsize=10)
    meridians = np.arange(-180.,180.,5.)
    mapped.drawmeridians(meridians,labels=[0,0,0,1],fontsize=10)
    x, y = mapped(lons, lats) # compute map proj coordinates.
    mapped.plot(x, y, 'o', markersize=4,zorder=6, markerfacecolor='r',markeredgecolor="none", alpha=0.25)
    
    title = '%s search for "%s", %s Related Tweets Found from\n%s to %s' % (dataset['name'],
                                                                            subject,
                                                                            len(dataset['data']),
                                                                            times[0],
                                                                            times[-1])
    plt.title(title)
    
    divider = make_axes_locatable(plt.gca())
    cax = divider.append_axes("right", "5%", pad="3%")
    cbar = plt.colorbar(orientation='vertical',cax=cax)
    if level != 'full':
        plt.clim([0,level])
    cbar.set_label('Number of Tweets')
    
    if call != 'animate':
        plt.show()
    return plt
    
    
def getDays(dataSet):
    days = dataSet['data']['date']
    return days.unique()


def animateMap(box,dataSet,subject,level,binCts):
    days = getDays(dataSet)
    length = len(days)
    plots = []; daySubs = []
    
    daySubs = [getFieldSub(dataSet,[day],[],day,'date') for day in days]
    for item in daySubs:
        print len(item['data'])
    
    if box == 'tight':
        box = {'lat1':min(dataSet['data']['lat']-.5),
               'lat2':max(dataSet['data']['lat']+.5),
               'lon1':min(dataSet['data']['lon']-.5),
               'lon2':max(dataSet['data']['lon']+.5)}

    fig = plt.figure(figsize=(10,10))
    
    def animate(i):
        mapSubject(box,daySubs[i],subject,level,binCts,'animate')
    
    #anim = animation.FuncAnimation(fig,animate,frames=length, interval=length, blit=False)
    anim = animation.FuncAnimation(fig,animate, frames=length, blit=False)
    anim.save('test.gif', writer='imagemagick', fps=1)
    #plt.show()
    return anim
    
        
a = getLocSub(ebolaData,['guinea','sierra leone','liberia'],['equatorial guinea','guinea-bissau'],'First Afflicted')
print "DEBOOO\n\n"
checkLinks(a['data'],linkfreq=1)
print "DEBOOO\n\n"
checkLinks(a['data'],linkfreq=2)
print "DEBOOO\n\n"
checkLinks(a['data'],linkfreq=3)
#print len(getLocSub(ebolaData,['guinea','sierra leone','liberia'],['equatorial guinea'],'First Afflicted')['data'])
#print len(getLocSub(ebolaData,['guinea','sierra leone','liberia'],[],'First Afflicted')['data'])
