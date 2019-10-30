from bs4 import BeautifulSoup
import threading
import re
from compressinator_utils import STATUSES, all_pages_visited, printlog, TIMEOUT, REASONS, sizeof_fmt, del_dirs, link_errors, image_to_page_map, image_errors
import requests
import os
from imageprocessor import process_image


def get_image_urls_from_page(source, url, domain_url):
    STATUSES[threading.get_ident()] = 'Searching for images on '  + url
    images = re.findall(r'(?:\/|http)[\]\[ %a-zA-Z0-9-_\/.:\w_-]+\.(?:jpg|png|jpeg)', source, flags=re.IGNORECASE)
    processed_images = []
    for image in images:
        image = re.sub(r' ', '%20', image)
        if re.search(r'(https?:|^\/\/)', image) is None:
            if re.search(r'^\/', image) is None:
                image = url + '/' + image
            else:
                image = domain_url + image
        processed_images.append(image)
        add_image_to_map(image, url, domain_url)
    return processed_images

def add_image_to_map(image_url, url, domain_url):
    global image_to_page_map
    if image_url in image_to_page_map[domain_url]:
        if not url in image_to_page_map[domain_url][image_url]:
            image_to_page_map[domain_url][image_url].append(url)
    else:
        image_to_page_map[domain_url][image_url] = [url,]

def crawl_all_images(url, domain_url, parent_url=None):
    STATUSES[threading.get_ident()] = 'Crawling page ' + url
    response = None
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except Exception as err:
        printlog('Crawling error: ' + repr(err))
        return []
    if response.status_code != 200:
        if parent_url is not None:
            link_errors[domain_url].append('Invalid link found on ' + parent_url + ': ' + url + ' - Error Code: ' + str(response.status_code))
        else:
            link_errors[domain_url].append('Invalid link found on ' + domain_url + ': ' + url + ' - Error Code: ' + str(response.status_code))
    s = BeautifulSoup(response.text, "html.parser")
    links = []
    images = get_image_urls_from_page(response.text, url, domain_url)
    for link in s.findAll('a', href=True):
        href = link.get('href')
        if re.search(r'^(tel:|mailto:|javascript:)', href) is not None:
            continue
        if re.search(r'(\.pdf|\.mp4|\.mp3|\.mov|\.m4v|\.jpg|\.jpeg|\.png)$', href, flags=re.IGNORECASE) is not None:
            continue
        if re.search(r'(https?:|^\/\/)', href) is None:
            if re.search(r'^\/', href) is None:
                href = url + '/' + href
            else:
                href = domain_url + href
        elif re.search(re.escape(domain_url), href) is None:
            continue
        href = re.sub(r'[#].*', '', href) # Replace everything after anchors
        href = re.sub(r'([^:])\/{2,}', r'\1/', href) # Replace extra slashes
        href = re.sub(r'\/$', '', href) # Remove the trailing slash
        if href not in all_pages_visited[domain_url]:
            all_pages_visited[domain_url].append(href)
            links.append(href)
    for link in links:
        new_images = crawl_all_images(link, domain_url, parent_url=url)
        for image in new_images:
            if image not in images:
                images.append(image)
    return images
        

def process_url(url, updatedConfig):
    STATUSES[threading.get_ident()] = 'Beginning to Process ' + url
    MinBytes = int(updatedConfig['minbytes'])
    MinSaving = int(float(updatedConfig['minsaving']))
    SsoLink = updatedConfig['ssolink']
    PngquantCommand = updatedConfig['pngquantcommand']
    PillowQuality = int(updatedConfig['pillowquality'])
    ThumbnailPath = updatedConfig['thumbnailpath']
    RootPath = updatedConfig['rootpath']
    WholeSite = updatedConfig['wholesite']
    if WholeSite == '0':
        WholeSite = False
    

    total_size = 0
    new_size = 0
    old_size = 0

    images_attempted = 0
    total_bytes_saved = 0
    total_bytes_saved = 0
    images_compressed = 0

    host_regex = r'(?:http[s]?:)\/\/([^\/?#]+)'
    host_url_regex = r'(?:http[s]?:)\/\/(?:[^\/?#]+)'

    hostname = re.match(host_regex, url).group(1)
    host_url = re.match(host_url_regex, url).group()
    all_pages_visited[host_url] = []
    link_errors[host_url] = []
    image_errors[host_url] = {}
    image_to_page_map[host_url] = {}
    pages_crawled = 0

    current_path = os.path.realpath(RootPath)

    if not os.path.exists(current_path):
        os.makedirs(current_path)

    new_path = os.path.join(current_path, hostname)
    backup_path_root = os.path.join(current_path, '_original')

    if not os.path.exists(backup_path_root):
        os.mkdir(backup_path_root)

    backup_path = os.path.join(backup_path_root, hostname)

    if not os.path.exists(backup_path):
        os.mkdir(backup_path)
    if not os.path.exists(new_path):
        os.mkdir(new_path)

    images = []
    STATUSES
    if not WholeSite:
        STATUSES[threading.get_ident()] = 'Downloading ' + url
        response = requests.get(url, timeout=TIMEOUT)
        images = get_image_urls_from_page(response.text, url, host_url)
    else:
        try:
            STATUSES[threading.get_ident()] = 'Crawling site: ' + host_url
            images = crawl_all_images(url, host_url)
            pages_crawled = len(all_pages_visited[host_url])
        except Exception as err:
            printlog(repr(err))

    STATUSES[threading.get_ident()] = 'Creating shortcut for: ' + url
    shortcut_path = os.path.join(new_path, "View Online.url")
    info_file = os.path.join(new_path, 'Compression Info.txt')
    shotrcut_target = url + '/' + SsoLink
    images_on_site = 0
    images_found = 0
    images_compressed = 0
    old_size = 0
    new_size = 0
    images_skipped = {}
    
    with open(shortcut_path, 'w') as shortcut:
        shortcut.write('[InternetShortcut]\n')
        shortcut.write('URL=%s' % shotrcut_target)
        shortcut.close()
    images = list(dict.fromkeys(images)) #Remove duplicates
    for image_match in images:
        image_url = image_match
        STATUSES[threading.get_ident()] = 'Processing image: ' + image_url
        try:
            info = process_image(image_url, updatedConfig, host_url, new_path, backup_path)
        except Exception as err:
            printlog('Image error: ' + repr(err))
        if info.to_remove is not None:
            os.remove(info.to_remove)
        images_found += 1
        if info.compressed == True:
            images_compressed += 1
            old_size += info.old_size
            new_size += info.new_size
        if info.attempted == True:
            images_attempted += 1
        if not info.exclusion_reason == 'NONE':
            images_skipped[info.exclusion_reason] = images_skipped.get(info.exclusion_reason, 0) + 1
            
    if images_compressed == 0:
        os.remove(shortcut_path) #Remove the shortcut
    ratio = 0
    if new_size > 0:
        ratio = round(100 * (1 - new_size / (new_size + old_size)), 2)
    try:
        with open(info_file, 'w') as file:
            file.write('Compression Ratio: ' + str(ratio) + '%\n')
            if pages_crawled > 0:
                file.write('Pages Crawled: ' + str(pages_crawled) +'\n')
            file.write('Images found: ' + str(images_found) +'\n')
            for reason in images_skipped:
                file.write('\t' + str(REASONS[reason]) + ': ' + str(images_skipped[reason]) + '\n')
            file.write('Images attempted: ' + str(images_attempted) +'\n')
            file.write('Images Compressed: ' + str(images_compressed) + '\n')
            file.write('Amount saved: ' + str(sizeof_fmt(old_size - new_size)) + '\n')
            file.write('\nLink Errors\n')
            for error in link_errors[host_url]:
                try:
                    printlog(error)
                except Exception as err:
                    printlog(repr(err))
                file.write('\t' + error + '\n')
            file.write('\nImage Errors\n')
            for image_url in image_errors[host_url]:
                file.write('Error with ' + image_url + ': ' + image_errors[host_url][image_url] + ' - on the following page(s): \n')
                for page in image_to_page_map[host_url][image_url]:
                    file.write('\t' + page + '\n')
    except Exception as error:
        printlog(repr(error))
    del_dirs(new_path)
    del_dirs(backup_path)
    del STATUSES[threading.get_ident()]
    return url