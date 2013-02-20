'''chroot.py: Functions for working with an Arch Linux chroot environment

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os

from pbldr import logger
from pbldr import util
from pbldr.logger import log

logr = logger.getLogger(logger.NAME)


def add_package(target, package_obj, keyid):
    '''Adds a package to a repository set in the config.

    :target: The repo target to add the package to
    :package_obj: The package object
    :keyid: A keyid to sign the repository with
    :returns: True if adding the package was successful

    '''
    log('Adding {} to {}'.format(package_obj['name'], target))
    gpat = os.path.join(target, package_obj['arch'], package_obj['name'] + '*')
    if util.run('rm -rf ' + gpat, True) > 0:
        logr.warning('Could not remove package')

    ppath = os.path.join(os.getcwd(), 'stage', package_obj['name'])
    log('Copying {} to {}'.format(package_obj['name'], target))
    rcmd = 'cp {0}*/*{1}.pkg.tar* {2}/{1}/'.format(ppath, package_obj['arch'],
                                                   target)
    if util.run(rcmd, True) > 1:
        logr.error('Could not move the package to the repo')
        return False

    # Copy the package source in stage to the repo directory
    ctmp = 'cp {0}*/*.src.tar* {1}/sources/'
    if util.run(ctmp.format(ppath, target), True) > 1:
        logr.warning('Could not move the package source to the repo')

    # Add the new packages to the repo
    rname = os.path.basename(os.getcwd())
    log('Adding {} to the {} {} repository.'.format(package_obj['filename'],
                                                    rname,
                                                    package_obj['arch']))
    rcmd = ['repo-add', '-s', '-f', '-k', keyid, rname + '.db.tar.xz',
            package_obj['filename']]
    rpath = os.path.join(target, package_obj['arch'])
    if util.run_in_path(rpath, rcmd, False) > 0:
        logr.error('Could not add the package to the repo')
        return False

    return True


def _prepare_repo_target(target, package_list, arch):
    """Prepares the repo target.

    This function first removes the old packages and then copies in the new
    packages.

    :target: The repo target
    :package_list: A list of package objects
    :arch: The architecture of the repo to prepare
    :returns: A list of packages to be added to a repository

    """
    rlist = []
    for pkg in package_list:
        if not pkg['arch'] == arch:
            continue
        gpat = os.path.join(target, arch, pkg['name'] + '*')
        star = os.path.join(target, 'sources', pkg['name'] + '*')
        if util.run('rm -rf {} {}'.format(gpat, star), True) > 0:
            logr.warning('Could not remove existing packages in ' + target)
            logr.warning('      or no packages not found')

        ppath = os.path.join(os.getcwd(), 'stage', pkg['name'])
        log('Copying {} to {}'.format(pkg['name'], target))
        rcmd = 'cp {0}*/*{1}.pkg.tar* {2}/{1}/'.format(ppath, arch, target)
        if util.run(rcmd, True) > 1:
            logr.error('Could not move the package to the repo')
            return False

        ctmp = 'cp {0}*/*.src.tar* {1}/sources/'
        if util.run(ctmp.format(ppath, target), True) > 1:
            logr.warning('Could not move the package source to the repo')

        rlist.append(pkg['filename'])

    return rlist


def add_package_list(target, package_list, keyid):
    '''Adds a list of packages to repository.

    :target: The target repo to add the packages to
    :package_list: A list of package.Package() objects
    :keyid: The GPG key to sign the repository
    :returns: True if the packages were added successfully

    '''
    log('\nAdding packages to ' + target)

    mkcmd = 'mkdir -p {}/{{i686,x86_64,sources}}'.format(target)
    if util.run(mkcmd, True, util.subprocess.DEVNULL) > 0:
        logr.warning('Could not create the repo subdirectories')

    for arch in ('x86_64', 'i686'):
        log('Adding packages to the ' + arch + ' repository.')
        rlist = _prepare_repo_target(target, package_list, arch)
        rname = os.path.basename(os.getcwd())
        rpath = os.path.join(target, arch)
        rcmd = ['repo-add', '-s', '-f', '-k', keyid, rname + '.db.tar.xz']
        rcmd.extend(rlist)
        if util.run_in_path(rpath, rcmd, False) > 0:
            logr.error('Could not add the packages to the repo')
            return False

    return True
