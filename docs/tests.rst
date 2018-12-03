.. _tests-label:

Automatic tests
===============

There is `test` directory in the repository. The `filabel` module
could be tested using recorded "cassettes" of GitHub API (a module
`betamax` is involved`). Thus, the testing is not performed
using "live" API.

For re-recording the GitHub API "cassettes", a particular system
of repositories is required. To create this system, use a script
`tests/setup.sh`. System variables `GH_TOKEN` a `GH_USER` has to
be set. The token has to belong to the user and have the scope `repo`.
Script uses program hub (https://hub.github.com/)
which has to be installed.

.. code::

   $ export GH_USER=testing_user
   $ export GH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   $ python -m pytest -v tests

