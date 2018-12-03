.. _using-label:

Getting started
===============

To use the filabel module, a `personal token` and a labels configuration must be set up firstly.

Setting up `personal token`
---------------------------

For connecting to your GitHub repositories, the filabel module needs to configure a `personal token`. Create a token with the scope `repo` following instructions at https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/ . Then make new blank text file in the folder where do you want to run the filabel CLI application, let's give it name e.g. `credentials.cfg`. Paste into this file following lines and instead of `<your token>` insert your token (a word with 40 characters).

.. code::

   [github]
   token = <your token>

Note: Be careful! Your token is something like a password and you should not have it public accessible!

Setting up labels configuration
-------------------------------

The filabel module needs to know the rules for labeling your pull requests. These rules has to be specified in a particular file. Let's make another new blank text file in the folder where do you want to run the filabel CLI application, e.g. `labels.cfg`. You can paste there the example configuration and then modify it as you like.

.. code::

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

This configuration tells to filabel to
   * add label `frontend` to pull requests which modify files with path `*/templates/*` and `static/*`, 
   * add label `backend` to pull requests which modify files with path `logic/*`,
   * add label `docs` to pull requests which modify files with path `*.md`, `*.rst`, `*.adoc`, `LICENSE`, and `docs/*`.
   * If a pull request has label `frontend`, `backend` or `docs` even thought it does not modify corresponding file(s), the label will be deleted.


CLI application
---------------

Assuming that the configuration has beem set up in files `credentials.cfg` and `labels.cfg` as was described above, CLI application can be started executing command:

.. code::

    filabel --config-auth credentials.cfg --config-label labels.cfg

It is also possible to use a command

.. code::

    python -m filabel --config-auth credentials.cfg --config-label labels.cfg

Complete list of options and arguments:

   * `-s, --state [open|closed|all]` - Filter pull requests by state. [default: open]
   * `-d, --delete-old / -D, --no-delete-old` - Delete labels that do not match anymore. [default: True]
   * `-b, --base BRANCH` - Filter pull requests by base (pull request target) branch name.
   * `-a, --config-auth FILENAME` - File with authorization configuration.
   * `-l, --config-labels FILENAME` - File with labels configuration.
   * `--help` - Show help message and exit.

To learn how to run filabel web application or use as Python module, see the next chapters :ref:`web-app-label` and :ref:`modular-label`.

