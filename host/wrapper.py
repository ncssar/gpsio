#!/usr/bin/env python

# wrapper.py - gpsio Python script to communicate with GPSBabel;
#  output from this wrapper script is sent over stdio to background.js

# In Linux, this file is executable and can be called directly;
#  in Windows, this file must be called from wrapper.bat,
#  which is registered in nmh_manifest.json
#
# stdin and stdout from this code will communicate directly with
#  GPSBabel and background.js; so, to watch errors for debugging,
#  wrapper.py should redirect stderr only, like this for Windows:
# python "%~dp0\wrapper.py" %* 2> C:\wrapper_errors.txt


import struct
import subprocess
import sys
import json
import os
import time
import xml.dom.minidom

GDXML_FILENAME="Garmin/GarminDevice.xml"

# quick way to read a user-configurable options file config.py
#  which must set values for these variables:
#  gpsbabel_exe - full filename of the gpsbabel executable file
#  chunk_size - integer less than 1e6; must be <1MB per Chrome spec
#  debug - True or False to enable logging file

from config import *

# write debug files, if any, to cross-platform user's home directory
debug_path=os.path.expanduser("~")
if debug:
    logfile=open(os.path.join(debug_path,"gpsio_log.txt"),"w")
    logfile.write("Python="+sys.version+"\n")
    logfile.write("platform="+sys.platform+"\n")
    logfile.write("arguments:"+str(sys.argv)+"\n")

# reopen stdout and stdin in bytes mode, for 2.7/3.3 compatibility
# Q: is this a win32 thing only or a python 3 thing only?
#sys.stdout=os.fdopen(sys.stdout.fileno(),'w+b')
#sys.stdin=os.fdopen(sys.stdin.fileno(),'rb',0)

# On Windows, the default I/O mode is O_TEXT. Set this to O_BINARY
# to avoid unwanted modifications of the input/output streams.

if sys.platform == "win32":
    import msvcrt
    sys.stdout=os.fdopen(sys.stdout.fileno(), 'w+b')
    sys.stdin=os.fdopen(sys.stdin.fileno(), 'rb', 0)
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)


# Helper function that sends a message to the webapp.
def send_message(message):
    # divide message in to <1MB chunks, per Chrome spec
    message=json.dumps(message)
    msglen=len(message)
    chunk_array=[message[i:i+chunk_size] for i in range(0,msglen,chunk_size)]

    if debug:
        logfile.write("msglen="+type(msglen).__name__+":"+str(msglen)+"\n")
        logfile.write("message="+type(message).__name__+":"+str(message)+"\n")
        logfile.write("chunk_array length: "+str(len(chunk_array))+"\n")

    # send each chunk as a separate message; each is UTF-8 encoded JSON,
    #  prepended by 32-bit length of encoded message, per Chrome spec
    for chunk in chunk_array:
        json_chunk=json.dumps(chunk)
        json_chunklen=len(json_chunk)
        json_chunklen_bytes=struct.pack('I',json_chunklen)
        if debug:
            logfile.write("CHUNK:"+chunk+"\n")
            logfile.write(" JSON:"+json_chunk+"\n")
        z=sys.stdout.write(json_chunklen_bytes)
        sys.stdout.flush()
        z=sys.stdout.write(json_chunk.encode('latin-1'))
        sys.stdout.flush()


def Main():
    # process the 32-bit message length to determine how many bytes to read
    request_length_bytes = sys.stdin.read(4)

    request_length = struct.unpack('i', request_length_bytes)[0]
    if debug:
        logfile.write("request_length="+type(request_length).__name__+":"+str(request_length)+"\n")

    # read the request of specified length: UTF-8 encoded JSON, per Chrome specs
    request = sys.stdin.read(request_length).decode('utf-8')

    if debug:
        logfile.write("request="+type(request).__name__+":"+str(request)+"\n")

    # validate and parse the request
    rq = json.loads(request)
    if "cmd" in rq:
        cmd=rq["cmd"]
        data=None
        if cmd=="export":
            if "data" in rq:
                data=rq["data"]
            else:
                send_message({'cmd': 'export', 'status': 'error', 'message': 'when \'cmd\' is \'export\', \'data\' must be specified in the JSON request'})
                sys.exit()
    else:
        send_message({'cmd': cmd, 'status': 'error', 'message': 'must specify \'cmd\' in the JSON request'})
        sys.exit()

    if cmd == "ping-host":
        send_message({'cmd': 'ping-host', 'status': 'ok', 'version': 1})
        sys.exit()

    # get the filter options, if they exist - used in the call to transfer_gmsm
    options={}
    if "options" in rq:
        options=rq["options"]
        
    # differentiate by GPS brand and protocol
    if "target" in rq:
        target=rq["target"]

        if target=="garmin":
            # Garmin procedure:
            # 1. scan for a Garmin Mass Storage Mode device, which would appear as
            #     a drive with a file <drive>:/Garmin/GarminDevice.xml
            # 2a. if GMSM device is found: for import, recursively read all .gpx
            #      files under Garmin/XML; for export, just write the .gpx there
            # 2b. if no GMSM device is found, try Garmin Mode using gpsbabel
            # 2c. if still no connection, return with an error
            drive=scan_for_gmsm()
            if drive:
                if debug:
                    logfile.write("GMSM drive found at "+drive+"; calling transfer_gmsm\n")
                transfer_gmsm(cmd,data,drive,options)
            else:
                if debug:
                    logfile.write("No GMSM drive was found; calling transfer_gbsbabel\n")
                transfer_gpsbabel(cmd,data,"garmin")
        else:
            send_message({'cmd': cmd, 'status': 'error', 'message': 'Currently, \'garmin\' is the only supported target'})
            sys.exit()
    else:
        send_message({'cmd': cmd, 'status': 'error', 'message': 'must specify \'target\' in the JSON request'})
        sys.exit()

    if debug:
        logfile.write("rq.cmd:"+cmd+"\n")
        logfile.write("rq.target:"+target+"\n")

# step 1: find the connected device (i.e. the connected drive)
#  return value: full filename of the first <drive>:\Garmin\GarminDevice.xml
#     file that was found, or False if none was found, indicating no Garmin
#     Mass Storage Mode device is connected
def scan_for_gmsm():
    if sys.platform == "win32":
        drives=["A:\\","B:\\","C:\\","D:\\","E:\\","F:\\","G:\\","H:\\","I:\\","J:\\","K:\\","L:\\","M:\\","N:\\"]
        for drive in drives:
            if os.path.exists(os.path.join(drive, GDXML_FILENAME)):
                return drive
        return False
    elif sys.platform == "darwin":
        vols = os.listdir('/Volumes')
        for vol in vols:
            if debug:
                logfile.write(os.path.join('/Volumes', vol, GDXML_FILENAME) + "\n")
            if os.path.exists(os.path.join('/Volumes', vol, GDXML_FILENAME)):
                return os.path.join('/Volumes', vol)
    else:
        return False

def transfer_gmsm(cmd,data,drive,options):
        # Apparently, the file structure on a GPSmap 62s looks like this:
        # 1. the file specified by parsing GarminDevice.xml (apparently always
        #     Garmin/GPX/Current/Current.gpx) only contains the current track log if
        #     there is one.  Waypoints, saved tracks, and routes do not appear in
        #     this file.
        # 2. Saved route: Garmin/GPX/Route_yyyy-mm-dd<space>hhmmss.gpx
        # 3. Saved track: Garmin/GPX/Track_<track_name>.gpx
        # 4. Saved waypoints: Garmin/GPX/Waypoints_dd-MMM-yy.gpx
        # 5. Archived track: Garmin/GPX/Archive/<track_name>.gpx
        #
        # Apparently, the safest method to import from the GPS is to just recursively
        #  read all gpx files in Garmin/GPX.
        #
        # When a file is copied to this directory from the computer, apparently the
        #  file remains until all objects in it have been deleted.  Needs to be verified.

        # If some objects from that file are deleted using the GPS, the same file will
        #  be re-saved without the deleted objects.  Needs to be verified.
        #
        # So, when saving a file to Garmin/GPX from the computer, it should not begin
        #  with Route_ or Track_ or Waypoints_.

        # notes:
        # - export from GCP creates Garmin/GPX/temp.GPX
        # - create waypoints, track, and route on gps; import them using GCP; add
        #    a waypoint,route,track in caltopo; export all to gps; then read again,
        #    without unplugging the gps, and everything IS listed twice!  So, it is
        #    reading temp.GPX in addition to all the other gpx files.
        #   then cancel GCP without reading; unplug, re-plug and look at the files:
        #    new file Imported_yyyy-mm-dd<space>hhmmss.gpx exists in Garmin/GPX and
        #    it has everything (but not duplicates).  Maybe just a renamed version
        #    of temp.GPX?  (temp.GPX no longer exists)
        #   now try to import using GCP, and duplicates still exist - indication that
        #    it is still reading all .gpx files.
        #   unplug and delete one of the items that were created in and exported from
        #    caltopo; then plug back in and view files: the same Imported_ file
        #    (and same id) exists, but the deleted object(s) have been deleted from
        #    that file.
        #   unplug and delete all of the items that were exported from caltopo; then
        #    re-plug: that Imported_ file no longer exists.

    if cmd=="import":

        # 1. get a list of .gpx files to import
        # start with a list of all .gpx files recursively under Garmin/GPX
        gpx_files=[]
        for root, dirs, files in os.walk(os.path.join(drive,'Garmin','GPX')):
            for file in files:
                if file.upper().endswith(".GPX") and not(file.startswith(".")):
                    gpx_files.append(os.path.join(root,file))

        # reverse chronological sort (most recent file is first in the list)
        gpx_files=sorted(gpx_files,key=os.path.getmtime,reverse=True)
        totalFileCount=len(gpx_files)
                
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
                
                if debug:
                    logfile.write("Selecting files "+str(m)+" thru "+str(n)+" from a reverse-chronological-order sorted list...\n")
                gpx_files=gpx_files[m-1:n]
                
            if options["method"]=="time" and "timeSel" in options:
                currentTime=time.time()
                if debug:
                    logfile.write("Filtering out files older than "+options["timeSel"]+" hours...\n")
                gpx_files=[f for f in gpx_files if (currentTime-os.path.getmtime(f))/3600<int(options["timeSel"])]    

        if "size" in options:                
            if options["size"]==True and "sizeSel" in options:
                if debug:
                    logfile.write("Filtering out files larger than "+options["sizeSel"]+"...\n")
                # as long as sizeSel is in the format of <n>kb or <n>mb (case does not matter)
                #  then the following line will filter correctly, i.e. '10kB' or '5MB'
                gpx_files=[f for f in gpx_files if (os.path.getsize(f)<eval(options["sizeSel"].lower().replace("kb","*1024").replace("mb","*1048576")))]

        # end of filtering
        
        # list the filtered file set
        filteredFileCount=len(gpx_files)
        if filteredFileCount == 0:
            if debug:
                logfile.write("No recent files out of " + str(totalFileCount) + " total gpx files on the device:\n")
            send_message({'cmd': cmd, 'status': 'error', 'message': 'No GPX files out of '+str(totalFileCount)+' met the filter settings.  Click the GPSIO Extension icon for details.' })
            sys.exit()
        if debug:
            logfile.write("Sending "+str(filteredFileCount)+" out of "+str(totalFileCount)+" total gpx files on the device:\n")
            logfile.write(str(gpx_files)+"\n")
        
        # 2. use gpsbabel to combine the files and send to the extension
        args=[gpsbabel_exe,"-w","-r","-t","-i","gpx"]
        for gpx_file in gpx_files:
            args.extend(("-f",gpx_file))
        args.extend(("-o","gpx","-F","-"))
        if debug:
            logfile.write("invoking: "+str(args)+"\n")
            logfile.write("with data: "+str(data)+"\n")
        p=subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate(data)
        if err != None and len(err) > 2:
            send_message({'cmd': cmd, 'status': 'error', 'message': str(err.decode('latin-1')) })
        else:
            if debug:
                logfile.write("err: "+str(err)+"\n")
            note="Showing data from "+str(filteredFileCount)+" out of "+str(totalFileCount)+" total GPX file(s).  Click the GPSIO Extension icon for details."
            send_message({'cmd': cmd, 'status': 'ok', 'note': note, 'message': str(output.decode('latin-1')) })
    elif cmd=="export":
        gpx_fname=os.path.join(drive,'Garmin','GPX','gpsio'+time.strftime("%Y_%m_%d_%H%M%S")+'.gpx')
        gpx=open(gpx_fname,"w")
        gpx.write(data)
        gpx.close
        send_message({'cmd': cmd, 'status': 'ok', 'message': "GMSM export successful"})
    else:
        send_message({'cmd': cmd, 'status': 'error', 'message': 'cmd must be \'import\' or \'export\''})
        sys.exit()

def transfer_gpsbabel(cmd,data,target):
    # build the subprocess command
    if(cmd=="import"):
        args=[gpsbabel_exe,"-w","-r","-t","-i",target,"-f","usb:","-o","gpx","-F","-"]
    elif(cmd=="export"):
        args=[gpsbabel_exe,"-w","-r","-t","-i","gpx","-f","-","-o",target,"-F","usb:"]
        data=data.encode('utf-8')
        if debug:
            logfile.write("rq.data length:"+str(len(data))+"\n")
            logfile.write("rq.data:"+str(data)+"\n")
    else:
        send_message({'cmd': cmd, 'status': 'error', 'message': 'cmd must be \'import\' or \'export\''})
        sys.exit()

    # do the subprocess command and send any data
    if debug:
        logfile.write("invoking: "+str(args)+"\n")
    p=subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate(data)

    # if no usb device is found, err will be a multi-line string like this:

    # for GPSBabel 1.5.3 on Vista:

        #[ERROR] SetupDiEnumDeviceInterfaces: The system cannot find the path specified.
        #Is the Garmin USB unit number 0 powered up and connected?
        #Is it really a USB unit?  If it's serial, don't choose USB, choose serial.
        #Are the Garmin USB drivers installed and functioning with other programs?
        #Is it a storage based device like Nuvi, CO, or OR?
        #  If so, send GPX files to it, don't use this module.
        #[ERROR] Get_Time: Unknown date/time protocol
        #GARMIN:Can't init usb:

    # for GPSBabel 1.5.3 on Windows 7: all the same as above, except the first line:

        #[ERROR] SetupDiEnumDeviceInterfaces: The device is not ready.

    if err:
        err=str(err.decode('latin-1'))
        if debug:
            logfile.write("err: "+str(err.decode('latin-1')))
        if "The system cannot find the path specified." in err or "The device is not ready." in err:
            send_message({'cmd': cmd, 'status':'error','message':'no GPS was found'})
        else:
            send_message({'cmd': cmd, 'status':'error','message':err})
        sys.exit()

    if debug:
        response = {}
        response['output']=str(output.decode('latin-1'))
        logfile.write("resonse: " + json.dumps(response))
        logfile.write("output="+type(output).__name__+":"+str(output)+"\n")
        logfile.write("Total xml response length: "+str(len(output))+" bytes\n")

    if(cmd=="import"):
        send_message({'cmd': cmd, 'status': 'ok', 'message': str(output.decode('latin-1'))})
    elif(cmd=="export"):
        send_message({'cmd': cmd, 'status': 'ok', 'message': "GPSBabel export successful"})


if __name__ == '__main__':
    Main()
