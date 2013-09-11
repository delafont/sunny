sunny v.1.0.0
=============

Fit of dose-response model, with dynamic graph.

Authors:

* Julien Delafontaine - EPFL, BBCF
* Sunniva Foerster - Universitat Konstanz

Copyright 2013 EPFL BBCF <julien dot delafontaine at yandex dot com>

Installation
============

Required Python modules:
* Python 2.6 or 2.7
* numpy (http://numpy.scipy.org/)
* Django (https://www.djangoproject.com/)
* rpy2 (http://rpy.sourceforge.net/rpy2.html)

Required R libraries:
* R >=2.6
* drc (http://cran.r-project.org/web/packages/drc/)
* bmd (http://cran.r-project.org/web/packages/bmd/bmd.pdf)

Latest source code is available from GitHub::

    http://github.com/delafont/sunny

by clicking on "Downloads", or by cloning the git repository with::

    $ git clone https://github.com/delafont/sunny.git

Local server
============

1. Install the required libs.
2. Clone the repository ('sunny/').
3. Enter the newly created 'sunny/' directory, and run
    `python manage.py syncdb` (to create the database).
4. Run the local development server with the command
    `python manage.py runserver`. You get a message of the type:
    *Development server is running at http://127.0.0.1:8000/*
5. Start a web browser and got to `http://127.0.0.1:8000/**graph**`
    (or the adress given above). The app should start.

Apache server
=============

1. Install the required libs.
2. Clone the repository ('sunny/').
3. Enter the newly created 'sunny/' directory, and run
    `python manage.py syncdb` (to create the database).
...

Full documentation
==================

Later.

