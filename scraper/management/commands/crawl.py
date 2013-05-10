from django.core.management.base import BaseCommand, CommandError
from scraper.tasks import crawl 

class Command(BaseCommand):
    args = '<url>'
    help = ('Kicks off celery tasks to crawl a domain starting at the'
            'specified url')

    def handle(self, *args, **options):
        if len(args) < 1:
            print 'usage: python manage.py crawl domain'
        else:
            crawl(args[0])
            
