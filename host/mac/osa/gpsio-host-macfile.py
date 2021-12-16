#!/usr/bin/python3

# these are the gpsio functions that require removable volume access on a mac,
#  so this script should be called from a Terminal from osascript

# syntax:
# gpsio-host-macfile.py scan <gpxdir> <outfile>
# gpsio-host-macfile.py cpLocal <targetDir> <file> ...
# gpsio-host-macfile.py both <gpxdir> <targetDir> <options>
#   options is a json string as in gpsio-host.py

import os
import sys
import shutil
import json
import time

def scan(gpxdir,outfile):
    j={}
    for root, dirs, files in os.walk(gpxdir):
        for file in files:
            if file.upper().endswith(".GPX") and not(file.startswith(".")):
                fullpath=os.path.join(root,file)
                j[fullpath]={
                    'time':os.path.getmtime(fullpath),
                    'size':os.path.getsize(fullpath)}
    with open(outfile,'w') as f:
        json.dump(j,f,indent=3)

def cpLocal(targetDir,*flist):
    for f in flist:
        shutil.copy2(f,targetDir)

def both(gpxdir,targetDir,options):
    shutil.rmtree(targetDir,ignore_errors=True)
    os.makedirs(targetDir,exist_ok=True)
    options=json.loads(options)
    jsonfile=targetDir+'/gpxfiles.json'
    jsonfiletmp=jsonfile+'.tmp'
    scan(gpxdir,jsonfiletmp) # renamed to .json at the very end
    with open(jsonfiletmp,'r') as jf:
        j=json.load(jf)
    gpx_files=j.keys()
    timeDict={}
    for k in gpx_files:
        timeDict[k]=j[k]['time']
    gpx_files=sorted(gpx_files,key=timeDict.__getitem__,reverse=True)
    totalFileCount=len(gpx_files)
    print('sorted gpx_files:'+str(gpx_files))


    # apply file filtering as specified in the extension options
    if "method" in options:
        if options["method"]=="recent" and "recentSel" in options:
            # only get files m thru n (both are one-based) from the sorted list
            #  (set m=1 by default; not currently specified in the options;
            #    leave it here for forward compatibility using 'recentSelFirst')
            m=1
            if "recentSelFirst" in options:
                m=int(options["recentSelFirst"])
            n=int(options["recentSel"])

            # make sure 1<=n<=totalFileCount
            n=max(1,min(n,totalFileCount))
            # then make sure 1<=m<=n
            m=max(1,min(m,n))
            
            print("Selecting files "+str(m)+" thru "+str(n)+" from a reverse-chronological-order sorted list...")
            gpx_files=gpx_files[m-1:n]
            
        if options["method"]=="time" and "timeSel" in options:
            currentTime=time.time()
            print("Filtering out files older than "+options["timeSel"]+" hours...")
            gpx_files=[f for f in gpx_files if (currentTime-j[f]['time'])/3600<int(options["timeSel"])]    

    if "size" in options:                
        if options["size"]==True and "sizeSel" in options:
            print("Filtering out files larger than "+options["sizeSel"]+"...")
            # as long as sizeSel is in the format of <n>kb or <n>mb (case does not matter)
            #  then the following line will filter correctly, i.e. '10kB' or '5MB'
            gpx_files=[f for f in gpx_files if (j[f]['size']<eval(options["sizeSel"].lower().replace("kb","*1024").replace("mb","*1048576")))]

    print('final gpx_files:'+str(gpx_files))
    cpLocal(targetDir,*gpx_files)
    os.rename(jsonfiletmp,jsonfile) # do this at the very end to signal that the target dir is fully populated


if len(sys.argv)<4:
    sys.exit("ERROR: must specify at least three arguments.  Aborting.")
if sys.argv[1]=='scan':
    scan(sys.argv[2],sys.argv[3])
elif sys.argv[1]=='cpLocal':
    cpLocal(sys.argv[2],sys.argv[3:])
elif sys.argv[1]=='both':
    both(sys.argv[2],sys.argv[3],sys.argv[4])
else:
    sys.exit("ERROR: first argument must be 'scan' or 'cpLocal'.  Aborting.")