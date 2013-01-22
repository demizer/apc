'''app.py: The application control object

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os
import json
import sys
import pprint

from pbldr import package
from pbldr import logger
from pbldr import util
from pbldr import repo
from pbldr.chroot import clean
from pbldr.logger import log, log_note

logr = logger.getLogger(__name__)


def load_configuration():
    '''Loads the json configuration from the current directory

    '''
    with open(os.path.join('config.json'), 'r') as p_file:
        conf = p_file.read()
    jobj = json.loads(conf)[0]
    return {'keyid': jobj['KeyID'] or '',
            'pkg_in': jobj['PackageBuildOrder'] or '',
            'log_level': jobj['LogLevel'] or '',
            'chroot_path': jobj['ChrootPath'] or '',
            'chroot_copyname': jobj['ChrootCopyName'] or '',
            'repo_target': jobj['DefaultRepoTarget'] or ''}


class App(dict):
    '''The application storage object

    '''
    def __init__(self, args):
        self.update(load_configuration())
        logger.init_logging(self['log_level'])
        log_note('Welcome!', 'pbldr', 'white', 'bgred')

        self['args'] = args
        self['base_path'] = os.getcwd()
        self['user'] = os.getuid()
        self['overwrite_all'] = ''

        if not self['pkg_in'] and not self['args'].pkgs:
            self['pkg_in'] = os.listdir(os.path.join(os.getcwd(), 'devsrc'))
        elif self['args'].pkgs:
            self['pkg_in'] = self['args'].pkgs

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

        self['pkgs'] = package.Packages(self['pkg_in'])

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
        for _, obj in self['pkgs'].items():
            if self['args'].pkgs and obj['name'] not in self['args'].pkgs:
                continue
            if not self['args'].sloppy:
                clean(self['chroot_path'], self['chroot_copyname'],
                      obj['arch'])
            if obj['arch'] == 'i686':
                # We only need to build the package source once
                package.build_source(obj)
            package.build_package(self['chroot_path'], self['chroot_copyname'],
                                  obj)

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

        target = self['repo_target']
        if self['args'].target:
            target = self['args'].target

        repo.add_package_list(target, rlist, self['keyid'])

        if not self['args'].no_delete:
            log('Deleting stage files')
            if util.run('rm -r stage/*'.format(obj['name']), True) > 1:
                logr.warning('Could not remove stage files')
