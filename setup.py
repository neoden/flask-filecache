from setuptools import setup


setup(
    name='Flask-FileCache',
    version='0.1',
    url='https://github.com/neoden/flask-filecache/',
    license='MIT',
    author='Lenar Imamutdinov',
    author_email='lenar.imamutdinov@gmail.com',
    description='File cache',
    long_description=__doc__,
    py_modules=['flask_filecache'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    # packages=['flask_sqlite3'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
