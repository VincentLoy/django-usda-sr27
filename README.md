# django-usda-sr27
Django project displaying the data in the USDA nutritional dababase version sr27

Also included is the daily recommended values for nutrients.

To load the database, execute :

    ./manage.py load_sr27 --usda=sr27asc.zip --db --all

This will load all the tables in sr27 into the database.
You can also write out the tables to JSON or YAML files,
as well as writing out individual tables.

To see a live example, see http://www.vagabondcoder.com/usda
