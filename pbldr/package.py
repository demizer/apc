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
import pprint

from pbldr import logger
from pbldr import util
from pbldr import chroot
from pbldr.logger import log, OUTPUT_PREFIX

logr = logger.getLogger(logger.NAME)

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
    sdest = os.path.dirname(package_obj['dest'])
    log('Moving {}*.src.tar.gz to {}'.format(package_obj['name'], sdest))
    try:
        src = glob.glob(os.path.join(package_obj['path'], '*.src.tar.gz'))[0]
    except IndexError:
        logr.warning('Could not find package source')
        return False
    logr.debug('Source glob: ' + str(src))
    log('Moving ' + package_obj['filename'] + ' to stage')
    if util.run('mv {} {}'.format(src, sdest), True, subprocess.DEVNULL) > 1:
        logr.warning('Could not move package source')
        return False
    return True


def _move_package_to_stage(package_obj):
    '''Moves a newly built package to the stage directory.

    :package: The name of the package to move
    :arch: The architecture to target
    :returns: True if successful

    '''
    bdest = os.path.dirname(package_obj['dest'])
    gpat = os.path.join(package_obj['path'], '*-*.pkg.tar.xz')
    log('Moving {}*.pkg.tar.xz to {}'.format(package_obj['name'], bdest))

    try:
        pname = glob.glob(gpat)[0]
    except IndexError:
        logr.warning('Could not find package in ' + package_obj['path'])
        return False

    if util.run('mkdir -p ' + bdest, True) > 1:
        logr.warning('Could not create destination directory')
        return False

    # Move the package binary and signature
    log('Moving {} to {}/'.format(package_obj['filename'], bdest))
    if util.run('mv {}* {}/'.format(pname, bdest), True) > 1:
        logr.warning('Could not move the package to stage')
        return False
    return True


def build_list(packages):
    plist = []
    for arch in ('x86_64', 'i686'):
        for pkg in packages:
            cdir = os.getcwd()
            path = os.path.join(cdir, 'devsrc', pkg)
            vers = _get_version_from_pkgbuild(path)
            fname = '{}-{}-{}.pkg.tar.xz'.format(pkg, vers, arch)
            dest = os.path.join(cdir, 'devsrc', pkg)
            dest = os.path.join(cdir, 'stage', pkg + '-' + vers, fname)
            obj = {'name': pkg, 'arch': arch, 'path': path, 'filename': fname,
                   'version': vers, 'overwrite': True, 'dest': dest,
                   'deps': get_deps(path, arch), 'built': False,
                   'update_sums': False, }
            plist.append(obj)

    return plist


def existing_precheck(conf):
    '''Determines if any packages already exist and asks the user for
    confirmation of overwrite.

    '''
    log('\nChecking for existing packages...')
    for pkg in conf['pkgs']:
        noexist = False
        if conf['args'].pkgs and pkg['name'] not in conf['args'].pkgs:
            continue
        if not os.path.exists(pkg['dest']):
            log(pkg['filename'] + ' does not exist')
            noexist = True
        elif not conf['overwrite_all']:
            mtmp = '{}{} already exists. Overwrite? [Y/y/N/n] '
            var = input(mtmp.format(OUTPUT_PREFIX, pkg['filename']))
            if var == 'Y':
                conf['overwrite_all'] = 'Y'
            elif var == 'y':
                pkg['overwrite'] = True
            elif var == 'N':
                conf['overwrite_all'] = 'N'
                pkg['overwrite'] = False
            else:
                pkg['overwrite'] = False  # safety
        elif conf['overwrite_all'] == 'Y':
            pkg['overwrite'] = True
        elif conf['overwrite_all'] == 'N':
            pkg['overwrite'] = False

        if pkg['overwrite']:
            if not noexist:
                log('Overwriting ' + pkg['filename'])
            logr.debug('Answered yes to overwrite')
        else:
            log('Keeping ' + pkg['filename'])
            logr.debug('Answered no to overwrite')


def build_source(package_obj):
    '''Build package source for package

    :package_obj: The package object dict
    :returns: True if successful

    '''
    log('\nCreating source package for ' + package_obj['name'])
    user = util.get_owner_of_path(package_obj['path'])
    cmd = 'su ' + user + ' -c "makepkg -cSf"'
    if util.run_in_path(package_obj['path'], cmd, True) > 0:
        logr.warning('Could not build source package')
        return False
    return _move_source_to_stage(package_obj)


def build_package(chroot_path, chroot_copyname, package_obj, check_sig):
    '''Build a package

    :chroot_path: The base path to the chroot
    :chroot_copyname: The chroot copy to build in
    :package_obj: The package object dict
    :check_sig: Check package signatures
    :returns: True if successful

    '''
    if not package_obj['overwrite']:
        return True

    log('\nProcessing {} for {}'.format(package_obj['name'],
                                        package_obj['arch']))

    if package_obj['update_sums']:
        reset_sums(package_obj)

    suffix = '32' if package_obj['arch'] == 'i686' else '64'
    cdir = os.path.join(chroot_path, package_obj['arch'])
    ccopy = chroot_copyname + suffix
    cbase = os.path.join(cdir, ccopy)
    util.run('rm -rf ' + os.path.join(cbase, 'build', '*'), True)

    chroot.install_deps(cbase, package_obj, check_sig)

    log('Building "{}" in "{}"'.format(package_obj['name'], ccopy))
    cmd = ('setarch {} makechrootpkg -r {} -l {}'.format(package_obj['arch'],
                                                         cdir, ccopy))
    if util.run_in_path(package_obj['path'], cmd, True) > 0:
        logr.critical('The package could not be built... Terminating')
        sys.exit(1)

    package_obj['built'] = True
    return _move_package_to_stage(package_obj)


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
    orig_dir = os.getcwd()
    os.chdir(package_obj['path'])
    logr.debug('Changed dir: ' + package_obj['path'])
    user = util.get_owner_of_path(package_obj['path'])
    cmd = 'su ' + user + ' -c "makepkg -cg"'
    sout, serr, rcode = util.run_with_output(cmd, True)
    if rcode > 0:
        logr.warning('Return code: ' + str(rcode))
        logr.warning('stderr: ' + str(serr))
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
        log('Generating hashes for ' + package_obj['name'])
        new_pconf = pkg_conf.replace(pfsum[0], smsum[0])
        log('Writing updated PKGBULID')
        with open('PKGBUILD', 'w') as p_file:
            p_file.write(new_pconf)
    else:
        log('Hashes up-to-date for ' + package_obj['name'])

    os.chdir(orig_dir)
    logr.debug('Changed dir: ' + orig_dir)

    return True


def sign_packages(user, key, package_list):
    '''Signs all packages in the package list

    :user: The owner of the keyid
    :key: The keyid
    :package_list: A map of package names and data

    '''
    gpgt = 'HOME={} {} gpg --detach-sign -u {} --use-agent --yes {}'
    logr.debug('Package list: ' + pprint.pformat(package_list))
    for pkg in package_list:
        gpgenv = util.get_gpg_agent_info(user)
        suser = pwd.getpwnam(user)
        logr.debug('Username: ' + str(suser))
        os.setresuid(suser[2], suser[2], 0)
        cmd = (gpgt.format(suser[5], gpgenv, key, pkg['filename']))
        if util.run_in_path(os.path.dirname(pkg['dest']), cmd, True) > 0:
            logr.warning('There was a problem signing ' + pkg['filename'])
        os.setresuid(0, 0, 0)
