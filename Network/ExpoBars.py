import sys, os
from multiprocessing import Process, Queue, cpu_count
from math import ceil
#from random import shuffle
from PIL import Image




def filterIDs(directory, count):
    """Loads subpop, removed comments and duplicates"""
    try:
        popfile = open(directory)
    except:
        print "Error: population file not found at", directory
        return 'error'
    ids = set()              
    line = 0
    while True:
            testline = popfile.readline()
            if len(testline) == 0:
                break
            if not testline.startswith("#"):
                ids.add(int(testline))
                line += 1
                
    idstemp =  sorted(list(ids))      
    print '\tSubpop', count, str(line), "entries with IDS", int(idstemp[0]), "through", int(idstemp[line-1]), "loaded"
    return ids




def loadSubpop(subpop, subPopDir, out_q, count, popSizeAll):
    """Subprocess, loads subpop with logical operators"""
    outDict = {}
    
    temp = filterIDs(subPopDir + subpop, count)
    if temp == 'error':
        outDict[subpop] = 'error'
        print "Terminating process due to error"
    else:
        outDict[subpop] = temp
        outDict[subpop + "_type"] = direct
            
    print "\t\tLoad complete, returning subpop", count

    out_q.put(outDict)
    
    
    
    
def getSubpops(script, subpopDir, popSize):
    """Host process, loads subpop with logical operators"""
    subpopFiles = {}
    subpopList = []
    out_q = Queue()
    processes = []
    for subpop in script:
        if subpop not in subpopList:
            subpopList.append(subpop)
    
    print "\nLoading subpop files:"
    count = 0
    for subpop in subpopList:
        count += 1
        p = Process(target = loadSubpop, args = (subpop, subpopDir, out_q, count, popSize))
        processes.append(p)
        p.start() 
    for subpop in subpopList:
        subpopFiles.update(out_q.get())
    for p in processes:
        p.join()
    print "Subpop loading complete"
    
    return subpopFiles, subpopList
    
    
    
    
def prepPiece(socialNetPiece, outPut):
    """Formats social net piece & uniquifies"""
    if outPut == 'direct':
        collected = dict()
        for entry in socialNetPiece:
            key = entry[0]+' '+entry[1]+' '+entry[2]+' '+entry[3]
            if key not in collected.keys():
                collected[key] = entry[4]
            else:
                collected[key] += entry[4]
    else:
        collected = dict()
        for entry in socialNetPiece:
            key = entry[0]+entry[2]
            if key not in collected.keys():
                collected[key] = entry[4]
            else:
                collected[key] += entry[4]
    return collected




def mergePieces(pieces,fileName):
    """Merges and uniquifies several social net pieces"""
    collected = dict()
    merged = []
    axes = set()
    #print pieces
    numKeys = len(pieces.values()[0].keys())
    if numKeys == 2:
        for piece in pieces.values():
            for key in piece.keys():
                splitKey = key.split()
                axes.add(splitKey[0])
                axes.add(splitKey[1])
                if key not in collected:
                    collected[key] = piece[key]
                else:
                    collected[key] += piece[key]
    else:
        for piece in pieces.values():
            for key in piece.keys():
                splitKey = key.split()
                axes.add(splitKey[0])
                axes.add(splitKey[2])
                if key not in collected:
                    collected[key] = piece[key]
                else:
                    collected[key] += piece[key]
    
    maxima = max(collected.values())
    
    makeImage(sorted(list(axes)),collected,maxima,fileName)
    
    sortedKeys = sorted(collected.keys())
    for key in sortedKeys:
        merged.append(key+' '+collected[key])
    return merged, max(collected.values())




def isInSubpops(ID, subpopList, subpopFiles):
    """Checks if an ID is in the target subpop(s)"""
    found = False
    ID = int(ID)
    for subpop in subpopList:
        if (ID in subpopFiles[subpop]) == subpopFiles[subpop+'_type']:
            found = True
            break
    return found
           
            
              

def prepNet(socialNetPiece, subpopList, subpopFiles, outPut, out_q, core):
    """Filters & prepares one piece of the social net"""
    outDict = dict()
    
    print "Core", core, "preparing to format", len(socialNetPiece), "entries"
    socialNetPiece = [entry.replace('\n','').split(' ') for entry in socialNetPiece if not entry.startswith('#') and len(entry) > 2]
    print "Core", core, "formating complete, preparing to filter by subpop membership"
    socialNetPiece = [entry for entry in socialNetPiece if isInSubpops(entry[0],subpopList,subpopFiles) and isInSubpops(entry[2],subpopList,subpopFiles)]
    
    print "Core", core, "filtering complete,", len(socialNetPiece), "entries remaining, arranging for parsing"
    for pos in range(len(socialNetPiece)):
        if int(socialNetPiece[pos][0]) > int(socialNetPiece[pos][2]):
            socialNetPiece[pos][0],socialNetPiece[pos][2] = socialNetPiece[pos][2],socialNetPiece[pos][0]
    print "Core", core, "rearrange complete, preparing to uniquify.."
    socialNetPiece = prepPiece(socialNetPiece, outPut)
    print "Core", core, "all tasks complete, returning for compilation"
    
    outDict[core] = socialNetPiece
    
    out_q.put(outDict)
      

    
def vegasShuffle(listed):
    """Rapid shuffle to reduce block heterogeneity"""
    if len(listed)%2:
        listed.append("#null")
    stackOne = listed[:len(listed)/2]
    stackTwo = listed[len(listed)/2:]
    listed[::2] = stackOne
    listed[1::2] = stackTwo
    return listed
    
    
def loadSocialNet(socialNetFile, subpopList, subpopFiles, outPut, fileName):
    """Generates target net for output from social net"""
    print "\nLoading social net file..."
    fileIn =  open(socialNetFile,'r')
    socialNetLoaded =  fileIn.readlines()
    print "Shuffling..."
    socialNetLoaded = vegasShuffle(socialNetLoaded)    
    print "Raw social net entries:", len(socialNetLoaded)
    print "Filtering social net...\n"
    
    length0 = len(socialNetLoaded)
    
    cores = max(cpu_count() - 1,1)
    out_q = Queue()
    block =  int(ceil(length0/float(cores)))
    processes = []
    
    for i in range(cores):
        p = Process(target = prepNet, args = (socialNetLoaded[block*i:block*(i+1)], subpopList, subpopFiles, outPut, out_q, i))
        processes.append(p)
        p.start() 
    merged = {}
    for i in range(cores):
        merged.update(out_q.get())
    for p in processes:
        p.join()
    
    print "All subprocesses complete, preparing to merge..."
    targetNet,maxima = mergePieces(merged, fileName)
    print "Filtered social net entries:", len(targetNet)
    
    return targetNet
    
    
    

def makeImage(axes,collected,maxima,fileName):
    """Generates and saves image"""
    numIDs = len(axes)
    references = dict(zip(axes, range(numIDs)))
    pointList = []
    print maxima
    
    img = Image.new('L',(numIDs,numIDs), "black")
    pixels = img.load()
    greyRange = 255
    
    
    if len(collected.keys()[0].split()) == 3:
        for key, item in collected.iteritems():
            splitKey = key.split(' ')
            x = references[splitKey[0]]
            y = references[splitKey[1]]
            c = int(greyRange*(float(item)/float(maxima)))
            pointList.append({'x':x,'y':y,'c':c})
    else:
        for key, item in collected.iteritems():
            splitKey = key.split(' ')
            x = references[splitKey[0]]
            y = references[splitKey[2]]
            c = int(greyRange*(float(item)/float(maxima)))
            pointList.append({'x':x,'y':y,'c':c})
            
    for point in pointList:
        #print point
        for item in point.values():
            #print item,type(item)
            pixels[point['x'],point['y']] = point['c']
            pixels[point['y'],point['x']] = point['c']
    
    img.show()
    img.save(fileName+'.png')

            
                
                        
def main():
    """Main file execution"""
    if len(sys.argv) == 4:
        sys.argv[0] = ''
        sys.argv = [''] + sys.argv
    print sys.argv
    subpopDir = sys.argv[1]
    socialNetFile = sys.argv[2]
    outFile = sys.argv[3].replace('.txt','')
    script = sys.argv[4].split(',')
    
    outPut = "direct"
    
    try:
        outPut = sys.argv[5]
    except:
        None

    if type(script) is str:
        script = [script]
    print script    
    
    subpopFiles, subpopList = getSubpops(script, subpopDir, 0)
    
    print "subpops loaded\n"
    
    print subpopList
    for key in subpopList:
        print key, len(subpopFiles[key]), subpopFiles[key+'_type']
     
    targetNet = loadSocialNet(socialNetFile, subpopList, subpopFiles, outPut, outFile)
    
    print "Writing contents to file:", outFile
    fileOut = open(outFile+'.txt','w')
    
    for line in targetNet:
        fileOut.write("%s\n" % line)
    
    fileOut.close()
    
    print "operation complete, quitting now"
    quit()
    







main()
