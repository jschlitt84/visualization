import pandas as pd
import os
import subprocess

from time import sleep

def makeTimeLine(inFile,
                name='default',
                embed='media',
                sort='place',
                placeLevel = 1,
                keep = 'null',
                keepStyle = 'direct'):
    
    outFile = 'timeLineTemp.csv'
    
    if embed == 'media':
        contentCol = 'media1_display_url'
        mediaCol = 'media1_media_url_https'
    else:
        contentCol = 'link1'
        mediaCol = 'link1'

    
    if type(inFile) is str:
        data =  pd.DataFrame.from_csv(inFile,index_col='id')
    elif type(inFile) is dict:
        data = inFile['data']
    else:
        data = inFile
        
    fileOut = open(outFile,'wb')
    newKeys = 'date,display_date,description,link,series,html\n'
    
    fileOut.write(newKeys)
    
    print "Generating new csv as", outFile
    
    for index, row in data.iterrows():
        date = row['created_at']
        displayDate = ' '.join([entry for entry in row['created_at'].split() if not entry.startswith('+')])
        description = '<b>Text:</b> '+' '.join(row['text'].split())
        try:
            description += '<br><b>Location:</b> '+str(row['place'])
        except:
            None
        try:
            description += '<br><b>Retweets:</b> '+str(row['retweet_count'])
        except:
            None
        try:
            description += '<br><b>Favorites:</b> '+str(row['favorite_count'])
        except:
            None
        
        link = row[contentCol]; media = row[mediaCol]
        
        if not link.startswith('http') and str(link).lower() != 'false':
            link = 'https://'+link
        if not media.startswith('http') and str(media).lower() != 'false':
            media = 'https://'+media
            
        series = row[sort]
        
        if sort == 'place':
            series = str(series).split(', ')[-placeLevel]
            
        inKeep = ((series in keep) == (keepStyle == 'direct')) or keep == 'null'
        
        if embed == 'media':    
            html = "<img src='%s'>" % media
        else:
            html = "<iframe width='800' height='600' src='%s'></iframe>" % media
            
        cleaned = lambda x: str(x).replace(',','').replace('"','').replace("'",'')
        content = [date,displayDate,description,link,series]
        content = [cleaned(item) for item in content]
        content.append(html)
        lens = [len(str(item)) for item in content]
        
        if str(link).lower() != 'false' and min(lens) != 0 and inKeep:
            fileOut.write("%s,%s,%s,%s,%s,%s\n" % tuple(content))
            
    fileOut.close(); sleep(1)
    
    outDir = 'TimeLine'+name
    
    command = "timeline-setter -c %s -o %s -O" % (outFile,outDir)
    
    print "Running timeline-setter"

    process = subprocess.Popen(command, shell=True)
    output = process.communicate()[0]
    
    fileDirect = os.getcwd()+'/'+outDir+'/timeline.html'
    
    print "Operation complete, timeline available at:",fileDirect
    
    return fileDirect