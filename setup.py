import setuptools
from PlaystoreDownloader.version import VERSION

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

install_reqs = parse_requirements("requirements.txt")

setuptools.setup(
     name='playstore-downloader',  
     version=VERSION,
     author="Claudiu Georgiu",
     description="PlaystoreDownloader library wrap",
     url="https://github.com/wandera/PlaystoreDownloader",
     packages=setuptools.find_packages(),
     package_dir={'PlaystoreDownloader': 'PlaystoreDownloader'},
     install_requires=install_reqs,
     classifiers=[
         "Programming Language :: Python :: 3",
         "Operating System :: POSIX :: Linux",
     ],
 )

