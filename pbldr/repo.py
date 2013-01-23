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
    obj = package_obj
    log('Adding {} to {}'.format(obj['name'], target))
    gpat = os.path.join(target, obj['arch'], obj['name'] + '*')
    if util.run('rm -rf ' + gpat, True) > 0:
        logr.warning('Could not remove package')

    ppath = os.path.join(os.getcwd(), 'stage', obj['name'])
    log('Copying {} to {}'.format(obj['name'], target))
    rcmd = 'cp {0}*/*{1}.pkg.tar* {2}/{1}/'.format(ppath, obj['arch'], target)
    if util.run(rcmd, True) > 1:
        logr.error('Could not move the package to the repo')
        return False

    # Copy the package source in stage to the repo directory
    ctmp = 'cp {0}*/*.src.tar* {1}/sources/'
    if util.run(ctmp.format(ppath, target), True) > 1:
        logr.warning('Could not move the package source to the repo')

    # Add the new packages to the repo
    rname = os.path.basename(os.getcwd())
    log('Adding {} to the {} {} repository.'.format(obj['filename'], rname,
                                                    obj['arch']))
    rcmd = ['repo-add', '-s', '-k', keyid, rname + '.db.tar.xz',
            obj['filename']]
    if util.run_in_path(os.path.join(target, obj['arch']), rcmd, False) > 0:
        logr.error('Could not add the package to the repo')
        return False

    return True


def add_package_list(target, package_list, keyid):
    '''Adds a list of packages to repository.

    :target: The target repo to add the packages to
    :package_list: A list of package.Package() objects
    :keyid: The GPG key to sign the repository
    :returns: True if the packages were added successfully

    '''
    log('\nAdding packages to ' + target)
    rlist = []
    for pkg in package_list:
        gpat = os.path.join(target, pkg['arch'], pkg['name'] + '*')
        if util.run('rm -rf ' + gpat, True) > 0:
            logr.warning('Could not remove existing packages at ' + gpat)
            logr.warning('      or no packages not found')

        ppath = os.path.join(os.getcwd(), 'stage', pkg['name'])
        log('Copying {} to {}'.format(pkg['name'], target))
        rcmd = 'cp {0}*/*{1}.pkg.tar* {2}/{1}/'.format(ppath, pkg['arch'],
                                                       target)
        if util.run(rcmd, True) > 1:
            logr.error('Could not move the package to the repo')
            return False

        # Copy the package source in stage to the repo directory
        ctmp = 'cp {0}*/*.src.tar* {1}/sources/'
        if util.run(ctmp.format(ppath, target), True) > 1:
            logr.warning('Could not move the package source to the repo')

        rlist.append(pkg['filename'])

    if rlist:
        rname = os.path.basename(os.getcwd())
        log('Adding {} to the {} {} repository.'.format(pkg['filename'], rname,
                                                        pkg['arch']))
        rpath = os.path.join(target, pkg['arch'])
        rcmd = ['repo-add', '-s', '-k', keyid, rname + '.db.tar.xz']
        rcmd.extend(rlist)
        if util.run_in_path(rpath, rcmd, False) > 0:
            logr.error('Could not add the packages to the repo')
            return False

        return True

    return False
