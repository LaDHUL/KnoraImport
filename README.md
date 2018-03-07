# KnoraImport
Python wrapper over the Knora and Sipi APIs for importing data

It implements a subset of the Knora v1 and Sipi APIs, with enough features to importing projects.

Specific features of this Wrapper:
- basic statistics of the import (`class ExecStats`) to know the execution time and the number of imported items.
- retry on error (`class Knora_ER`) errors are catched and the command is retried after a recovery wait time

TODO:
- this code might be too closely bond to my needs and would require some effort to generalise
- it should be turned into a deployable python module to be reused without being copy/pasted
