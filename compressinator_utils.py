import re
import pycurl
import os
import certifi
from collections import namedtuple

updatedConfig = {}

TIMEOUT = 8

STATUSES = {}

all_pages_visited = {}
link_errors = {}
image_errors = {}
image_to_page_map = {}

EXCLUSION = {
    'NONE':0,
    'TOO_SMALL': 1,
    'THUMBNAIL': 2,
    'REMOTE': 3,
    'EXISTS': 4,
    'ERROR': 5
}
REASONS = {
    'NONE': 'Not skipped',
    'TOO_SMALL': 'File was too small',
    'THUMBNAIL': 'File was a thumbnail',
    'REMOTE': 'File was on another server',
    'EXISTS': 'File already exists on your local machine',
    'ERROR': 'File could not be downloaded'
}
compression_info_fields = ('new_size', 'old_size', 'attempted', 'compressed', 'to_remove', 'exclusion_reason')
CompressionInfo = namedtuple('CompressionInfo', compression_info_fields, defaults=(0,0,False,False,None,'NONE'))

def printlog(message):
    with open('./log.txt','a') as f: 
        f.write(message)
        f.write('\n')

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def del_dirs(src_dir):
    for dirpath, _, _ in os.walk(src_dir, topdown=False):  # Listing the files
        if dirpath == src_dir:
            break
        try:
            os.rmdir(dirpath)
        except OSError as ex:
            continue

def curl_progress(total, existing, upload_t, upload_d):
    try:
        frac = float(existing)/float(total)
    except:
        frac = 0

def curl_limit_rate(url, filename, rate_limit):
    """Rate limit in bytes"""
    c = pycurl.Curl()
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(c.URL, url)
    c.setopt(c.MAX_RECV_SPEED_LARGE, rate_limit)
    c.setopt(c.FOLLOWLOCATION, 1)
    c.setopt(c.USERAGENT, '')
    c.setopt(c.CONNECTTIMEOUT, TIMEOUT)
    if os.path.exists(filename):
        file_id = open(filename, "ab")
        c.setopt(c.RESUME_FROM, os.path.getsize(filename))
    else:
        file_id = open(filename, "wb")

    c.setopt(c.WRITEDATA, file_id)
    c.setopt(c.NOPROGRESS, 0)
    c.setopt(c.PROGRESSFUNCTION, curl_progress)
    c.perform()

#Yeah I yoinked this from StackOverflow
url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)