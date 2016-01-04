'''
Created on Dec 9, 2015

@author: theo
'''
from PIL import Image
from PIL.ExifTags import TAGS
import os, urllib, urlparse
from cStringIO import StringIO


ORIENTATION_TAG = 274
ROTATE_VALUES = {3: 180, 6: 270, 8: 90}

def isUrl(src):
    try:
        return urlparse.urlparse(src).scheme
    except:
        return False
    
class Exif:

    @classmethod
    def from_file(cls, f):
        exif = Image.open(f)._getexif()
        return {TAGS.get(tag,tag): value for tag, value in exif.items()}

    @classmethod
    def from_url(cls, url):
        return Exif.from_file(StringIO(urllib.urlopen(url).read()))

    @classmethod
    def copyImage(cls, url, dest):
        ''' copies an image to local storage, honouring the orientation '''
        image = Image.open(StringIO(urllib.urlopen(url).read()))
        exif = image._getexif()
        if exif and ORIENTATION_TAG in exif:
            orientation = exif[ORIENTATION_TAG]
            if orientation in ROTATE_VALUES:
                image = image.rotate(ROTATE_VALUES[orientation])

        folder = os.path.dirname(dest)
        if not os.path.exists(folder):
            os.mkdir(folder)
        image.save(dest, quality=100)

if __name__ == '__main__':
    imagefile = r'/home/theo/git/acaciadata/iom/media/eecc4c3f-6eeb-45a1-a7f5-640d3515e512.jpg'
    print Exif.from_file(imagefile)
    url = r'https://akvoflow-90.s3.amazonaws.com/images/eecc4c3f-6eeb-45a1-a7f5-640d3515e512.jpg'
    print Exif.from_url(url)
    dest =  r'/home/theo/git/acaciadata/iom/media/rotated.jpg'
    Exif.copyImage(url, dest)
