from django.db import models
from django.core.urlresolvers import reverse

# Create your models here.

class FoodGroup(models.Model):
	food_group_code = models.CharField(max_length=4, primary_key=True)
	name = models.CharField(max_length=60)
	def __str__( self ):
		return self.name

class Food(models.Model):
	nbd_no = models.CharField(max_length=5, primary_key=True)
	food_group = models.ForeignKey( FoodGroup, to_field='food_group_code' )
	long_desc = models.CharField(max_length=200)
	short_desc = models.CharField(max_length=60)
	common_name = models.CharField(max_length=100,blank=True)
	manufacturer_name = models.CharField(max_length=65,blank=True)
	survey = models.NullBooleanField(blank=True,null=True)
	refuse_desc = models.CharField(max_length=135,blank=True)
	refuse_percent = models.IntegerField(blank=True,null=True)
	scientific_name = models.CharField(max_length=65,blank=True)
	nitrogen_factor = models.DecimalField(max_digits=6,decimal_places=2,blank=True,null=True)
	protein_factor = models.DecimalField(max_digits=6,decimal_places=2,blank=True, null=True)
	fat_factor = models.DecimalField(max_digits=6,decimal_places=2,blank=True, null=True)
	carb_factor = models.DecimalField(max_digits=6,decimal_places=2,blank=True, null=True)

	def __str__( self ):
		return self.short_desc

	def get_absolute_url( self ):
		return reverse( 'usda:show_food', args=[ self.nbd_no ] )

class LanguaLFactorDescription(models.Model):
	code = models.CharField(max_length=5, primary_key=True)
	description = models.CharField(max_length=140)
	food = models.ManyToManyField( Food, through='LanguaLFactor' )

class LanguaLFactor(models.Model):
	food = models.ForeignKey( Food )
	factor = models.ForeignKey( LanguaLFactorDescription )

class DataType(models.Model):
	code = models.CharField(max_length=2, primary_key=True)
	description = models.CharField(max_length=60)

class DataDerivation(models.Model):
	code = models.CharField(max_length=4, primary_key=True)
	description = models.CharField(max_length=120)

class NutrientDefinition(models.Model):
	code = models.CharField(max_length=3, primary_key=True )
	food = models.ManyToManyField( Food, through='Nutrient', through_fields=( 'nutrient', 'food') )
	units = models.CharField(max_length=7)
	tagname = models.CharField(max_length=20, blank=True)
	name = models.CharField(max_length=60)
	num_decimal_places = models.IntegerField()
	sr_order = models.IntegerField()
	daily_amount = models.DecimalField(max_digits=13,decimal_places=3, blank=True, null=True )

	def __str__( self ):
		return self.name

class Nutrient(models.Model):
	food = models.ForeignKey( Food, to_field='nbd_no' )
	nutrient = models.ForeignKey( NutrientDefinition, to_field='code' )
	amount = models.DecimalField(max_digits=13,decimal_places=3)
	num_data_points = models.IntegerField()
	std_error = models.DecimalField(max_digits=11,decimal_places=3, blank=True, null=True)
	data_type = models.ForeignKey( DataType, to_field='code' )
	derivation = models.ForeignKey( DataDerivation, blank=True, null=True, to_field='code' )
	reference_food = models.ForeignKey( Food, blank=True, null=True, related_name='reference_food', to_field='nbd_no' )
	added_nutrition = models.NullBooleanField( blank=True, null=True )
	num_studies = models.IntegerField( blank=True,null=True )
	min_value = models.DecimalField(max_digits=13,decimal_places=3, blank=True, null=True )
	max_value = models.DecimalField(max_digits=13,decimal_places=3, blank=True, null=True )
	degrees_of_freedom = models.IntegerField( blank=True, null=True )
	lower_error_bound = models.DecimalField(max_digits=13,decimal_places=3, blank=True, null=True )
	upper_error_bound = models.DecimalField(max_digits=13,decimal_places=3, blank=True, null=True )
	statistical_comments = models.CharField(max_length=10, blank=True)
	last_modified = models.DateField( blank=True, null=True )
	confidence_code = models.CharField(max_length=1, blank=True)

	class Meta:
		unique_together = ( 'food', 'nutrient' )

class GramWeight(models.Model):
	food = models.ForeignKey( Food, to_field='nbd_no' )
	sequence = models.CharField(max_length=2 )
	amount = models.DecimalField(max_digits=8,decimal_places=3)
	description = models.CharField(max_length=84)
	weight = models.DecimalField(max_digits=8,decimal_places=1)
	num_data_points = models.IntegerField(blank=True, null=True)
	std_deviation = models.DecimalField(max_digits=10,decimal_places=3, blank=True, null=True )
	id = models.AutoField( primary_key=True )

	def __str__( self ):
		return amount

class Footnote(models.Model):
	food = models.ForeignKey( Food, to_field='nbd_no' )
	sequence = models.CharField(max_length=4)
	type_code = models.CharField(max_length=1)
	nutrient_definition = models.ForeignKey( NutrientDefinition, blank=True, null=True, to_field='code' )
	text = models.CharField(max_length=200)
	id = models.AutoField( primary_key=True )


class DataSource(models.Model):
	code = models.CharField(max_length=6,primary_key=True)
	authors = models.CharField(max_length=255, blank=True )
	title = models.CharField(max_length=255 )
	year = models.CharField(max_length=4, blank=True )
	journal = models.CharField(max_length=135, blank=True )
	volume_city = models.CharField(max_length=16, blank=True )
	issue_state = models.CharField(max_length=5, blank=True )
	start_page = models.CharField(max_length=5, blank=True )
	end_page = models.CharField(max_length=5, blank=True )
	nutrient = models.ManyToManyField( NutrientDefinition, through='DataSourceLink' )

	def __str__( self ):
		return title

class DataSourceLink(models.Model):
	food = models.ForeignKey( Food, to_field='nbd_no' )
	nutrient_definition = models.ForeignKey( NutrientDefinition, to_field='code' )
	data_source = models.ForeignKey( DataSource, to_field='code' )
