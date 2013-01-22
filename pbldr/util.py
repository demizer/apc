'''util.py: Common utility functions

Copyright (c) 2013, Jesus Alvarez <jeezusjr@gmail.com>
License: MIT (See LICENSE for details)

'''
import os
import subprocess
import pwd

from pbldr import logger

logr = logger.getLogger(__name__)


def check_root_user():
    '''Returns true if the current user is root.

    :returns: True if the script is being ran as root, otherwise false.

    '''
    return False if not os.getuid() == 0 else True


def run(command, shell=False, stderr=None):
    '''Run a command.

    :command: The command to run as a list.
    :shell: If true the command is run in a shell.
    :returns: The process returncode.

    '''
    logr.info(str(command))
    return subprocess.call(command, shell=shell, stderr=stderr)


def run_with_output(command, shell=False):
    '''Run a command gathering its output.

    :command: The command to run as a list.
    :shell: If true the command is run in a shell.
    :returns: A tuple of stdout, stderr, returncode. stdout and stderr are
              returned as strings.

    '''
    logr.info(str(command))
    proc = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    sout, serr = proc.communicate()
    return sout.decode(), serr.decode(), proc.returncode


def run_in_path(path, command, shell=True, stderr=None):
    '''Run a command in a path.

    :path: The path to run the command in.
    :command: The command to run.

    '''
    orig_dir = os.getcwd()
    os.chdir(path)
    logr.debug('Changed dir: ' + path)
    logr.info(str(command))
    ret = subprocess.call(command, shell=shell, stderr=stderr)
    os.chdir(orig_dir)
    logr.debug('Changed dir: ' + orig_dir)
    return ret


def get_gpg_agent_info(user):
    '''Gets the GPG_AGENT_INFO for user and returns it.

    '''
    user_home = os.path.expanduser('~' + user)
    genv_path = os.path.join(user_home, '.gnupg', 'gpg-agent.env')
    logr.debug('gpg-agent.env path: ' + genv_path)
    if not os.path.exists(genv_path):
        logr.warning(genv_path + ' not found')
        logr.warning('There will be problems signing packages')
        return ''
    with open(genv_path, 'r') as e_file:
        gpg_environ = e_file.read()
    logr.debug('GPG_AGENT_INFO: ' + gpg_environ.strip())
    return gpg_environ.strip()


def get_owner_of_path(path):
    '''Returns the owner of a path.

    :path: The path
    :returns: The owner as a string

    '''
    stat = os.stat(path)
    uid = stat.st_uid
    return pwd.getpwuid(uid)[0]
