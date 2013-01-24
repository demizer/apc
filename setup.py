from distutils.core import setup

setup(
    name='pbldr',
    version='0.3.0',
    author='Jesus Alvarez',
    author_email='jeezusjr@gmail.com',
    packages=['pbldr'],
    scripts=['pbldr/pbldr'],
    url='http://demizerone.com/',
    license='LICENSE',
    description='An automated packager for Arch Linux packages.',
    long_description=open('README.rst', encoding='UTF-8').read(),
    install_requires=['pyyaml'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.3',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Topic :: System :: Software Distribution',
        'Topic :: Utilities',
    ]
)
