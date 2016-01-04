from __future__ import absolute_import
from iom.management.commands import import_akvo
from celery import shared_task
from django.conf import settings

@shared_task
def import_Akvo(user):
    command = import_akvo.Command()
    command.execute(akvo=settings.AKVOFLOW_ID,cartodb=settings.CARTODB_ID,proj=1,user=user)

@shared_task
def import_Devices():
    pass
