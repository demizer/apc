'''chroot.py: Functions for working with an Arch Linux chroot environment

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import sys
import os
import re

import util
import logger
import package
from util import run
from logger import log

logr = logger.getLogger(__name__)


def clean(chroot_path, chroot_copyname):
    '''Clean the chroot copy.

    This function cleans both i686 and x86_64 chroots.

    :chroot_path: The path to the chroot
    :chroot_copyname: The chroot copy to clean
    :returns: True if successful

    '''
    for arch in ('x86_64', 'i686'):
        suffix = '32' if arch == 'i686' else '64'
        cdir = os.path.join(chroot_path, arch)
        copydir = os.path.join(cdir, chroot_copyname + suffix)
        if not os.path.exists(copydir):
            log('Creating ' + copydir)
            proc = run(['mkdir', '-p', copydir])
            if proc > 0:
                logr.warning('Error: could not create directory')
        log('\nCreating clean chroot at ' + copydir + '...')
        proc = run(['rsync', '-a', '--delete', '-q', '-W', '-x', cdir +
                    '/root/', copydir])
        if proc > 0:
            logr.critcal('Error: could not create clean chroot!')
            sys.exit(1)


def install_package(chroot_path, filepath, arch):
    """Install a package into the chroot environment.

    :chroot_path: The path to the chroot to install the package into
    :filepath: The absolute path to the package file to install
    :arch: The architecture to use when installing the package
    :returns: True if the installation was successful

    """
    fname = os.path.basename(filepath)
    log('Installing ' + fname)
    pcmd = 'pacman --needed -U /' + fname + ' --noconfirm'
    cmd = 'setarch {} mkarchroot -r "{}" {}'.format(arch, pcmd, chroot_path)
    if run(cmd, True) > 0:
        logr.warning('There was a problem installing the package!')
        return False
    return True


def install_deps(chroot_path, package_obj):
    '''Install package dependencies for the package defined by package_obj.

    :chroot_path: The path to install the dependency packages into
    :package_obj: The package object dict

    '''
    obj = package_obj
    deps = _get_dep_install_list(package_obj)
    if not deps:
        return
    logr.debug('Dependencies to install: ' + str(deps))
    for pkg in deps:
        arch = obj['arch']
        pvers = package.version_from_path(pkg)
        pname = package.name_from_path(pkg)
        if not _package_required(chroot_path, pname, pvers, arch):
            continue
        _copy_package_to_chroot(chroot_path, pkg)
        install_package(chroot_path, pkg, arch)


def _package_required(chroot_path, package_name, package_version, arch):
    '''Checks chroot_path for installed package.

    If the package is installed, then the version is compared to the version
    detected during dependency detection.

    :chroot_path: The path to the chroot
    :package_name: The name of the package
    :package_version: The version to compare with
    :arch: The architecture of the chroot
    :returns: True if the package is up-to-date

    '''
    pac_cmd = 'pacman  -Qi ' + package_name
    cmd = 'setarch {} mkarchroot -r "{}" {}'.format(arch, pac_cmd,
                                                    chroot_path)

    sout, serr, ret = util.run_with_output(cmd, True)
    if ret > 0:
        return False

    pvers = re.search('Version\s+:\s([\w\._-]+)\s', sout)
    if not pvers:
        return False

    if pvers.group(1) == package_version:
        return True

    return False


def _get_dep_install_list(package_obj):
    '''Returs a list of dependencies for installation.

    :package_obj: The package object dict
    :returns: A list of absolute file paths

    '''
    obj = package_obj
    log('Getting dependency list for ' + obj['name'])
    logr.debug('Dependencies: ' + str(obj['deps']))

    ilist = []
    for pkg in obj['deps']:
        if '=' in pkg:
            pkgname, pkgvers = pkg.split('=')
        else:
            pkgname = pkg
            pkgvers = ''
        dep = package.find_local_dep(pkgname, pkgvers, obj['arch'])
        if dep:
            ilist.append(dep)
    return ilist


def _copy_package_to_chroot(chroot_path, filepath):
    """Copies a filepath to the chroot path.

    :chroot_path: The path to the chroot
    :filepath: The absolute path of the file to copy
    :returns: True if the copy was successful

    """
    pname = os.path.basename(filepath)
    log('Copying ' + pname + ' to the chroot')
    if run(['cp', filepath, os.path.join(chroot_path, pname)]) > 0:
        logr.warning('Could not copy the package to the chroot!')
        return False
    return True
