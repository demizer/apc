'''app.py: The application control object

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os
import sys
import pprint

from pbldr import package
from pbldr import logger
from pbldr import util
from pbldr import repo
from pbldr.chroot import clean
from pbldr.logger import log

import yaml

logr = logger.getLogger(logger.NAME)


def load_configuration():
    '''Loads the json configuration from the current directory

    :returns: A dictionary with the loaded configuration

    '''
    if not os.path.exists('config.yaml'):
        logr.critical('Could not find config.yaml')
        sys.exit(1)
    with open(os.path.join('config.yaml'), 'r') as p_file:
        conf = p_file.read()
    if not conf:
        logr.critical('Could not load configuration!')
        sys.exit(1)

    try:
        yobj = yaml.load(conf)
    except yaml.scanner.ScannerError as err:
        logr.critical(str(err))
        sys.exit(1)

    try:
        yobj['chroot_path']
        yobj['chroot_copy_name']
        yobj['default_repo_target']
        yobj['keyid']
    except KeyError as err:
        logr.critical('Missing config value: ' + str(err))
        sys.exit(1)

    return yobj


class App(dict):
    '''The application storage object

    '''
    def __init__(self, args):
        self['args'] = args
        self['base_path'] = os.getcwd()
        self['user'] = os.getuid()
        self['overwrite_all'] = ''

        self.update(load_configuration())
        if self['args'].log_level:
            self['log_level'] = self['args'].log_level
        if self['log_level']:
            logr.setLevel(self['log_level'])

        if not self['package_build_order'] and not self['args'].pkgs:
            self['pkg_input'] = os.listdir(os.path.join(os.getcwd(), 'devsrc'))
        elif self['args'].pkgs:
            self['pkg_input'] = self['args'].pkgs
        else:
            self['pkg_input'] = self['package_build_order']

        # When building packages, we will need root priviledges to work with
        # the chroot environment
        if self['args'].subparser_name == 'build':
            if not util.check_root_user():
                logr.critical('The build command needs root priviledges')
                sys.exit(1)
            log('Script running with root priviledges')
            self['user'] = os.getenv('SUDO_USER')
            logr.debug('SUDO user: ' + self['user'])

        if self['args'].subparser_name in ('repo', 'source'):
            if util.check_root_user():
                logr.critical('The repo and source commands should be run '
                              'without root priviledges.')
                sys.exit(1)

        self['pkgs'] = package.Packages(self['pkg_input'])

        logr.debug('App(): \n\n' + pprint.pformat(self))

        if self['args'].subparser_name == 'build':
            self.build()
        elif self['args'].subparser_name == 'source':
            self.source()
        elif self['args'].subparser_name == 'repo':
            self.repo()

    def build(self):
        '''Builds the packages in the devsrc directory.

        '''
        package.existing_precheck(self)

        if not self['args'].sloppy:
            clean(self['chroot_path'], self['chroot_copy_name'], 'x86_64')
            clean(self['chroot_path'], self['chroot_copy_name'], 'i686')

        for _, obj in self['pkgs'].items():
            if self['args'].pkgs and obj['name'] not in self['args'].pkgs:
                continue
            if obj['arch'] == 'i686':
                # We only need to build the package source once
                package.build_source(obj)
            package.build_package(self['chroot_path'],
                                  self['chroot_copy_name'], obj,
                                  self['args'].no_check)

        log('Changing ownership of stage/ to ' + self['user'])
        if util.run('chown -R ' + self['user'] + ': stage/', True) > 1:
            logr.warning('Could change owner of stage files')

        log('Signing packages...')
        package.sign_packages(self['user'], self['keyid'], self['pkgs'])

        log('\nCleaning up log files')
        if util.run('rm -r devsrc/*/*.log 2> /dev/null', True) > 1:
            logr.warning('There was a problem cleaning the working files')

        log('Changing ownership of working directories to ' + self['user'])
        if util.run('chown -R ' + self['user'] + ': stage/ devsrc/', True) > 1:
            logr.warning('Could change owner of working directories')

    def source(self):
        '''Builds the source to the packages in the devsrc directory.

        '''
        for _, obj in self['pkgs'].items():
            if self['args'].pkgs and obj['name'] not in self['args'].pkgs:
                continue
            package.build_source(obj)

    def repo(self):
        '''Repo subcommand function. Adds built packages to a repository.

        '''
        if not os.listdir('stage'):
            logr.critical('There are no packages in the stage!')
            logr.critical('Use the build command first')
            sys.exit(1)
        rlist = []
        for _, obj in self['pkgs'].items():
            if self['args'].pkgs and obj['name'] not in self['args'].pkgs:
                continue
            rlist.append(obj)

        target = self['default_repo_target']
        if self['args'].target:
            target = self['args'].target

        repo.add_package_list(target, rlist, self['keyid'])

        if not self['args'].no_delete:
            log('Deleting stage files')
            if util.run('rm -r stage/*'.format(obj['name']), True) > 1:
                logr.warning('Could not remove stage files')
