'''chroot.py: Functions for working with an Arch Linux chroot environment

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
# import sys
import os
import re

from pbldr import util
from pbldr import logger
from pbldr.logger import log

logr = logger.getLogger(logger.NAME)


def clean(chroot_path, chroot_copyname, arch):
    '''Clean the chroot copy.

    This function cleans both i686 and x86_64 chroots.

    :chroot_path: The path to the chroot
    :chroot_copyname: The chroot copy to clean
    :arch: The arch to clean
    :returns: True if successful

    '''
    print()  # For appearance
    suffix = '32' if arch == 'i686' else '64'
    cdir = os.path.join(chroot_path, arch)
    croot = os.path.join(chroot_path, arch, 'root')
    copydir = os.path.join(cdir, chroot_copyname + suffix)

    if not os.path.exists(copydir):
        log('Chroot copy does not exist, creating ' + copydir)
        if util.run(['mkdir', '-p', copydir]) > 0:
            logr.warning('Could not create directory')

    log('Updating the chroot root for ' + arch)
    if util.run('setarch ' + arch + ' mkarchroot -u ' + croot, True) > 0:
        logr.warning('Could not update the chroot root!')

    log('Syncing chroot root to ' + copydir + ' ...')
    rcmd = 'rsync -aqWx --delete {}/ {}'.format(croot, copydir)
    if util.run(rcmd, True) > 0:
        logr.warning('Could not sync a clean chroot!')
        return False

    log('Chroot copy clone complete')
    return True


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
    if util.run(cmd, True) > 0:
        logr.warning('There was a problem installing the package!')
        return False
    return True


def install_deps(chroot_path, package_obj, check_sig):
    '''Install package dependencies for the package defined by package_obj.

    :chroot_path: The path to install the dependency packages into
    :package_obj: The package object to install deps for
    :check_sig: If true, the package signatures will be checked

    '''
    arch = package_obj['arch']
    deps = _get_dep_install_list(package_obj)
    if not deps:
        return
    logr.debug('Dependencies to install: ' + str(deps))
    for dep in deps:
        pvers = _version_from_path(dep)
        pname = _name_from_path(dep)
        if _package_required(chroot_path, pname, pvers, arch):
            log(pname + ' is up-to-date in the chroot')
            continue
        stage_pkg = True if '/stage/' in dep else False  # hacky
        if not check_sig and not stage_pkg:
            log('Checking the signature for ' + package_obj['filename'])
            if not util.check_signature(dep + '.sig'):
                logr.error('The package signature was invalid')
                continue
        _copy_package_to_chroot(chroot_path, dep)
        install_package(chroot_path, dep, arch)


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
        logr.debug(sout.strip())
        logr.debug('Return code: ' + str(ret))
        return False

    pvers = re.search('Version\s+:\s([\w\._-]+)\s', sout)
    if pvers.group(1) == package_version:
        return True

    return False


def _get_dep_install_list(package_obj):
    '''Returs a list of dependencies for installation.

    :package_obj: The package object dict
    :returns: A list of absolute file paths

    '''
    pkg = package_obj
    log('Getting dependency list for ' + pkg['name'])
    logr.debug('Dependencies: ' + str(pkg['deps']))

    ilist = []
    for dep in pkg['deps']:
        if '=' in dep:
            pkgname, pkgvers = dep.split('=')
        else:
            pkgname = dep
            pkgvers = ''
        idep = _find_local_dep(pkgname, pkgvers, pkg['arch'])
        if idep:
            ilist.append(idep)
    return ilist


def _copy_package_to_chroot(chroot_path, filepath):
    """Copies a filepath to the chroot path.

    :chroot_path: The path to the chroot
    :filepath: The absolute path of the file to copy
    :returns: True if the copy was successful

    """
    pname = os.path.basename(filepath)
    log('Copying ' + pname + ' to the chroot')
    if util.run(['cp', filepath, os.path.join(chroot_path, pname)]) > 0:
        logr.warning('Could not copy the package to the chroot!')
        return False
    return True


def _find_local_dep(name, version, arch):
    '''Returns a path to a dependency package.

    This function searches depends/ or stage/ only.

    :name: The name of the package.
    :version: The expected version of the dependency.
    :arch: The architecture of the package. If a package matches the name
            and version but the arch is "any", it is a considered a match
            and returned.

    '''
    ret = '{}-{}[\d\.\_-]+(?:{}|any).pkg.tar.xz(?!\.sig)'
    repat = ret.format(name, version, arch)
    logr.debug('Get dep regex: ' + repat)
    stage_path = os.path.join(os.getcwd(), 'stage')
    dep_path = os.path.join(os.getcwd(), 'depends')

    # Walk the stage directory
    for dirp, _, files in os.walk(stage_path):
        for f in files:
            if re.match(repat, f):
                return os.path.join(dirp, f)

    # Walk the depends directory
    for dirp, _, files in os.walk(dep_path):
        for f in files:
            if re.match(repat, f):
                return os.path.join(dirp, f)


def _name_from_path(filepath):
    """Returns the name of the package from a filepath.

    :filepath: The path to the package file.
    :returns: The human readable name for the filepath.

    """
    name = os.path.basename(filepath)
    nre = re.search('([\w\.-]+)-[\w\.-]+-\d-(?:x86_64|i686|any).pkg.tar.xz',
                    name)
    if nre:
        return nre.group(1)


def _version_from_path(filepath):
    """Returns the name of the package from a filepath.

    :filepath: The path to the package file.
    :returns: The human readable name for the filepath.

    """
    name = os.path.basename(filepath)
    nre = re.search('[\w\.-]+-([\w\.-]+-\d)-(?:x86_64|i686|any).pkg.tar.xz',
                    name)
    if nre:
        return nre.group(1)
