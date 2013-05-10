Scraper
=======

Crawls all the urls on a specified domain and creates an entry for each in the
Django database.

Installation
------------

Create the database: python manage.py syncdb

The location of the database file is hardcoded in the settings file.  I
couldn't figure out a way around this so it will have to be modified.  Edit
website/settings.py and modify the Name field under Databases to reflect the
absolute path of the database.

Invocation
----------

Set environment variables: . ./setup 

Start RabbitMQ: sudo /usr/local/Cellar/rabbitmq/3.0.4/sbin/rabbitmq-server

Start Celery: cd $SCRAPER_HOME/scraper; celery -A tasks worker --loglevel=info

Run the scraper: cd $SCRAPER_HOME; python manage.py crawl &lt;url>

Start the admin interface: cd $SCRAPER_HOME; python manage.py runserver

Cleanup
-------

Stop Celery Tasks: celeryctl purge

Stop RabbitMQ: sudo /usr/local/Cellar/rabbitmq/3.0.4/sbin/rabbitmqctl stop

Testing
-------

Run test website: cd $SCRAPER_HOME/test; python testsite.py

Run scraper against test website: cd $SCRAPER_HOME; python manage.py crawl
http://localhost:8080/page1 



