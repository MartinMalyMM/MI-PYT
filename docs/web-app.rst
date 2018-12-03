.. _web-app-label:

Web application
===============

Configuration and running a filabel web application is done in different way than in case of the CLI application. Hewever, it is also simple. The main role plays a function :func:`filabel.create_app()` in a :mod:`filabel.web_app` module (see :ref:`API-label`). 

Example: Assuming that the configuration is set in files `credentials.cfg` and `labels.cfg`, the page of root of the web application can be get using these commands:

.. code::

   import os
   import filabel
   app = filabel.create_app(None)
   os.environ['FILABEL_CONFIG'] = "credentials.cfg:labels.cfg"
   app_client = app.test_client()
   app_client.get('/')

