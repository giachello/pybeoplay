import os
from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

PACKAGE_NAME = 'py-beoplay'
HERE = os.path.abspath(os.path.dirname(__file__))
VERSION = '0.0.8'

PACKAGES = find_packages(exclude=['tests', 'tests.*', 'dist', 'ccu', 'build'])

REQUIRES = []

setup(
        name=PACKAGE_NAME,
        version=VERSION,
        license='MIT License',
        url='https://github.com/giachello/py-beoplay',
        download_url='https://github.com/giachello/py-beoplay/tarball/'+VERSION,
        author='Giovanni Iachello',
        author_email='giac@clovermail.net',
        description='BeoPlay API for Python',
        packages=PACKAGES,
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=REQUIRES,
        keywords=['beoplay'],
        classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.4'
        ],
)
