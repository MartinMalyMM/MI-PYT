.. _modular-label:

Use as a Python module
======================

The filabel module contains functions which can be imported to the Python shell or your project. Firstly, a session of the request module has to be set and then it is possible to use all the fuctions in the filabel module very simply.

Prepare your session
--------------------

The session could be set using this code for example. Do not forget to replace `<your_personal_token>` with your personal token with the scope `repo` and do not have this token public available.

.. code::

   import filabel
   import requests
   token = "<your_personal_token>"
   session = requests.Session()
   session.headers = {'User-Agent': 'Python'}
   def token_auth(req):
       req.headers['Authorization'] = f'token {token}'
       return req
   session.auth = token_auth
   username = "testing_user"

.. testsetup::

   import filabel
   import requests
   import betamax
   session = requests.Session()

Find out pull requests and theirs properties
--------------------------------------------

After configuring the session, it is possible to analyse various properies of pull requests in a given GitHub repository. This can be done using functions :func:`filabel.find_pulls()`, :func:`filabel.find_pull_files()`, and :func:`filabel.find_pull_labels()` in :mod:`filabel.commons` (see :ref:`API-label`). 

Example: Assume that there are 2 pull requests in a repository `filabel-testrepo4` of the a `testing_user`. The pull request #2 is open, #1 is closed, both of them modify a file `aaaa` and do not contain any label.

.. code::

   username = "testing_user"; repo = "filabel-testrepo4"; reposlug = username + "/" + repo

   pulls_master_all = filabel.find_pulls(session, reposlug, base="master", state="all")
   pulls_master_open = filabel.find_pulls(session, reposlug, base="master", state="open")
   pulls_master_closed = filabel.find_pulls(session, reposlug, base="master", state="closed")
   print(pulls_master_all, pulls_master_open, pulls_master_closed)

   pull_files = filabel.find_pull_files(session, reposlug, pull=2)
   print(pull_files)

   labels =  [['docs', ['*.md', '*.rst', '*.adoc', 'LICENSE', 'docs/*']]]
   pull_labels = filabel.find_pull_labels(session, reposlug, pull=2, labels)
   print(pull_labels)

.. testcode::
   :hide:

   username = "testing_user"; repo = "filabel-testrepo4"; reposlug = username + "/" + repo

   with betamax.Betamax(session, cassette_library_dir='_static/cassettes') as vcr:
       vcr.use_cassette('test_github_clean.test_find_pulls[filabel-testrepo4-master-all-2]')   
       pulls_master_all = filabel.find_pulls(session, reposlug, base="master", state="all")
       vcr.use_cassette('test_github_clean.test_find_pulls[filabel-testrepo4-master-open-1]')   
       pulls_master_open = filabel.find_pulls(session, reposlug, base="master", state="open")
       vcr.use_cassette('test_github_clean.test_find_pulls[filabel-testrepo4-master-closed-1]')   
       pulls_master_closed = filabel.find_pulls(session, reposlug, base="master", state="closed")
       print(pulls_master_all, pulls_master_open, pulls_master_closed)

       vcr.use_cassette('test_github_clean.test_find_pull_files_[filabel-testrepo4-2-files6]')   
       pull_files = filabel.find_pull_files(session, reposlug, pull=2)
       print(str(pull_files))

       vcr.use_cassette('test_github_clean.test_find_pull_labels[filabel-testrepo4-2]')
       labels_setting = [['docs', ['*.md', '*.rst', '*.adoc', 'LICENSE', 'docs/*']]]
       pull_labels = filabel.find_pull_labels(session, reposlug, pull=2, labels=labels_setting)
       print(pull_labels)

.. testoutput::

   [2, 1] [2] [1]
   ['aaaa']
   []

Labels configuration
--------------------

Definition of the labels configuration by specifying quite complicated list as was shown in the previous example is not so smart. Better idea could be to save the configuration into a configuration file. If this file is in the proper format, it can be processed easily using a function :func:`filabel.find_labels` in :mod:`filabel.commons` (see :ref:`API-label`).

Assume that the configuration is saved in a text file `labels.cfg`.

.. doctest::

   >>> with open('_static/labels.cfg', 'r') as file:
   ...     content = file.read()
   >>> print(content)
   [labels]
   frontend=
       */templates/*
       static/*
   backend=logic/*
   docs=
       *.md
       *.rst
       *.adoc
       LICENSE
       docs/*
   <BLANKLINE>

Now we can use the function :func:`filabel.find_labels` to put this setting into a list with a specific order.

.. doctest::

   >>> import configparser
   >>> labels_parser = configparser.ConfigParser()
   >>> labels_parser.read_string(str(content))
   >>> labels = filabel.find_labels(labels_parser)
   >>> print(labels)
   [['frontend', ['*/templates/*', 'static/*']], ['backend', ['logic/*']], ['docs', ['*.md', '*.rst', '*.adoc', 'LICENSE', 'docs/*']]]

