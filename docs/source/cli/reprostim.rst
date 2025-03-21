reprostim
=========

::

    reprostim [<global options>] <subcommand> [<arguments>]

A command-line client to execute ReproStim commands.

**Global Options**

.. option:: -l <level>, --log-level <level>

    Set the `logging level`_ to the given value; default: ``INFO``.  The level
    can be given as a case-insensitive level name or as a numeric value.

    .. _logging level: https://docs.python.org/3/library/logging.html
                       #logging-levels


.. option:: -f <format>, --log-format <format>

    Set the logging format string. For the pattern details see standard Python
    `logging.Formatter <https://docs.python.org/3/library/logging.html#formatter-objects>`_
    documentation.

**Subcommands**

* .. option:: detect-noscreen
* .. option:: list-displays
* .. option:: monitor-displays
* .. option:: qr-parse
* .. option:: timesync-stimuli
