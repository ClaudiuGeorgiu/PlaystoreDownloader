import setuptools
from playstore_downloader.version import VERSION


setuptools.setup(
     name='playstore-downloader',  
     version=VERSION,
     author="Claudiu Georgiu",
     description="PlaystoreDownloader library wrap",
     url="https://github.com/wandera/PlaystoreDownloader",
     packages=setuptools.find_packages(),
     package_dir={'PlaystoreDownloader': 'PlaystoreDownloader'},
     install_requires=[
        'Flask==1.1.2',
        'Flask-SocketIO==4.3.1',
        'protobuf==3.13.0',
        'pycryptodome==3.9.8',
        'pytest-cov==2.10.1',
        'requests==2.24.0',
        'tqdm==4.50.2'
     ],
     classifiers=[
         "Programming Language :: Python :: 3",
         "Operating System :: POSIX :: Linux",
     ],
 )

