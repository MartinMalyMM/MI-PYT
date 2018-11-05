from setuptools import setup, find_packages

with open('README') as f:
    long_description = ''.join(f.readlines())


setup(
    name='filabel_malymar9',
    version='0.3.0.4',
    description='Tool for managing of labels of GitHub pull requests',
    long_description=long_description,
    author='Martin Malý',
    author_email='malymar9@fjfi.cvut.cz',
    keywords='git,github,flask',
    license='CC0 1.0 Universal',
    url='https://github.com/MartinMalyMM/MI-PYT',
    packages=find_packages(),
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Framework :: Flask',
        'Environment :: Console',
        'Environment :: Web Environment',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Version Control',
        'Topic :: Software Development :: Version Control :: Git'
        ],
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'filabel = filabel.cli_app:main',
        ]
    },
    install_requires=['Flask', 'click', 'requests'],
    package_data={'filabel': ['templates/*.html', 'static/*.css']}, 
)
