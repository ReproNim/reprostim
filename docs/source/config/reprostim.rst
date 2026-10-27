reprostim
=========

The ``reprostim`` CLI supports YAML configuration files.

Example
-------

.. code-block:: yaml

   reprostim:
     log_level: DEBUG

   bids_inject:
     recursive: true
     ignore_paths:
       - sub-01/ses-01

Section and option names use underscores (``bids_inject``, ``log_level``),
names with dashes are rejected.

Configuration options supplied explicitly on the command line
take precedence over values in the YAML configuration file.

See :doc:`reprostim-schema` for the complete configuration
schema reference.
