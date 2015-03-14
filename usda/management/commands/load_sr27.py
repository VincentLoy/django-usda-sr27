import csv
import decimal
from optparse import make_option
import os
import sys
import zipfile
import json
import yaml
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from usda.models import Food, FoodGroup, GramWeight, NutrientDefinition, Footnote, \
						DataSource, DataDerivation, Nutrient, DataType, \
						LanguaLFactor, LanguaLFactorDescription, DataSourceLink

class Command(BaseCommand):
	help = 'Imports SR27 data.'
	option_list = BaseCommand.option_list + (
		make_option( '--usda', help='The SR27 zipfile', default='sr27.zip' ),
		make_option( '--db', action='store_true', help='Write to the database' ),
		make_option( '--json', help='Write to json file. Give the base of the filename. The table name and .json will be added.' ),
		make_option( '--yaml', help='Write to yaml file. Give the base of the filename. The table name and .yaml will be added.' ),
		make_option( '--all', action='store_true', help='Import all data.' ),
		make_option( '--food', action='store_true', help='Import foods.' ),
		make_option( '--foodgroup', action='store_true', help='Import food groups.' ),
		make_option( '--nutrientdef', action='store_true', help='Import nutrient definitions.' ),
		make_option( '--nutrient', action='store_true', help='Import nutrients.' ),
		make_option( '--weight', action='store_true', help='Import weights.' ),
		make_option( '--footnote', action='store_true', help='Import footnotes.' ),
		make_option( '--datasource', action='store_true', help='Import data sources.' ),
		make_option( '--datasourcelink', action='store_true', help='Import data source links.' ),
		make_option( '--derivation', action='store_true', help='Import data derivations.' ),
		make_option( '--langualdef', action='store_true', help='Import langual definitions.' ),
		make_option( '--langualfactor', action='store_true', help='Import langual factors.' ),
		make_option( '--datatype', action='store_true', help='Import datatypes.' ),
	)

	def do_write( self, f, zip_file, write_db, write_yaml, write_json ):
		if write_db :
			f.to_db_bulk( zip_file )
		if write_yaml:
			f.to_yaml( zip_file, '%s_%s.yaml' % ( write_yaml, f.tableName ) )
		if write_json:
			f.to_json( zip_file, '%s_%s.json' % ( write_json, f.tableName ) )

	def handle( self, *args, **options ):

		filename = options[ 'usda' ]
		if not os.path.exists( filename ):
			raise CommandError('%s does not exist' % filename )

		write_db = options[ 'db' ]
		write_yaml = options[ 'yaml' ]
		write_json = options[ 'json' ]
		do_all = options[ 'all' ]

		commands = [ ( 'foodgroup', FoodGroupFile() ),
				( 'nutrientdef', NutrientDefFile() ),
				( 'derivation', DataDerivationFile() ),
				( 'langualdef', LanguaLDescriptionFile() ),
				( 'food', FoodFile() ),
				( 'datatype', DatatypeFile() ),
				( 'langualfactor', LanguaLFactorFile() ),
				( 'nutrient', NutrientFile() ),
				( 'weight', WeightFile() ),
				( 'footnote', FootnoteFile() ),
				( 'datasource', DataSourceFile() ),
				( 'datasource', DataSourceLinkFile() ),
				]


		with zipfile.ZipFile( filename, mode='r' ) as zip_file:
			for t in commands:
				if do_all or options[ t[0] ]:
					self.do_write( t[1], zip_file, write_db, write_yaml, write_json )

class USDAFile( object ):
	DB = 1
	JSON = 2
	YAML = 3
	fileName = None
	fieldNames = ()
	tableName = None
	model = None
	delimiter = '^'
	quote = '~'
	def write( self, t, zipfile, outfile ):
		if t == self.DB:
			self.to_db( zipfile )
		elif t == self.JSON:
			self.to_json( zipfile, outfile )
		elif t == self.YAML:
			self.to_yaml( zipfile, outfile )

	def process_row( self, row ):
		return row

	def get_zip_data( self, zipfile ):
		#data = data.replace( b'\xb5', b'\xc2\xb5' )
		#data = data.replace( b'\xe9', b'\xc3\xa9' )
		data = zipfile.read( self.fileName )
		data = data.decode( encoding='ISO-8859-1' )
		#data = data.encode( 'UTF-8' ).decode( 'UTF-8' )
		#print( data )
		data = data.splitlines()
		return data

	def remove_old( self ):
		with transaction.atomic():
			# just delete the old ones like this.
			# We can't do the natural self.model.objects.all().delete()
			# because it gives errors ( too many sql variables ).
			# It also seems that you can't delete in bigger batches either
			count = 0
			while self.model.objects.count():
				ids = self.model.objects.values_list('pk')[:1]
				self.model.objects.filter(pk__in = ids).delete()
				count += 1
			print( "Deleted %d records from %s" % ( count, self.tablename ) )

	def to_db_bulk( self, zipfile ):
		data = self.get_zip_data( zipfile )
		created = 0
		i = 0
		objs = []

		self.remove_old()

		for row in csv.DictReader( data, self.fieldNames, delimiter=self.delimiter, quotechar=self.quote):
			row = self.process_row( row )
			objs.append( self.model( **row ) )
			created += 1
			if i == 10000:
				with transaction.atomic():
					self.model.objects.bulk_create( objs )
					objs = []
					i = 0
					print( "Saved 10000 records of %s. Total %d" % (self.tableName, created) )
				transaction.commit()
			i += 1
		with transaction.atomic():
			self.model.objects.bulk_create( objs )

		transaction.commit()

		print( "Created %d records of %s" % ( created, self.tableName ) )

	def to_db( self, zipfile ):
		data = self.get_zip_data( zipfile )
		created = 0
		updated = 0
		i = 0

		with transaction.atomic():
			self.remove_old()
			for row in csv.DictReader( data, self.fieldNames, delimiter=self.delimiter, quotechar=self.quote):
				row = self.process_row( row )
				o,o_created = self.model.objects.get_or_create( **row )
				if o_created:
					created += 1
				else:
					updated += 1

		transaction.commit()
		print( "Created %d, updated %d, records of %s" % ( created, updated, self.tableName ) )
		return created, updated

	def to_json( self, zipfile, outfile ):
		data = self.get_zip_data( zipfile )
		jsonobjs = []
		for row in csv.DictReader( data, self.fieldNames, delimiter=self.delimiter, quotechar=self.quote):
			jsonobjs.append( { "model": 'usda.'+self.tableName, "fields" : row } )

		with open( outfile, 'w' ) as f:
			json.dump( jsonobjs, f, indent=2 )
			print( "Created %d json objects of type %s into file %s" % ( len( jsonobjs ), self.tableName, outfile ) )

		return len( jsonobjs )

	def to_yaml( self, zipfile, outfile ):
		data = self.get_zip_data( zipfile )
		yamlobjs = []
		for row in csv.DictReader( data, self.fieldNames, delimiter=self.delimiter, quotechar=self.quote):
			yamlobjs.append(  { "model": 'usda.'+self.tableName, "fields" : row } )

		with open( outfile, 'w' ) as f:
			yaml.dump( yamlobjs, f, indent=2 )
			print( "Created %d yaml objects of type %s into file %s" % ( len( yamlobjs ), self.tableName, outfile ) )

		return len( yamlobjs )

	def to_decimal( self, row, field ):
		if row[ field ] != '':
			row[ field ] = decimal.Decimal( row[ field ] )
		else:
			row[ field ] = None

		return row

	def to_int( self, row, field ):
		if row[ field ] != '':
			row[ field ] = int( row[ field ] )
		else:
			row[ field ] = None

		return row

	def to_bool( self, row, field ):
		if row[ field ] == 'Y':
			row[ field ] = True
		else:
			row[ field ] = None
		return row

	def to_date( self, row, field ):
		if row[ field ] != '':
			m = row[field][0:2]
			y = row[field][3:7]
			row[ field ] = datetime.date( int( y ), int( m ), 1 )
		else:
			row[ field ] = None
		return row

	def to_object( self, row, field, model ):
		if row[ field ] != '':
			row[ field ] = model.objects.get( pk = row[field] )
		else:
			row[ field ] = None
		return row

class FoodGroupFile( USDAFile ):
	fileName = 'FD_GROUP.txt'
	fieldNames = ( 'food_group_code', 'name' )
	tableName = "foodgroup"
	model = FoodGroup

class NutrientDefFile( USDAFile ):
	fileName = 'NUTR_DEF.txt'
	fieldNames = ( 'code', 'units', 'tagname', 'name', 'num_decimal_places', 'sr_order' )
	tableName = "nutrientdefinition"
	model = NutrientDefinition

class DataDerivationFile( USDAFile ):
	fileName = 'DERIV_CD.txt'
	fieldNames = ( 'code', 'description' )
	tableName = 'dataderivation'
	model = DataDerivation

class LanguaLDescriptionFile( USDAFile ):
	fileName = 'LANGDESC.txt'
	fieldNames = ( 'code', 'description' )
	tableName = 'langualfactordescription'
	model = LanguaLFactorDescription

class FoodFile( USDAFile ):
	fileName = 'FOOD_DES.txt'
	fieldNames = ( 'nbd_no', 'food_group', 'long_desc', 'short_desc', 'common_name',
			'manufacturer_name', 'survey', 'refuse_desc', 'refuse_percent',
			'scientific_name', 'nitrogen_factor', 'protein_factor', 'fat_factor', 'carb_factor' )
	tableName = "food"
	model = Food

	def process_row( self, row ):
		row = self.to_object( row, 'food_group', FoodGroup )
		row = self.to_bool( row, 'survey' )
		row = self.to_int( row, 'refuse_percent' )
		row = self.to_decimal( row, 'nitrogen_factor' )
		row = self.to_decimal( row, 'protein_factor' )
		row = self.to_decimal( row, 'fat_factor' )
		row = self.to_decimal( row, 'carb_factor' )
		return row


class DatatypeFile( USDAFile ):
	fileName = 'SRC_CD.txt'
	fieldNames = ( 'code', 'description' )
	tableName = 'datatype'
	model = DataType

class LanguaLFactorFile( USDAFile ):
	fileName = 'LANGUAL.txt'
	fieldNames = ( 'food', 'factor' )
	tableName = 'langualfactor'
	model = LanguaLFactor

	def process_row( self, row ):
		row = self.to_object( row, 'food', Food )
		row = self.to_object( row, 'factor', LanguaLFactorDescription )
		return row

class NutrientFile( USDAFile ):
	fileName = 'NUT_DATA.txt'
	tableName = 'nutrient'
	model = Nutrient
	fieldNames = ( 'food', 'nutrient', 'amount', 'num_data_points',
			'std_error', 'data_type', 'derivation', 'reference_food',
			'added_nutrition', 'num_studies', 'min_value', 'max_value',
			'degrees_of_freedom', 'lower_error_bound', 'upper_error_bound',
			'statistical_comments', 'last_modified', 'confidence_code' )

	def process_row( self, row ):
		row = self.to_object( row, 'food', Food )
		row = self.to_object( row, 'nutrient', NutrientDefinition )
		row = self.to_object( row, 'data_type', DataType )
		row = self.to_object( row, 'derivation', DataDerivation )
		row = self.to_object( row, 'reference_food', Food )
		row = self.to_bool( row, 'added_nutrition' )
		row = self.to_int( row, 'num_data_points' )
		row = self.to_int( row, 'num_studies' )
		row = self.to_int( row, 'degrees_of_freedom' )
		row = self.to_decimal( row, 'std_error' )
		row = self.to_decimal( row, 'min_value' )
		row = self.to_decimal( row, 'max_value' )
		row = self.to_decimal( row, 'amount' )
		row = self.to_decimal( row, 'lower_error_bound' )
		row = self.to_decimal( row, 'upper_error_bound' )
		row = self.to_date( row, 'last_modified' )
		return row

class WeightFile( USDAFile ):
	fileName = 'WEIGHT.txt'
	tableName = 'gramweight'
	model = GramWeight
	fieldNames = ( 'food', 'sequence', 'amount', 'description'
			, 'weight', 'num_data_points', 'std_deviation' )

	next_id = 0
	def process_row( self, row ):
		row = self.to_object( row, 'food', Food )
		row = self.to_int( row, 'num_data_points' )
		row = self.to_decimal( row, 'amount' )
		row = self.to_decimal( row, 'weight' )
		row = self.to_decimal( row, 'std_deviation' )
		row[ 'id' ] = self.next_id
		self.next_id += 1
		return row

class FootnoteFile( USDAFile ):
	fileName = 'FOOTNOTE.txt'
	tableName = 'footnote'
	model = Footnote
	fieldNames = ( 'food', 'sequence', 'type_code',
			'nutrient_definition', 'text' )
	next_id = 0
	def process_row( self, row ):
		row = self.to_object( row, 'food', Food )
		row = self.to_object( row, 'nutrient_definition', NutrientDefinition )
		row[ 'id' ] = self.next_id
		self.next_id += 1
		return row

class DataSourceFile( USDAFile ):
	fileName = 'DATA_SRC.txt'
	tableName = 'datasource'
	model = DataSource
	fieldNames = ( 'code', 'authors', 'title', 'year',
			'journal', 'volume_city', 'issue_state',
			'start_page', 'end_page' )

class DataSourceLinkFile( USDAFile ):
	fileName = 'DATSRCLN.txt'
	tableName = 'datasourcelink'
	model = DataSourceLink
	fieldNames = ( 'food', 'nutrient_definition', 'data_source' )

	def process_row( self, row ):
		row = self.to_object( row, 'food', Food )
		row = self.to_object( row, 'nutrient_definition', NutrientDefinition )
		row = self.to_object( row, 'data_source', DataSource )
		return row

