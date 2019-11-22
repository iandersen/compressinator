import json

settings_json = json.dumps([
            {
                "type":"path",
                "title": "Output Directory",
                "desc":"This is where your compressed images will go",
                "section":"Default",
                "key":"RootPath"
            },
            {
                "type":"numeric",
                "title": "Minimum File Size",
                "desc":"The smallest file size, in bytes, that you care about compressing. 20000 by default",
                "section":"Default",
                "key":"MinBytes"
            },
            {
                "type":"numeric",
                "title": "Minimum Percentage Saved",
                "desc":"If compressing the file saves less than this, ignore it. 5 by default",
                "section":"Default",
                "key":"MinSaving"
            },
            {
                "type":"string",
                "title": "SSO Link to Use",
                "desc":"sso49 by default",
                "section":"Default",
                "key":"SsoLink"
            },
            {
                "type":"string",
                "title": "PNGQuant Command",
                "desc":"The command to call for compressing PNGs. The default is: pngquant --ext .png --force 256 --quality=65-80",
                "section":"Default",
                "key":"PngquantCommand"
            },
            {
                "type":"numeric",
                "title": "JPG Compression Quality",
                "desc":"80 by default",
                "section":"Default",
                "key":"PillowQuality"
            },
            {
                "type":"string",
                "title": "Thumbnail Path",
                "desc":"The path to thumbnails, which will be ignored since compressing thumbnails is probably not useful. Separate different terms with a ','. By default this is: /cms/thumbnails/,/cmssys/thumbnails/",
                "section":"Default",
                "key":"ThumbnailPath"
            },
            {
                "type":"bool",
                "title": "Crawl the Whole Site?",
                "desc":"If selected, the Compressinator will attempt to visit every page and download all the images. This will be much much slower.",
                "section":"Default",
                "key":"WholeSite"
            },
            {
                "type":"bool",
                "title": "Download External Images?",
                "desc":"If selected, the Compressinator will download images hosted on other domains.",
                "section":"Default",
                "key":"AllowExternalImages"
            },
            {
                "type":"bool",
                "title": "Flatten Output Directory?",
                "desc":"If selected, this will not separate the images into subfolders",
                "section":"Default",
                "key":"FlattenOutputDirectory"
            },
            {
                "type":"bool",
                "title": "Download All Images?",
                "desc":"If selected, this will save images even if they cannot be compressed anymore.",
                "section":"Default",
                "key":"CopyAllImages"
            }
        ])