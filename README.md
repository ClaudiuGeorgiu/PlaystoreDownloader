# PlaystoreDownloader

> A command line tool to download Android applications directly from the Google Play Store.

[![Codacy](https://api.codacy.com/project/badge/Grade/92ff2ab2c1114c7e9df13b77fac0d961)](https://www.codacy.com/app/ClaudiuGeorgiu/PlaystoreDownloader)
[![Travis Build Status](https://img.shields.io/travis/com/ClaudiuGeorgiu/PlaystoreDownloader?logo=travis)](https://travis-ci.com/ClaudiuGeorgiu/PlaystoreDownloader)
[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/d7bed1h37w7x8w6y?svg=true
)](https://ci.appveyor.com/project/ClaudiuGeorgiu/playstoredownloader)
[![Code Coverage](https://codecov.io/gh/ClaudiuGeorgiu/PlaystoreDownloader/badge.svg)](https://codecov.io/gh/ClaudiuGeorgiu/PlaystoreDownloader)
[![Python Version](https://img.shields.io/badge/Python-3.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-green.svg?logo=python&logoColor=white)](https://www.python.org/downloads/release/python-380/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/LICENSE)



**PlaystoreDownloader** is a tool for downloading Android applications directly from the Google Play Store. After an
initial (one-time) configuration, applications can be downloaded by specifying their package name.

**_This project is intended for learning purposes only and is not affiliated with Google in any way._**



## ❱ Demo

![Demo](https://raw.githubusercontent.com/ClaudiuGeorgiu/PlaystoreDownloader/master/demo.gif)



## ❱ Configuration

Before interacting with the Play Store you have to provide valid credentials and an **ANDROID ID** associated to your
account. Please modify the
[credentials.json](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/credentials.json) file and insert
the required information before trying to use this tool:

* Enter your Google email and password in the `USERNAME` and `PASSWORD` fields of the
[credentials.json](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/credentials.json) file. This
information is needed to authenticate with Google's servers.

* Use the above credentials on an Android device (real or emulated) and download at least one application using the
official Google Play Store on the device. This step is necessary in order to associate the **ANDROID ID** of the
device to your account, so that you will be able to download applications as if you were directly using your device.
Do not remove the account from the device or its **ANDROID ID** won't be valid anymore.

* Get the **ANDROID ID** of the device and fill the `ANDROID_ID` field of the
[credentials.json](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/credentials.json) file. You can
obtain the **ANDROID ID** by installing the
[Device ID](https://play.google.com/store/apps/details?id=com.evozi.deviceid) application on your device, then copy
the string corresponding to `Google Service Framework (GSF)` (use this string instead of the `Android Device ID`
presented by the application).

* In case of errors related to the authentication after the above steps, consider allowing less secure apps to access
your account by visiting <https://myaccount.google.com/lesssecureapps> (visit the link while you are logged in).

_Note that you will be able to download only the applications compatible with the device corresponding to the aforementioned **ANDROID ID** and further limitations may influence the total number of applications available for download_.



## ❱ Usage

Apart from valid Play Store credentials, the only requirement of this project is a working `Python 3.8` installation
(along with its package manager `pip`). The first thing to do is to get a local copy of this repository, so open up
a terminal in the directory where you want to save the project and clone the repository:

```Shell
$ git clone https://github.com/ClaudiuGeorgiu/PlaystoreDownloader.git
$ cd PlaystoreDownloader
```

Make sure to execute the following commands in the previously created `PlaystoreDownloader/` directory:

```Shell
$ # The usage of a virtual environment is highly recommended, e.g., virtualenv.
$ # If not using virtualenv (https://virtualenv.pypa.io/), skip the next 2 lines.
$ virtualenv -p python3.8 venv
$ source venv/bin/activate

$ # Install PlaystoreDownloader's requirements.
$ python3.8 -m pip install -r requirements.txt
```

After configuring the Play Store credentials as described in the [configuration](#-configuration), simply call the
following instruction using the package name of the app to download:

```Shell
$ python3.8 download.py "com.application.example"
```

If the download is successful, the resulting `.apk` file will be saved in the `PlaystoreDownloader/Downloads/`
directory. You can change the name and the location of the downloaded `.apk` file by providing an additional
`-o "path/to/downloaded.apk"` argument to
[download.py](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/download.py)
(type `$ python3.8 download.py --help` for more information).

Docker is also supported:

```Shell
$ # Make sure to have valid credentials inside credentials.json file before building the image.
$ docker build -t downloader .

$ # Download the selected application in the current directory.
$ docker run --rm -it -u $(id -u):$(id -g) -v "${PWD}":"/app/Downloads" downloader "com.application.example"
```



## ❱ Contributing

Questions, bug reports and pull requests are welcome on GitHub at
[https://github.com/ClaudiuGeorgiu/PlaystoreDownloader](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader).



## ❱ License

You are free to use this code under the [MIT License](https://github.com/ClaudiuGeorgiu/PlaystoreDownloader/blob/master/LICENSE).
