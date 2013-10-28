BMC v.1.0.0
***********

Fit of dose-response model, with dynamic graph.

Authors:

* Julien Delafontaine - EPFL, BBCF (App development)
* Sunniva Foerster - Universitat Konstanz (Algorithm and R code)

Copyright 2013 EPFL BBCF
julien.delafontaine@yandex.com

For more details about the methods used, refer to the publication:
...

Requirements
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

    http://github.com/delafont/bmc

by clicking on "Download ZIP", or by cloning the git repository with one of::

    $ git clone git@github.com:delafont/bmc.git

    $ git clone http://github.com/delafont/bmc.git

    $ git clone https://github.com/delafont/bmc.git

(choose the one that works on your server).

First installation
==================

1. Install the required libs.
2. Clone the repository. Enter the newly created "bmc/" directory.
3. Enter the "sunny" folder and create a symbolic link called "settings.py" to the preferred settings file, such as::

       ln -s settings_local.py settings.py

   for local settings.
   If necessary for server deployment, create a new settings file, call it "settings_<whatever>.py" and link it the same way.
4. Return to the 'bmc/' directory and create the database::

       python manage.py syncdb

   When asked, do not create a superuser account - unless you know what you are doing.

Local server
------------

5. Run the local development server with the command
    `python manage.py runserver`. You get a message of the type:
    *Development server is running at http://127.0.0.1:8000/*
6. Start a web browser and got to `http://127.0.0.1:8000/**graph**`
    (or the adress given above). The app should start.

Apache server
-------------

5. Install the "mod_wsgi" module for Apache so that is runs Python apps.
6. Install Gunicorn: `sudo pip install gunicorn`.
    For more info on Gunicorn deployment, see http://gunicorn.org/ .
7. Edit the file "gunicorn.py" to change the server address.
8. Run the server with the command `gunicorn_django -c gunicorn.py`.
    Alternatively, it is equivalent to `gunicorn -c gunicorn.py sunny.wsgi`
9. Start a web browser and go to the address you specified in "gunicorn.py". The app should start.

Usage
=====

The expected input data is tab-delimited files with at least 3 columns:
dose - response - experiment. The experiment is an integer identifier that allows
you to put several samples (of the same treatment) in the same file.
Set it to 1 otherwise.

Click on the "Upload input file" button, load your sample and validate.
The data will be processed, a graph produced in the center, the normalized data
written in an editable table on the left, and the BMC and BMCL values
displayed in a rectangle on top of it.

Each experiment will be fitted separately and appear as separate solid curves,
and the pooled experiments will be added as a dashed curve.

Repeat to add other samples from other data files to the same figure.
One can toggle the display of each sample using the checkboxes on the right,
and edit the data separately for each sample using the radio buttons just below.
Just remember to click the "Update" button to save changes and update the graph.

The table can be edited by modifying values inside existing fields,
by creating new points (green "+" sign) or removing points (red "x" in front of each line).

One can also create a sample using only the interface.
Click on the "New custom sample" button; a popup will appear to enter the sample name.
Upon validation, a new table will appear, with a single empty line.

The "Clear all" button will erase every dataset that you entered.
To remove a single dataset, click on the red "x" in front of its name, on the right.

Finally, if the fit failed, the error will be shown beside the graph and can be reported
to he site admins - although usually it just means bad quality data.


