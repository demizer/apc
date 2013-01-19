'''app.py: The application control object

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os
import json
import sys


import package
import logger
import chroot
import util
from logger import log, log_note


logr = logger.getLogger(__name__)


def load_configuration():
    '''Loads the json configuration from the current directory

    '''
    with open(os.path.join('config.json'), 'r') as p_file:
        conf = p_file.read()
    jobj = json.loads(conf)[0]
    return {'signing_key': jobj['SigningKey'] or '',
            'pkg_in': jobj['PackageBuildOrder'] or '',
            'log_level': jobj['LogLevel'] or '',
            'chroot_path': jobj['ChrootPath'] or '',
            'chroot_copyname': jobj['ChrootCopyName'] or '',
            'repo_path': jobj['RepoPath'] or ''}


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

        if not self['pkg_in']:
            self['pkg_in'] = os.listdir(os.path.join(os.getcwd(), 'devsrc'))

        # When building packages, we will need root priviledges to work with
        # the chroot environment
        if self['args'].subparser_name == 'build':
            if not util.check_root_user():
                logr.critical('Error: the build command needs root '
                              'priviledges')
                sys.exit(1)
            log('Script running with root priviledges')
            self['user'] = os.getenv('SUDO_USER')
            logr.debug('SUDO user: ' + self['user'])

        self['pkgs'] = package.Packages(self['pkg_in'])

        logr.debug('App(): ' + str(self))

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
        if self['args'].c:
            chroot.clean(self['chroot_path'], self['chroot_copyname'])

        for _, obj in self['pkgs'].items():
            if self['args'].p and obj['name'] not in self['args'].p:
                continue
            if obj['arch'] == 'i686':
                # We only need to build the package source once
                package.build_source(obj)
            package.build_package(self['chroot_path'], self['chroot_copyname'],
                                  obj)

        log('\nCleaning up log files')
        if util.run('rm -r devsrc/*/*.log 2> /dev/null', True) > 1:
            logr.warning('There was a problem cleaning the working files')

        log('Changing ownership of stage/ to ' + self['user'])
        if util.run('chown -R ' + self['user'] + ': stage/', True) > 1:
            logr.warning('Error: could change owner of stage files')

        log('Changing ownership of devsrc/ to ' + self['user'])
        if util.run('chown -R ' + self['user'] + ': devsrc/', True) > 1:
            logr.warning('Error: could change owner of devsrc files')

        log('Signing packages...')
        package.sign_packages(self['user'], self['signing_key'], self['pkgs'])

    def source(self):
        '''Builds the source to the packages in the devsrc directory.

        '''
        pass
        # for pkg in self.build_order:
            # if self.args.p and pkg not in self.args.p:
                # continue
            # self.build_source_package(pkg)

    def repo(self):
        '''Repo subcommand function. Adds built packages to a repository.

        '''
        pass
        # for arch in ('x86_64', 'i686'):
            # for pkg in self.build_order:
                # if self.args.p and pkg not in self.args.p:
                    # continue
                # self.add_package_to_repo(pkg, arch)
        # self.cleanup('repo')
        # if mode == 'repo':
            # log('Deleting stage files')
            # if run('rm -r {}/*'.format(spath), True) > 1:
                # logr.warning('Error: could not remove stage files')
