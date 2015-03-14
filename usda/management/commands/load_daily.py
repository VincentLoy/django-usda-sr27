import decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from usda.models import NutrientDefinition

class Command(BaseCommand):
	help = 'Imports daily recommended values.'

	def handle( self, *args, **options ):

		values = [ ( '204', 65 ), # total fat
				( '606', 20 ), # Saturated fat
				( '601', 300 ), # Cholesterol
				( '307', 2400 ), # Sodium
				( '306', 3500 ), # Potassium
				( '205', 300 ), # Total carbs
				( '291', 25 ), # Fiber
				( '203', 50 ), # Protein
				( '318', 5000 ), # Vitamin A
				( '401', 60 ), # Vitamin C
				( '301', 1000 ), # Calcium
				( '303', 18 ), # Iron
				( '324', 400 ), # Vitamin D
				( '323', 30 ), # Vitamin E
				( '430', 80 ), # Vitamin K
				( '404', '1.5' ), # Thiamin
				( '406', 20 ), # Niacin
				( '415', 2 ), # Vitamin B6
				( '417', 400 ), # Folate
				( '418', 6 ), # Vitamin B12
				( '000', 300 ), # Biotin
				( '410', 10 ), # Panthothenic acid
				( '305', 1000 ), # Phosphorus
				( '000', 150 ), # Iodine
				( '304', 400 ), # Magnesium
				( '309', 15 ), # Zinc
				( '317', 70 ), # Selenium
				( '312', 2 ), # Copper
				( '315', 2 ), # Manganese
				( '000', 120 ), # Chromium
				( '000', 75 ), # Molybdenum
				( '000', 3400 ), # Chloride
				]

		with transaction.atomic():
			for d in values:
				if d[0] == '000':
					continue
				n = NutrientDefinition.objects.get( pk=d[0] )
				n.daily_amount = decimal.Decimal( d[1] )
				n.save( update_fields=[ 'daily_amount' ] )
				print( "%s set to daily amount : %s" % ( n.name, n.daily_amount ) )

