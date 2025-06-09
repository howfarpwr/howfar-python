# HowFar Python Library

This is a set of tools and code for communicating with a HowFar device. The communication takes
place over USB Mass Storage thanks to the UF2 protocol.

## Installation

Use any standard Python package installation method. For using the command line tools I strongly
recommended [pipx](https://pipx.pypa.io/stable/installation/) in order to isolate the installation
from the rest of the system:

```commandline
python -m pip install --user pipx
pipx ensurepath
pipx install c:\Users\kosma\Desktop\howfar\howfar-python 
```

Test the installation by running `howfar-read` and `howfar-conf`.

## Configuring the device before examination

Run the following, substituting the device drive letter as needed:

```sh
howfar-conf d:\optoconf.uf2 flagEraseDatabase=1
```

Extra settings can also be added to override the defaults:

```sh
howfar-conf d:\optoconf.uf2 flagEraseDatabase=1 measurementInterval=60 tofTimingBudget=60
```

This commands performs the following:

1. Uploads settings; they will be shown on screen for reference.
2. Synchronizes the device date and time to the computer date and time.
3. Deletes existing data if requested via `flagEraseDatabase`.

## Retrieving device data after examination

Pulling data directly from a device:

```
howfar-read d:\optodata.uf2 c:\science\optodata.csv
```

Copying the raw binary data and unpacking it later:

```sh
copy d:\optodata.uf2 c:\science\optodata.uf2
# sometime later
howfar-read c:\science\optodata.uf2 c:\science\optodata.csv

```

Note that downloading data from the device takes about 30 seconds due to firmware limitations.

## Performing batch examinations

In scenarios where a significant number of devices is deployed in the field, it can become tricky to track
which device corresponds to which user. In such situation, each device can be configured with a custom
8-character identifier when setting up an examination:

```sh
howfar-conf d:\optoconf.uf2 flagEraseDatabase=1 examinationIdentifier=PATIENT0 ...other settings...
```

This identifier will be used as the filename of the exposed UF2 data:

```
 Volume in drive D is OPTODATA
 Volume Serial Number is 0042-0042

 Directory of D:\

15/09/2024  01:39               148 INFO_UF2.TXT
15/09/2024  01:39               102 INDEX.HTM
15/09/2024  01:39         4,194,304 PATIENT0.UF2
               3 File(s)      4,194,554 bytes
               0 Dir(s)      29,226,496 bytes free
```

## Graphical User Interface

Implementing a GUI is outside the scope of this library. The user is welcome to implement a custom GUI. 

## Library usage

Use your IDE's package manager to install this library - point the package manager to this directory, e.g.:

```shell
source ~/venv-howfar/bin/activatae
pip install ~/Downloads/howfar/howfar-python
```

For code usage examples, see `howfar.cli.*`.

## License

This project is licensed under MIT license, see [COPYING](COPYING).

This project uses Microsoft UF2 code, licensed under MIT license.

This project reimplements parts of [RingFS](https://github.com/cloudyourcar/ringfs),
licensed under WTFPL license.
