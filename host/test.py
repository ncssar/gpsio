import re
import contextlib
import mmap

# check_for_gpxtrkx: return true if the file contains 'xmlns:gpxtrkx', false if not
def check_for_gpxtrkx(filename):
    # this method is pretty fast per
    # https://stackoverflow.com/questions/40868592/fastest-way-to-grep-big-files
    # regex=re.compile(r'xmlns:gpxtrkx')
    with open(filename,mode='r',encoding='utf-8') as f:
        mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
        return mm.find(b'xmlns:gpxtrkx')>=0
        # with contextlib.closing(mm) as txt:
        #     match=regex.search(txt)
        #     if match:
        #         return True
        #     else:
        #         return False

print("checking...")
r=check_for_gpxtrkx("G:\Garmin\GPX\AAM.gpx")
print(str(r))