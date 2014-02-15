# KCAA: Kancolle Automated Assistant

KCAA (pronounced as K-car) is an assistant tool for playing Kancolle (Kantai
Collection).

# Python server dependencies

KCAA server (`server/server_main.py`) needs following third-party PyPI
packages.

- python-dateutil
- requests
- pytest (only for testing)

All of the above can be installed via `pip`. For example,

    pip install python-dateutil requests pytest

You may need a root priviledge if you don't run python in a virtual
environment. If you want to create your own sandbox environment, see also
http://www.virtualenv.org/.
