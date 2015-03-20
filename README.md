# django-usda-sr27
Django project displaying the data in the USDA nutritional database version sr27

## Requirements

Written with python3 and Django 1.7

## Installation

* Copy the `usda` directory to somewhere in your PYTHONPATH.
* Add 'usda' to `INSTALLED_APPS` in your `settings.py`
* Add `url( r'^usda/', include( 'usda.urls', namespace="usda" ))` to your `urlpatterns` in `urls.py`

## Importing data

Download the USDA zipfile [sr27asc.zip](https://www.ars.usda.gov/SP2UserFiles/Place/12354500/Data/SR27/dnload/sr27asc.zip)

To load the database into Django, execute :

    ./manage.py load_sr27 --usda=sr27asc.zip --db --all

This will probably take a long time. It is also
recommended to set `DEBUG = False` in your `settings.py`
so that it doesn't consume huge amounts of memory.

You can also write out individual tables to JSON or YAML files or
import individual tables into the database. For a complete list of options, try:

    ./manage.py load_sr27 --help

You can sample it on a [live site](http://www.vagabondcoder.com/usda)
