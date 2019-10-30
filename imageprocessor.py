from PIL import Image
import urllib
import os
from compressinator_utils import printlog, CompressionInfo, TIMEOUT, curl_limit_rate, image_errors
import re
import subprocess
import shutil

def process_image(image_url, updatedConfig, url, new_path, backup_path):
    MinBytes = int(updatedConfig['minbytes'])
    MinSaving = int(float(updatedConfig['minsaving']))
    SsoLink = updatedConfig['ssolink']
    PngquantCommand = updatedConfig['pngquantcommand']
    PillowQuality = int(updatedConfig['pillowquality'])
    ThumbnailPath = updatedConfig['thumbnailpath']
    RootPath = updatedConfig['rootpath']
    site_regex = re.escape(url)
    new_size = 0
    old_size = 0
    attempted = False
    compressed = False
    if re.search(r'(https?:|^\/\/)', image_url) is None:
        image_url = url + image_url
    elif re.search(site_regex, image_url) is None:
        return CompressionInfo(exclusion_reason='REMOTE')
    if re.search(re.escape(ThumbnailPath), image_url) is not None:
        return CompressionInfo(exclusion_reason='THUMBNAIL')
    try:
        image = None
        try:
            image = urllib.request.urlopen(image_url, timeout=TIMEOUT)
        except Exception as error:
            image_errors[url][image_url] = repr(error)
            return CompressionInfo(exclusion_reason='ERROR')
        image_size = int(image.getheader("Content-Length"))
        if image_size > MinBytes:
            image_relative_path = re.sub(site_regex, '', image_url) #Remove the https://domain.com
            image_relative_path = re.sub(r'^\/', '', image_relative_path) # Remove the initial / so it doesn't look like an absolute path
            image_relative_path = image_relative_path.split('/')
            filename = os.path.join(new_path,*image_relative_path)
            backup_filename = os.path.join(backup_path, *image_relative_path)
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except OSError as exc: # Guard against race condition
                    printlog('OS Error')
                    pass
            elif os.path.exists(filename):
                return CompressionInfo(exclusion_reason='EXISTS')
            if not os.path.exists(os.path.dirname(backup_filename)):
                try:
                    os.makedirs(os.path.dirname(backup_filename))
                except OSError as exc: # Guard against race condition
                    printlog('OS Error')
                    pass
            with open(filename, "w") as file:
                #urllib.request.urlretrieve(image_url, filename)
                try:
                    curl_limit_rate(image_url, filename, 500000)
                except Exception as error:
                    printlog('Could not write ' + image_url + ' to ' + filename)
                    return CompressionInfo(to_remove=filename, exclusion_reason='ERROR')
            if not os.path.exists(backup_filename):
                shutil.copyfile(filename, backup_filename)
            original_file_size = os.path.getsize(filename)
            if re.search(r'png$', image_url, re.IGNORECASE):
                command = PngquantCommand + ' \"' + filename +'\"'
                CREATE_NO_WINDOW = 0x08000000
                process = subprocess.Popen(command, stdout=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
                output, error = process.communicate()
            else:
                image = Image.open(filename)
                try:
                    image.save(filename, optimize=True, quality=int(PillowQuality))
                except Exception as err:
                    printlog(filename)
                    printlog(repr(err))
                    pass
            new_file_size = os.path.getsize(filename)
            attempted = True
            if original_file_size == 0 or (original_file_size - new_file_size) / original_file_size < (MinSaving / 100):
                os.remove(filename)
                os.remove(backup_filename)
            else:
                old_size = original_file_size
                new_size = new_file_size
                compressed = True
        else:
            return CompressionInfo(exclusion_reason='TOO_SMALL')
    except Exception as err:
        printlog('Got an error with: ' + image_url)
        printlog(repr(err))
    return CompressionInfo(new_size=new_size, old_size=old_size, attempted=attempted, compressed=compressed)
