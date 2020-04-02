import os
import re
import glob
import json
import base64
import subprocess
from typing import NamedTuple
from urllib.parse import urlparse, parse_qs

import click
import orjson

url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

page_regex = re.compile(
    r'PA([0-9]{1,3})', re.IGNORECASE)

class Page(NamedTuple):
    mag_id: str
    page: str
    data: str
    contentType: str

    def __eq__(self, other: 'Page') -> bool:
        return self.mag_id == other.mag_id and self.page == other.page

    @staticmethod
    def parse(raw_url: str, data: str, contentType: str) -> 'Page':
        qs = parse_qs(urlparse(raw_url).query)
        page = qs['pg'][0]

        return Page(qs['id'][0], page, data, contentType)

    def save(self, name, counter) -> None:
        ext = 'png' if self.contentType == 'image/png' else 'jpg'
        with open(f'output/{name}_{counter}_{self.page}.{ext}', 'wb') as f:
            f.write(base64.b64decode(self.data))

class UrlParamType(click.ParamType):
    name = 'url'
    def convert(self, value, param, ctx):
        if value is None:
            return None
        if re.match(url_regex, value):
            return urlparse(value)
        self.fail(f'{value} is not a valid url', param, ctx)\

URL_TYPE=UrlParamType()

def is_mag_page(raw_url):
    qs = parse_qs(urlparse(raw_url).query)
    return 'pg' in qs.keys() and 'id' in qs.keys() and re.match(page_regex, qs['pg'][0])

@click.command()
@click.option('--file', help='HAR file to process', required=True, type=click.File())
@click.option('--title', help='Title for magazine files', type=click.STRING)
def process(file, title):
    mag_id = 'pcmag'
    har = json.loads(file.read())
    title = title if title is not None else mag_id

    if click.confirm('Do you want to clean output directory? '):
        files = glob.glob("output/*")
        for f in files:
            os.remove(f)

    counter = 1
    for image in [x for x in har['log']['entries'] if x['response']['content']['mimeType'] in ['image/png', 'image/jpeg']]:
        qs = parse_qs(urlparse(image['request']['url']).query)
        if 'id' not in qs.keys():
            continue

        page = qs['pg'][0] if 'pg' in qs else qs['printsec'][0]
        ext = 'png' if image['response']['content']['mimeType'] == 'image/png' else 'jpg'
        fname = f'output/{mag_id}_{counter:3}_{page}.{ext}'
        with open(fname, 'wb') as f:
            f.write(base64.b64decode(image['response']['content']['text']))
        counter += 1

    if click.confirm('Is everything ok?'):
        volume = click.prompt('Name of volume: ')
        subprocess.run(["imconvert", "output/*.*", 
            "-scale", "1240x1753", 
            "-gravity", "center",
            "-extent", "1240x1753",
            "-units", "PixelsPerInch",
            "-density", "150x150",
            "-quality", "100",
            "-unsharp", "0x2",
            f'pcmag_{volume}.pdf'])
    
if __name__ == '__main__':
    process()

