import re
import requests
import urllib
import os
import subprocess
from PIL import Image
import configparser

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    print(os.path.join(base_path, relative_path))
    return os.path.join(base_path, relative_path)

config = configparser.ConfigParser()
config.read(resource_path('config.ini'))
default_config = None

if 'DEFAULT' in config:
    default_config = config['DEFAULT']
else:
    print('Config error! DEFAULT section missing')

#Yeah I yoinked this from StackOverflow
url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def parse_sites(sites_list):
    print('Parsing site list')
    sites = []
    with open(sites_list, 'r') as file:
        line = file.readline()
        line_count = 1
        while line:
            if not line[0] == '#':
                parsed = re.sub(r'[\n\/]+$', '', line)
                if parsed:
                    if re.match(url_regex, parsed) is not None:
                        sites.append(parsed)
                    else:
                        print('It looks like you entered a malformed URL. I am gonna ignore it ' + parsed)
                        print('Ignored URL on line ' + str(line_count))
            line_count += 1
            line = file.readline()
    return sites
        

sites = parse_sites(default_config.get('SiteListFile', 'sites.txt'))

def del_dirs(src_dir):
    for dirpath, _, _ in os.walk(src_dir, topdown=False):  # Listing the files
        if dirpath == src_dir:
            break
        try:
            os.rmdir(dirpath)
        except OSError as ex:
            continue

total_bytes_saved = 0
images_compressed = 0
images_attempted = 0

for site in sites:
    MIN_BYTES = int(default_config.get('MinBytes', 50000))
    MIN_SAVING = float(default_config.get('MinSaving', 0.05))

    total_size = 0
    new_size = 0

    response = requests.get(site)

    host_regex = r'(?:http[s]?:)\/\/([^\/]+)'

    hostname = re.match(host_regex, site).group(1)
    # print('Compressing ' + hostname)

    current_path = os.path.realpath(default_config.get('RootPath', 'sites_to_compress'))

    new_path = current_path + '/' + hostname
    backup_path = current_path + '/'+default_config.get('BackupFolderName', '_original') + '/' + hostname

    if not os.path.exists(backup_path):
        os.mkdir(backup_path)
    else:
        print('Skipping ' + hostname)
        continue
    if not os.path.exists(new_path):
        os.mkdir(new_path)

    images = re.finditer(r'[a-zA-Z0-9-_\/.:]+([\w_-]+[.](jpg|png|jpeg))', response.text, flags=re.IGNORECASE)

    path = os.path.join(new_path, "View Online.url")
    target = site + '/' + default_config.get('SsoLink', 'sso49')

    images_on_site = 0
    
    with open(path, 'w') as shortcut:
        shortcut.write('[InternetShortcut]\n')
        shortcut.write('URL=%s' % target)
        shortcut.close()

    for image_match in images:
        image_url = image_match.group()
        site_regex = re.escape(site)
        if not re.match(r'http', image_url):
            image_url = site + image_url
        elif not re.match(site_regex, image_url):
            continue
        if re.search(r'\/cms\/thumbnails\/', image_url):
            continue
        try:
            image = urllib.request.urlopen(image_url)
            image_size = int(image.getheader("Content-Length"))
            if image_size > MIN_BYTES:
                filename = new_path + re.sub(site_regex, '', image_url)
                backup_filename = backup_path + re.sub(site_regex, '', image_url)
                if not os.path.exists(os.path.dirname(filename)):
                    try:
                        os.makedirs(os.path.dirname(filename))
                    except OSError as exc: # Guard against race condition
                        continue
                if not os.path.exists(os.path.dirname(backup_filename)):
                    try:
                        os.makedirs(os.path.dirname(backup_filename))
                    except OSError as exc: # Guard against race condition
                        continue
                with open(filename, "w") as file:
                    urllib.request.urlretrieve(image_url, filename)
                with open(backup_filename, "w") as file:
                    urllib.request.urlretrieve(image_url, backup_filename)
                original_file_size = os.path.getsize(filename)
                if re.search(r'png$', image_url, re.IGNORECASE):
                    command = default_config.get('PngquantCommand', 'pngquant --ext .png --force 256 --quality=65-80') + ' ' + filename
                    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                    output, error = process.communicate()
                else:
                    image = Image.open(filename)
                    try:
                        image.save(filename, optimize=True, quality=int(default_config.get('PillowQuality', 80)))
                    except:
                        pass
                new_file_size = os.path.getsize(filename)
                images_attempted += 1
                if (original_file_size - new_file_size) / original_file_size < MIN_SAVING:
                    os.remove(filename)
                    os.remove(backup_filename)
                else:
                    total_size += original_file_size
                    total_bytes_saved += original_file_size - new_file_size
                    images_compressed += 1
                    images_on_site += 1
                    new_size += new_file_size
        except:
            # print(image_url + ' responded with error code of ' + str(err.code))
            continue
    if images_on_site == 0:
        os.remove(path) #Remove the shortcut
    ratio = 0
    if total_size > 0:
        ratio = 100 * (1 - new_size / total_size)
    print(hostname + ' compression ratio: ' + str(ratio) + '%')

del_dirs(current_path)
print('KB saved: ' + str(total_bytes_saved / 1024))
print('Images compressed: ' + str(images_compressed))
print('Images attempted: ' + str(images_attempted))