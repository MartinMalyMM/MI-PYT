from setuptools import setup, find_packages

with open('README') as f:
    long_description = ''.join(f.readlines())


setup(
    name='isholiday', # dulezite # je dobre vsechno pojmenovavat stejne
    version='0.1',    # dulezite
    description='Finds Czech holiday for given year',
    long_description=long_description,
    author='Ondřej Caletka',
    author_email='ondrej@caletka.cz',
    license='Public Domain',
    url='https://gist.github.com/oskar456/e91ef3ff77476b0dbc4ac19875d0555e',
    #py_modules=['isholiday'], # dulezite (uvnitr jsou soubory)
    #packages=['isholiday'] # dulezity - moduly, ktere jsou v adresarich (uvnitr jsou adresare)
    packages=find_packages(),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
        ],
    zip_safe=False, # zipy mohou dovolovat ruzne praseciny a pak to muze spadnout    
    entry_points={
        'console_scripts': [
            'isholiday_demo = isholiday.isholidays:main',
        ]
    },
    install_requires=['Flask', 'click>=6'],    
)
