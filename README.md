# KCAA: KanColle Automated Assistant

KCAA (pronounced as *K-car*) is an assistant tool for playing Kancolle (Kantai
Collection).

# Python server dependencies

KCAA server (`server/server_main.py`) needs following third-party PyPI
packages.

- [python-dateutil](https://pypi.python.org/pypi/python-dateutil)
- [requests](https://pypi.python.org/pypi/requests)
- [selenium](https://pypi.python.org/pypi/selenium)

All of the above can be installed via `pip`. If you use Debian-like Linux
distribution (including Ubuntu), you can install `pip` itself via `apt-get`.
For example:

    sudo apt-get install python-pip
    sudo pip install pytest python-dateutil requests selenium

You will need a root priviledge if you don't run python in a virtual
environment. If you want to create your own sandbox environment, see also
[virtualenv](https://pypi.python.org/pypi/virtualenv).

And for testing, the following packages are recommended.

- [pytest](https://pypi.python.org/pypi/pytest)
- [pytest-cov](https://pypi.python.org/pypi/pytest-cov)
- [pytest-pep8](https://pypi.python.org/pypi/pytest-pep8)
