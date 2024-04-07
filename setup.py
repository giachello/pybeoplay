import os
from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

PACKAGE_NAME = 'pybeoplay'
HERE = os.path.abspath(os.path.dirname(__file__))
VERSION = '2.1.0'

PACKAGES = find_packages(exclude=['tests', 'tests.*', 'dist', 'ccu', 'build'])

REQUIRES = []

long_description = readme()


setup(
        name=PACKAGE_NAME,
        version=VERSION,
        license='MIT License',
        url='https://github.com/giachello/pybeoplay',
        download_url='https://github.com/giachello/pybeoplay/tarball/'+VERSION,
        author='Giovanni Iachello',
        author_email='giovanni.iachello@gmail.com',
        description='BeoPlay API for Python',
        long_description=long_description,
        long_description_content_type='text/markdown',
        readme="README.md",
        packages=PACKAGES,
        include_package_data=True,
        zip_safe=False,
        platforms='any',
        install_requires=REQUIRES,
        keywords=['beoplay', 'pybeoplay', 'B&O' , 'Bang & Olufsen'],
        classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.9'
        ],
)
