import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-djaken',
    version='2.0.2',
    packages=['djaken'],
    include_package_data=True,
    license='BSD License',
    description='Djaken is a complete web-based notes application for Django.',
    long_description=README,
    url='https://github.com/ethoms/django-djaken/',
    author='Euan Thoms',
    author_email='euan@potensol.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=['Django>=1.9,<2.0','docutils>=0.12', 'pycrypto>=2.6', ],
    keywords='django notes restructuredtext rest encrypt',
)
