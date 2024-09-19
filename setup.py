import os
from setuptools import setup, find_packages

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='SPOCK_chilean',
    version='1.0.1',
    author='Elsa Ducrot',
    author_email='educrot@uliege.be',
    description=('Speculoos Observatory SChedule maKer for chilean night on SPECULOOS South Observatory'),
    keywords='',
    url='https://github.com/educrot/SPOCK_chilean/',
    packages=find_packages(),
    long_description=read('README.rst'),
    python_requires='>=3.6',
    install_requires=['pandas','numpy','astroquery','astroplan','astropy','matplotlib','datetime','pyaml',
                      'python-docx','plotly','scipy>=1.6.1,<=1.11.4','xlrd', "colorama", "ipython", "termcolor"],
)
