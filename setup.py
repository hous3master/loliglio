from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3'
]

setup(
    name='loliglio',
    version='0.0.1',
    description='Loliglio allows you to extract data from the Riot API easily for your app development. Loliglio Framework is also intuitive and free.',
    long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='https://conradofmf.gitbook.io/loliglio/',
    author='Conrado Moreno',
    author_email='cfmorenofernandez@gmail.com',
    license='BSD License',
    classifiers=classifiers,
    keywords='lol',
    packages=find_packages(),
    install_requires=['']
)