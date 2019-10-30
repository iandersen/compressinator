import kivy
kivy.require('1.11.1') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
import re
import os
import subprocess
from multiprocessing.dummy import Pool as ThreadPool
import itertools
import random
from kivy.clock import Clock, _default_time as time
from settingsjson import settings_json
from loadingquotes import loading_quotes
from urlprocessor import process_url
from compressinator_utils import printlog, url_regex, STATUSES, updatedConfig
from popupbox import PopupBox

class Root(BoxLayout):
    pass

class CompressinatorApp(App):
    is_compressinating = False
    compressed_so_far = 0
    total_to_compress = 0
    pop_up = None
    clock_interval = None

    def compress_stuff(self):
        if not self.is_compressinating:
            self.is_compressinating = True
            pool = ThreadPool(8)
            to_process =  self.root.ids.unprocessed.text
            parsed_list = []
            for line in to_process.splitlines():
                if not line[0] == '#':
                    parsed = re.sub(r'[\n\/]+$', '', line)
                    parsed = re.sub(r'#.*$', '', parsed)
                    if parsed:
                        if re.match(url_regex, parsed) is not None:
                            parsed_list.append(parsed)
                        else:
                            printlog('It looks like you entered a malformed URL. I am gonna ignore it ' + parsed)
            self.compressed_so_far = 0
            self.total_to_compress = len(parsed_list)
            self.show_popup()
            self.clock_interval = Clock.schedule_interval(self.update_status, 1/15)
            try:
                pool.starmap_async(process_url, zip(parsed_list, itertools.repeat(updatedConfig)), callback=self.sites_compressed)
            except Exception as err:
                printlog('URL processing error: ' + repr(err))

    def set_pop_up_text(self):
        quote, person = random.choice(loading_quotes)
        self.pop_up.update_pop_up_text('Compressinator is Compressinating the Files!\n\n"'+quote+'"\n -' + person)

    def update_status(self, *args):
        status_string = ''
        for status in STATUSES:
            status_string += STATUSES[status] + '\n'
        self.pop_up.update_status(status_string)

    def show_popup(self):
        self.pop_up = Factory.PopupBox()
        self.set_pop_up_text()
        self.pop_up.open()

    def sites_compressed(self, result):
        if self.clock_interval is not None:
            self.clock_interval.cancel()
        for url in result:
            self.root.ids.processed.text = self.root.ids.processed.text + url + "\n"
        self.root.ids.unprocessed.text = ''
        self.pop_up.dismiss()
        self.is_compressinating = False

    def view_output_folder(self):
        subprocess.Popen(r'explorer "'+updatedConfig['rootpath']+'"')

    def build(self):
        self.use_kivy_settings = False
        for key in self.config['Default']:
            updatedConfig[key] = self.config['Default'].get(key)
            if key == 'wholesite':
                if updatedConfig[key] == '0':
                    updatedConfig[key] = False
                else:
                    updatedConfig[key] = True
        return Root()

    def build_config(self, config):
        default_root_path = os.path.expanduser('~\\Documents\\Compressed Websites')
        if not os.path.exists(default_root_path):
            os.makedirs(default_root_path)
        config.setdefaults('Default', {
            'MinBytes': '20000',
            'MinSaving': '5',
            'SsoLink': 'sso49',
            'PngquantCommand': '.\\pngquant --ext .png --force 256 --quality=65-80',
            'PillowQuality': '80',
            'ThumbnailPath': '/cms/thumbnails/',
            'RootPath': default_root_path,
            'WholeSite': False
        })

    def build_settings(self, settings):
        settings.add_json_panel('Compressinator Settings', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        if key == 'WholeSite':
            if value == '0':
                updatedConfig[key] = False
                updatedConfig['wholesite'] = False
            else:
                updatedConfig[key] = True
                updatedConfig['wholesite'] = True
        else:
            updatedConfig[key] = value
        if key == 'RootPath':
            self.root.ids.output_path.text = 'Output Path: ' + updatedConfig[key]



if __name__ == '__main__':
    CompressinatorApp().run()