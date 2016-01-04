'''
Created on Aug 6, 2015

@author: theo
'''
from django.core.management.base import BaseCommand
from iom.models import Meetpunt
import os
from iom.exif import Exif
from django.conf import settings

def copy(url):
    if url:
        filename = os.path.basename(url)
        Exif.copyImage(url, os.path.join(settings.PHOTO_DIR,filename))
        return (os.path.join(settings.PHOTO_URL, filename), True)
    else:
        return (url, False)
        
class Command(BaseCommand):

    args = ''
    help = 'fotos kopieren naar local storage'

    def handle(self, *args, **options):
        
        for mp in Meetpunt.objects.all():
            dest, copied = copy(mp.photo_url)
            if copied:
                print mp.photo_url, '->', dest
                mp.photo_url = dest
                mp.save()
            for w in mp.waarneming_set.all():
                dest,copied = copy(w.foto_url)
                if copied:
                    print w.foto_url, '->', dest
                    w.foto_url = dest
                    w.save()
                