from distutils.core import setup

setup(
    name='pbldr',
    version='0.1.0',
    author='Jesus Alvarez',
    author_email='jeezusjr@gmail.com',
    packages=['pbldr'],
    scripts=['pbldr.py'],
    url='http://demizerone.com/',
    license='LICENSE',
    description='An automated packager for Arch Linux packages.',
    long_description=open('README.rst').read(),
    entry_points={'console_scripts': ['pbldr=pbldr:main'], },
)
