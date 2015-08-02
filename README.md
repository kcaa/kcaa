# KCAA: KanColle Automated Assistant

**NOTE: This project has been frozen. Feel free to fork if you are
interested.**

KCAA (pronounced as *K-car*) is an assistant tool for playing
[Kancolle](http://www.dmm.com/netgame/feature/kancolle.html) (Kantai
Collection), aimed to do simple tasks for you so that you can focus on what you
really should do -- resource management and decision making.

Currently supported key features are
- Fleets and ships with vital parameters at a glance
- Assisting some routine works
- (Experimental) Remote usage, with screen capture

Planned key features are
- More flexible fleet/ship list view (filter, sort, see minor parameters)
- Saving/restoring Fleet/equipment configuration
- Making journals (log or charts) for resources
- More assists for routine works
- Polishing UI/UX

This is an English version of README. For Japanese information, see
https://github.com/kcaa/kcaa/blob/master/README-ja.md but beware that the
contents may differ.

日本語版は: https://github.com/kcaa/kcaa/blob/master/README-ja.md

# Quick Installation

## Windows

Install thirdparty softwares:

- Python 2.7: http://www.python.jp/download/
- Pillow for Python 2.7: https://pypi.python.org/pypi/Pillow/2.4.0
- Java Runtime Environment (JRE): http://www.java.com/en/download/

And make sure you have a [Chrome](https://www.google.com/chrome) browser.
You can choose Firefox as well in `tools-windows/config.bat` file (but it's
not tested recently).

Then download the latest kcaa_release_vX.X.X.zip (*X.X.X* means a version) from
[releases page](https://github.com/kcaa/kcaa/releases)
and unzip it.
Find `tools-windows/install.bat` in it and run. This will install some Python
packages required for KCAA.

Now you're done! Run `tools-windows/start_game.bat`. By default it starts up 2
Chrome browsers, one for Kancolle itself and the other for KCAA information and
control.

Ask any questions (either in English or Japanese) at
https://twitter.com/kcaadev !

## Ubuntu

First, `git clone` this repository.

    git clone https://github.com/kcaa/kcaa.git

If you don't get the meaning, download the latest kcaa_release_vX.X.X.zip
(*X.X.X* means a version) from
[releases page](https://github.com/kcaa/kcaa/releases)
and unzip it.

And make sure you have a [Chrome](https://www.google.com/chrome) browser.
You can choose Firefox as well in `tools/config.bat` file (but it's not tested
recently).

Then run `tools/install.sh`. You are required to have a sudoer permission.

    cd kcaa_vX.X.X/tools
    ./install.sh

Now you're done! Run `tools/start_game.sh`. By default it starts up 2 Chrome
browsers, one for Kancolle itself and the other for KCAA information and
control.

    ./start_game.sh

Ask any questions (either in English or Japanese) at
https://twitter.com/kcaadev !

## Mac OS

First, `git clone` this repository.

    git clone https://github.com/kcaa/kcaa.git

If you don't get the meaning, download the latest kcaa_release_vX.X.X.zip
(*X.X.X* means a version) from
[releases page](https://github.com/kcaa/kcaa/releases)
and unzip it.

And make sure you have a [Chrome](https://www.google.com/chrome) browser.
You can choose Firefox as well in `tools/config.bat` file (but it's not tested
recently).

[MacPorts](https://www.macports.org/install.php) is also required to install
necessary thirdparty libraries.

[Xcode](https://developer.apple.com/jp/xcode/downloads/) might or might not be
needed. I haven't tested an environment without Xcode.
If you haven't installed Xcode, make sure you have the latest
[Java Runtime Environment](https://java.com/en/download/).

Then run `tools-mac/install.sh`. You are required to have a sudoer permission.

    cd kcaa_vX.X.X/tools-mac
    ./install.sh

Now you're done! Run `tools-mac/start_game.sh`. By default it starts up 2
Chrome browsers, one for Kancolle itself and the other for KCAA information and
control.

    ./start_game.sh

Ask any questions (either in English or Japanese) at
https://twitter.com/kcaadev !

## Other Linux distributions

Not planned, but it should be technically feasible.
The main obstacle is to establish the installation process.
Contributions are very much appreciated.

# Important Caveats

This software is distributed *as-is*. KCAA Dev, the developer and distributor,
gives no warranty in any kind. See the license terms of this software (Apache
License, Version 2.0) below.

# License

KCAA software is licensed under Apache License, Version 2.0.

    Copyright 2014 KCAA Dev
    https://github.com/kcaa/kcaa
    Apache License, Version 2.0
    http://www.apache.org/licenses/LICENSE-2.0

KCAA software include all files and subdirectories in this repository or
directory, except under "bin" subdirectory.
Third-party softwares come with their own license terms and restrictions. See
thirdparty.txt for details.
