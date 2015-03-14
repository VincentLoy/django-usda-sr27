from django.shortcuts import render, get_object_or_404
from django import forms
from usda.models import Food, Nutrient, FoodGroup, GramWeight, Footnote, DataSourceLink, LanguaLFactor
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404
from django.views.generic import DetailView
from decimal import *

import logging
logger = logging.getLogger(__name__)

# Create your views here.
class SearchForm( forms.Form ):
	food = forms.CharField( max_length=100, required=False )
	food_group = forms.ModelMultipleChoiceField( queryset=FoodGroup.objects.all(), required=False )

class NutrientData( object ):
	nutrient = None
	footnotes = None
	datasourcelinks = None

class WeightData( object ):
	grams = None
	description = None
	amount = None
	daily_value = None

class FoodDetail( DetailView ):
	context_object_name = 'food'
	template_name = 'usda/food.html'
	model = Food

	def get_context_data( self, **kwargs ):
		context = super( FoodDetail, self ).get_context_data( **kwargs )
		food = context[ 'food' ]
		weights = GramWeight.objects.filter( food = food )
		context[ 'weights' ] = weights
		context[ 'langual' ] = LanguaLFactor.objects.filter( food = food )
		nutrients = Nutrient.objects.filter( food = food ).order_by( 'nutrient__sr_order' )
		context[ 'nutrients' ] = nutrients
		nutrient_data = []
		for n in nutrients:
			data = NutrientData()
			data.footnotes = Footnote.objects.filter( food = food, nutrient_definition = n.nutrient )
			data.datasourcelinks = DataSourceLink.objects.filter( food = food, nutrient_definition = n.nutrient )
			data.nutrient = n
			data.weight_data = []
			weight = WeightData()
			weight.grams = Decimal( 100 )
			weight.description = 'Value per'
			data.weight_data.append( weight )
			for w in weights:
				weight = WeightData()
				weight.grams = w.weight
				weight.description = '%d %s' % ( w.amount, w.description )
				data.weight_data.append( weight )

			for w in data.weight_data:
				w.amount = w.grams / Decimal( 100 ) * n.amount
				if n.nutrient.daily_amount:
					w.daily_value = round( ( w.amount / n.nutrient.daily_amount) * 100, 1 )

			nutrient_data.append( data )
		context[ 'nutrient_data' ] = nutrient_data
		return context

def get_page( request, objs ):
	try:
		page = int( request.GET.get("page", 1 ) )
		paginator = Paginator( objs, 100)
		objs = paginator.page(page)
	except (InvalidPage, EmptyPage):
		objs = paginator.page(1)
		page = 1
	return objs, page

def main(request):
	form = SearchForm()
	food_query = Food.objects.all()

	if request.GET.items():
		form = SearchForm( request.GET )
		if form.is_valid():
			group_search = form.cleaned_data[ 'food_group' ]
			if group_search:
				fg = FoodGroup.objects.filter( pk__in=group_search ).order_by( 'name' )
				food_query = food_query.filter( food_group__in=group_search ).order_by("short_desc")

			food_search = form.cleaned_data[ 'food' ]
			if food_search:
				food_query = food_query.filter( short_desc__icontains=food_search).order_by("short_desc")
		else:
			print( 'invalid form %s' % form.errors )
			form = SearchForm()
	else:
		form = SearchForm()

	qd = request.GET.copy()
	if 'page' in qd:
		qd.pop( 'page' )
	search = qd.urlencode()
	food, page = get_page( request, food_query )
	search = request.path + '?' + search
	logger.info( 'Showing search = %s : page = %d' % ( search, page ) )
	return render(request, "usda/main.html" , { 'food' : food , 'url' : search, 'user' : request.user, 'form' : form } )

