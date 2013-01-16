====================
pbldr for Arch Linux
====================
:Created: Tue Sep 18 20:56:03 PDT 2012
:Modified: Tue Jan 15 17:06:17 PST 2013

pbldr is an automated package builder and repository manager for Arch Linux
written in python.

============================================================================
package.py -- Intro
============================================================================

This script builds arch packages in a clean chroot and places them into a
pacman repository.

:: NOTICE ::

This script requires a specific directory structure and configuration file
(config.json) in order to operate properly.

============================================================================
Directory structure
============================================================================

<repo_name>/
|--archiso/
|--|--i686/
|--|--x86_64/
|--devsrc/
|--|--<package1>/
|--|--|--PKGBUILD
|--stage/
|--|--<package-version>/
|--|--|--{i686,x86_64,sources}/
|--depends/
|--|--<dependency1>
|--|--|--<dependency1.pkg.tar.xz
|--{community,core,extra,multilib}/

[archiso]

This is a special directory containing a repository to be compatible with the
current archiso release. For example, the ZFS packages require a specific
kernel version to function. When booting into the archiso to rescue a ZFS
filesystem, it would then be necessary to install the ZFS kernel modules for
the kernel contained in the archiso. As of Decemember 2012 this is kernel
3.6.8. This repository should track the current archiso release.

[devsrc]

These are the development sources to the packages of the repository. It is
useful to have them in the same directory as the repository so that the
entire repository can be versioned with a DVCS such as git.

[community|core|extra|multilib]

Arch linux has these repositories as default, and this script mimics them. So
if you think your package should be part of the community repo, like most
are, then it will be saved in the community directory as long as it is
configured in the configuration file.

[stage]

When packages are built, the complied output is saved to the stage directory
under the name of the package and version number. The reason for the stage is
to allow the packager to first inspect the package and package signatures to
determine correctness. Once correctness has been verified, the package.py can
be used to add the packages to the repository. Once this is done, the
packages in the stage directory are removed.

[Hosting the project directory]

This entire project directory can then be hosted on a webserver to allow
users to add your signed repository to their pacman.conf using the following
configuration:

[<repo_name>]
http://mycoolwebpage.com/$repo/$arch

archiso users, the can use the following:

[<repo_name>]
http://mycoolwebpage.com/$repo/archiso/$arch

Planned features
================

* Opinionated directory structure.

* Inheritable PKGBUILD variables.

* Meta PKGBUILDs.

* Repository metadata for adding completed packages to a repository.

* Clean chroot package building.

History
=======

This project and repository were once a part of the archzfs project for
packaging ZFS for Arch Linux. It has been split into two separate projects that
this repo is a submodule of.

Producers
=========

* Jesus Alvarez <jeezusjr@gmail.com>

**This project is MIT licensed**
