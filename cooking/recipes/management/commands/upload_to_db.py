from optparse import make_option

from django.core.management.base import BaseCommand
from recipes.utils import fill_in_db_from_json


class Command(BaseCommand):
    help = 'Create weekly promotion for steel users'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
        filename = options.get('filename')
        print(options)
        fill_in_db_from_json(filename)
