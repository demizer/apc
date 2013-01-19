'''package.py: Functions and classes for managing packages

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os
import re
import sys
import glob
import subprocess
import pwd
from collections import OrderedDict

import logger
import util
import chroot
from logger import log

logr = logger.getLogger(__name__)

# Bash script used to get dependency lists from PKGBUILD
BASH_DEP_SCRIPT = """'arches=(i686 x86_64); \
for march in "${arches[@]}"; do \
    export CARCH="${march}"; \
    source PKGBUILD; \
    echo "## ${march}-depends ##"; \
    for dep in "${depends[@]}"; do \
        echo $dep; \
    done
    echo "## ${march}-makedepends ##"; \
    for dep in "${makedepends[@]}"; do \
        echo $dep; \
    done
    echo "## ${march}-optdepends ##"; \
    for dep in "${optdepends[@]}"; do \
        echo $dep; \
    done
done'"""


def _get_version_from_pkgbuild(package_path):
    '''Get the version number for package from the PKGBUILD.

    :package_path: The path containing the PKGBUILD.
    :returns: The version of the package contained in the PKGBUILD.

    '''
    with open(os.path.join(package_path, 'PKGBUILD'), 'r') as p_file:
        pkgb = p_file.read()
    # TODO: Sat Jan 12 08:35:48 PST 2013: Merge these two regexs
    pkgver = re.findall(r'pkgver=([\d\w.]+)\n', pkgb)
    pkgrel = re.findall(r'pkgrel=(\d+)\n', pkgb)
    return pkgver[0] + '-' + pkgrel[0] or ''


def _move_source_to_stage(package_obj):
    '''Moves a newly built package source to stage/

    :package_obj: The package object dict
    :returns: True if successful

    '''
    obj = package_obj
    try:
        src = glob.glob(os.path.join(obj['path'], '*.src.tar.gz'))[0]
    except IndexError:
        logr.warning('Could not find package source')
        return False
    logr.debug('Source glob: ' + str(src))
    sdest = os.path.dirname(obj['dest'])
    log('Moving ' + obj['filename'] + ' to stage')
    if util.run('mv {} {}'.format(src, sdest), True, subprocess.DEVNULL) > 1:
        logr.warning('Error: could not move package source')
        return False
    return True


def _move_package_to_stage(package_obj):
    '''Moves a newly built package to the stage directory.

    :package: The name of the package to move
    :arch: The architecture to target
    :returns: True if successful

    '''
    obj = package_obj
    gpat = os.path.join(obj['path'], '*-' + obj['arch'] + '.pkg.tar.xz')

    try:
        pkg = glob.glob(gpat)[0]
    except IndexError:
        logr.warning('Could not find package in ' + obj['path'])
        return False

    bdest = os.path.dirname(obj['dest'])
    if util.run('mkdir -p ' + bdest, True) > 1:
        logr.warning('Error: could not create destination directory')
        return False

    # Move the package binary and signature
    log('Moving {} to {}/'.format(obj['filename'], bdest))
    if util.run('mv {}* {}/'.format(pkg, bdest), True) > 1:
        logr.warning('Error: could not move the package to stage')
        return False
    return True


class Packages(OrderedDict):
    'An ordered dictionary of packages'

    def __init__(self, packages):
        super(Packages, self).__init__()
        self._build_package_list(packages)

    def _build_package_list(self, packages):
        '''Creates the Packages.__dict__ in a specific order.'''
        for arch in ('x86_64', 'i686'):
            for pkg in packages:
                cdir = os.getcwd()
                path = os.path.join(cdir, 'devsrc', pkg)
                vers = _get_version_from_pkgbuild(path)
                fname = '{}-{}-{}.pkg.tar.xz'.format(pkg, vers, arch)
                dest = os.path.join(cdir, 'devsrc', pkg)
                dest = os.path.join(cdir, 'stage', pkg + '-' + vers, fname)
                obj = {'name': pkg,
                       'arch': arch,
                       'path': path,
                       'filename': fname,
                       'version': vers,
                       'overwrite': True,
                       'dest': dest,
                       'deps': get_deps(path, arch), }
                self[pkg + '%%' + arch] = obj


def existing_precheck(conf):
    '''Determines if any packages already exist and asks the user for
    confirmation of overwrite.

    '''
    log('\nChecking for existing packages...')
    for _, obj in conf['pkgs'].items():
        noexist = False
        if conf['args'].p and obj['name'] not in conf['args'].p:
            continue
        if not os.path.exists(obj['dest']):
            log(obj['filename'] + ' does not exist')
            noexist = True
        elif not conf['overwrite_all']:
            mtmp = '{}{} already exists. Overwrite? [Y/y/N/n] '
            var = input(mtmp.format(logger.OUTPUT_PREFIX, obj['filename']))
            if var == 'Y':
                conf['overwrite_all'] = 'Y'
            elif var == 'y':
                obj['overwrite'] = True
            elif var == 'N':
                conf['overwrite_all'] = 'N'
                obj['overwrite'] = False
            else:
                obj['overwrite'] = False  # safety
        elif conf['overwrite_all'] == 'Y':
            obj['overwrite'] = True
        elif conf['overwrite_all'] == 'N':
            obj['overwrite'] = False

        if obj['overwrite']:
            if not noexist:
                log('Overwriting ' + obj['filename'])
            logr.debug('Answered yes to overwrite')
        else:
            log('Keeping ' + obj['filename'])
            logr.debug('Answered no to overwrite')


def build_source(package_obj):
    '''Build package source for package

    :package_obj: The package object dict
    :returns: True if successful

    '''
    obj = package_obj
    log('\nCreating source package for ' + obj['name'])
    user = util.get_owner_of_path(obj['path'])
    cmd = 'su ' + user + ' -c "makepkg -cSf"'
    if util.run_in_path(obj['path'], cmd, True) > 0:
        logr.warning('Error: Could not build source package')
        return False
    return _move_source_to_stage(obj)


def build_package(chroot_path, chroot_copyname, package_obj):
    '''Build a package

    :chroot_path: The base path to the chroot
    :chroot_copyname: The chroot copy to build in
    :package_obj: The package object dict
    :returns: True if successful

    '''
    obj = package_obj
    if not obj['overwrite']:
        return True

    log('\nProcessing {} for {}'.format(obj['name'], obj['arch']))

    reset_sums(obj)

    suffix = '32' if obj['arch'] == 'i686' else '64'
    cdir = os.path.join(chroot_path, obj['arch'])
    ccopy = chroot_copyname + suffix
    cbase = os.path.join(cdir, ccopy)
    util.run('rm -rf ' + os.path.join(cbase, 'build', '*'), True)

    chroot.install_deps(cbase, obj)

    log('Building "{}" in "{}"'.format(obj['name'], ccopy))
    cmd = ('setarch {} makechrootpkg -u -r {} -l {} '
           '-- -i'.format(obj['arch'], cdir, ccopy))
    if util.run_in_path(obj['path'], cmd, True) > 0:
        logr.critical('Error: could not build in the chroot!')
        sys.exit(1)

    return _move_package_to_stage(obj)


def get_deps(package_path, arch):
    '''Get the dependencies for package with architecture.

    :package_path: The path of the package.
    :arch: The target architecture for dependencies.
    :returns: A dictionary of dependencies.

    '''
    orig_dir = os.getcwd()
    os.chdir(package_path)
    logr.debug('Changed dir: ' + package_path)
    pname = os.path.basename(package_path)
    logr.debug('Checking dependencies for ' + pname)
    dstr, err, proc = util.run_with_output('bash -c ' + BASH_DEP_SCRIPT, True)
    if proc > 0:
        logr.critical(err)
        sys.exit(1)
    logr.debug('dep_getter.sh output:\n' + dstr)

    dlist = []
    if arch == 'i686':
        x32re = re.compile(r'## i686-[\w]+ ##\n([\w\.<>=\n-]+)\n')
        tlist = x32re.findall(dstr)
        logr.debug("i686 regex matches: " + str(tlist))
    else:
        x64re = re.compile(r'## x86_64-[\w]+ ##\n([\w\.<>=\n-]+)\n')
        tlist = x64re.findall(dstr)
        logr.debug("x86_64 regex matches: " + str(tlist))

    for dep in tlist:
        dlist.extend(dep.split('\n'))
    os.chdir(orig_dir)
    logr.debug('Changed dir: ' + package_path)
    return dlist


def reset_sums(package_obj):
    '''Get new sums and change in the PKGBUILD

    :package_obj: The package object dict
    :returns: True if successful

    '''
    log('Checking hashes')
    obj = package_obj
    orig_dir = os.getcwd()
    os.chdir(obj['path'])
    logr.debug('Changed dir: ' + obj['path'])
    user = util.get_owner_of_path(obj['path'])
    cmd = 'su ' + user + ' -c "makepkg -cg"'
    sout, serr, rcode = util.run_with_output(cmd, True)
    if rcode > 0:
        logr.warning('Return code: ' + str(rcode))
        return False

    smsum = re.findall(r'\ *(?:sha|md)\d+sums=\([\w\s\n\']+\)', sout)
    if len(smsum) > 1:
        logr.warning('md5sums regex error: More than one match!')
        logr.warning(str(smsum))
        return False

    with open('PKGBUILD', 'r') as p_file:
        pkg_conf = p_file.read()

    pfsum = re.findall(r'\ *(?:sha|md)\d+sums=\([\w\s\n\']+\)', pkg_conf)
    if pfsum and pfsum[0] != smsum[0]:
        log('Generating hashes for ' + obj['name'])
        new_pconf = pkg_conf.replace(pfsum[0], smsum[0])
        log('Writing updated PKGBULID')
        with open('PKGBUILD', 'w') as p_file:
            p_file.write(new_pconf)
    else:
        log('Hashes up-to-date for ' + obj['name'])

    os.chdir(orig_dir)
    logr.debug('Changed dir: ' + orig_dir)

    return True


def sign_packages(user, key, package_list):
    '''Signs all packages in the package list

    :user: The owner of the signing key
    :key: The signing key
    :package_list: A map of package names and data

    '''
    for _, obj in package_list.items():
        gpgenv = util.get_gpg_agent_info(user)
        suser = pwd.getpwnam(user)
        logr.debug('Username: ' + str(suser))
        os.setresuid(suser[2], suser[2], 0)
        cmd = ('HOME={} {} gpg --detach-sign -u {} --use-agent '
               '{}'.format(suser[5], gpgenv, key, obj['filename']))
        if util.run_in_path(os.path.dirname(obj['dest']), cmd, True) > 0:
            logr.warning('There was a problem signing ' + obj['filename'])
        os.setresuid(0, 0, 0)


def find_local_dep(name, version, arch):
    '''Returns a path to a dependency package.

    This function searches depends/ or stage/ only.

    :name: The name of the package.
    :version: The expected version of the dependency.
    :arch: The architecture of the package. If a package matches the name
            and version but the arch is "any", it is a considered a match
            and returned.

    '''
    ret = '{}-{}[-\d]+(?:{}|any).pkg.tar.xz(?!\.sig)'
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


def name_from_path(filepath):
    """Returns the name of the package from a filepath.

    :filepath: The path to the package file.
    :returns: The human readable name for the filepath.

    """
    name = os.path.basename(filepath)
    nre = re.search('([\w\.-]+)-[\w\.-]+-\d-(?:x86_64|i686|any).pkg.tar.xz',
                    name)
    if nre:
        return nre.group(1)


def version_from_path(filepath):
    """Returns the name of the package from a filepath.

    :filepath: The path to the package file.
    :returns: The human readable name for the filepath.

    """
    name = os.path.basename(filepath)
    nre = re.search('[\w\.-]+-([\w\.-]+-\d)-(?:x86_64|i686|any).pkg.tar.xz',
                    name)
    if nre:
        return nre.group(1)


def check_signature(package):
    '''Check package signature

    :package: The package path to check. The full path
    :returns: True if the signature is valid

    '''
    pname = os.path.basename(package)
    sigp = package + '.sig'
    if os.path.exists(sigp):
        log('Checking signature for ' + package)
        if util.run(['pacman-key', '-v', pname + '.sig']) > 0:
            logr.warning('Signature check failed!')
        return True
    return False
