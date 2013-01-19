====================
pbldr for Arch Linux
====================
:Created: Tue Sep 18 20:56:03 PDT 2012
:Modified: Sat Jan 19 11:23:51 PST 2013

pbldr is a tool written in Python for building and packaging Arch Linux
packages into a repository.

*This project is MIT licensed*

-----------------
How does it work?
-----------------

* When used in a compliant directory, pbldr will build, package, and sign all
  packages in the devsrc directory.

* A configured clean chroot is required to build packages. The chroot creation
  process is detailed later in this article.

* The devtools_ package is required.

* Package sources are searched for in the devsrc.

* Built packages are saved to the stage directory.

* The user then should inspect the output in the stage directory.

* The repo subcommand can then be used to add packages from the stage to a
  targeted repository.

* Package sources are saved to {repo}/sources

* The entire directory can then be synced to a webhost, or just the
  repositories.

-------------------
Directory structure
-------------------

pbldr uses an opinionated directory structure by default. The directory and
subdirectories are used to determine the properties of the repository.

Example directory structure
===========================

::

    archzfs/
    ├── archiso
    │   ├── i686
    │   └── x86_64
    ├── core
    │   ├── i686
    │   └── x86_64
    ├── depends
    │   ├── linux-3.7.2-1-i686.pkg.tar.xz
    │   ├── linux-3.7.2-1-i686.pkg.tar.xz.sig
    │   ├── linux-3.7.2-1-x86_64.pkg.tar.xz
    │   └── linux-3.7.2-1-x86_64.pkg.tar.xz.sig
    ├── devsrc
    │   ├── spl
    │   │   ├── PKGBUILD
    │   │   └── spl.install
    │   ├── spl-utils
    │   │   ├── PKGBUILD
    │   │   └── spl-utils.hostid
    │   ├── zfs
    │   │   ├── PKGBUILD
    │   │   └── zfs.install
    │   └── zfs-utils
    │       ├── PKGBUILD
    │       ├── zfs-utils.bash-completion
    │       ├── zfs-utils.initcpio.hook
    │       ├── zfs-utils.initcpio.install
    │       └── zfs-utils.service
    ├── stage
    │   └── zfs-utils-0.6.0_rc13_3.6.11-2
    │       └── zfs-utils-0.6.0_rc13_3.6.11-2.src.tar.gz
    ├── testing
    │   ├── i686
    │   └── x86_64
    └── config.json

The repository name
===================

The basename of the directory pbldr used in is the name that will be used when
refering to the repository name.

In the example directory structure above, this name is "archzfs".

config.json
===========

The configuration file for pbldr. Without this file, pbldr would not know what
to do.

Optional values
---------------

PackageBuildOrder
    Specify a build order for building packages. If this value is missing,
    the packages in devsrc will be built in a random order.

LogLevel
    Adjust the rate of output logging. Levels include: INFO, WARNING, ERROR,
    CRITICAL, DEBUG. DEBUG is the lowest level and shows all output.

Required values
---------------

ChrootPath:
    This value indicates the base path of of the chroot. Typically this is
    /opt/chroot.

ChrootCopyName:
    When creating a copy of the chroot root, this name will be used. The
    targeted architecture of the current build process is appended to
    ChrootCopyName and the root chroot is rsync'd to this path. So if
    ChrootCopyName name is "zfs" and the current arch target is "i686', then
    the full chroot copy path will be /opt/chroot/i686/zfs32.

    In this path the chroot root (/opt/chroot/i686/root) will be copied over
    using rsync and the packages will be built and installed.

    The chroot is refreshed it the '-c' argument is passed to the build
    subcommand of pbldr.

SigningKey:
    pbldr signs all packages and repositories. This value is the KeyID of your
    GPG key.

RepoName:
    The default repo to use incase a repo target '-t' is not specified.

Example config.json
-------------------

.. code-block:: json

    [
        {
            "PackageBuildOrder": [
                "spl-utils",
                "spl",
                "zfs-utils",
                "zfs"
            ],
            "LogLevel": "DEBUG",
            "ChrootPath": "/opt/chroot",
            "ChrootCopyName": "zfs",
            "SigningKey": "0EE7A126",
            "RepoName": "core"
        }
    ]

Devsrc
======

The devsrc directory contains the package sources for building. All
subdirectories in devsrc will be built if PackageBuildOrder is not specified in
the configuration file.

Repositories
============

Arch linux has these repositories as default, and this script mimics them. So
if you think your package should be part of the community repo, like most are,
then it will be saved in the community directory as long as it is configured in
the configuration file.

stage
=====

When packages are built, the complied output is saved to the stage directory
under the name of the package and version number. The reason for the stage is
to allow the packager to first inspect the package and package signatures to
determine correctness. Once correctness has been verified, the pbldr can be
used to add the packages to the repository. Once this is done, the packages in
the stage directory are removed.

What I like to do is open a few packages in vim and inspect the .PKGINFO in the
compressed archive to make sure I didn't miss anything and that there are no
errors.

This is also a great time to use namcap_.

Chroot environments
===================

pbldr builds and installes packages into a clean chroot so that the host system
is not modified with uneeded build dependencies. This also has the added effect
of verifying the package will build on any system by detected missing
dependencies on a clean system.

Creating the chroot environment
-------------------------------

The steps below outline the creation of the of the chroot root copy that a
clean chroot is made from using rsync. This root environment is only used as a
pristine copy, no packages are installed or built inside the root copy.

You can adjust the variables used by pbldr when working with chroot
environments with the config.json configuration file in the project root
directory, or you can pass them as arguments to the script.

32bit chroot environment
~~~~~~~~~~~~~~~~~~~~~~~~

See `Buldinig 32-bit packages on a 64-bit system`_ for more information. While
this wiki article can be used as a reference, the pbldr tool expects the
directory structure defined in the following code block.

.. code-block:: console

    # mkdir -p /opt/chroot/{i686,x86_64}
    # setarch i686 mkarchroot -C "/usr/share/devtools/pacman-extra.conf" -M "/usr/share/devtools/makepkg-i686.conf" /opt/chroot/i686 base base-devel sudo

Edit pacman.conf and makepkg.conf and adjust to your desire. Specifically, the
packager and host fields.

.. code-block:: console

    # vim /opt/chroot/i686/root/etc/makepkg.conf /opt/chroot/i686/root/etc/pacman.conf

It is necessary to periodically perform updates to the chroot root copy, to do
this, you will have to chroot into the root copy and perform the update. This
same method is used to install new packages in the root copy.

.. code-block:: console

    # linux32 arch-chroot /opt/chroot/i686/root /bin/bash
    # pacman -Syu
    # pacman -S <package>
    # exit

64bit chroot environment
~~~~~~~~~~~~~~~~~~~~~~~~

The procedure for creating the 64bit chroot root environment is nearly
identical to the commands used to create the 32bit chroot environment.

.. code-block:: console

    # mkarchroot -C "/usr/share/devtools/pacman-multilib.conf" -M "/usr/share/devtools/makepkg-x86_64.conf" /opt/chroot/x86_64 base multilib-devel sudo

Edit pacman.conf and makepkg.conf and adjust to your desire. Specifically, the
packager and host fields.

.. code-block:: console

    # vim /opt/chroot/x86_64/root/etc/makepkg.conf /opt/chroot/x86_64/root/etc/pacman.conf

Periodically it is necessary to perform updates to the chroot root copy, to do
this, you will have to chroot into the root copy and perform the update. This
is the same method used to install new packages in the root copy.

.. code-block:: console

    # arch-chroot /opt/chroot/x86_64/root /bin/bash
    # pacman -Syu
    # pacman -S <package>
    # exit

-----------------------------
Hosting the project directory
-----------------------------

This entire project directory can then be hosted on a webserver to allow
users to add your signed repository to their pacman.conf using the following
configuration:

.. code-block:: sh

    [{RepoName}]
    http://mycoolwebpage.com/$repo/{RepoDirectory}/$arch

archiso users, the can use the following:

.. code-block:: sh

    [{RepoName}]
    http://mycoolwebpage.com/$repo/archiso/$arch

---------
Producers
---------

* Jesus Alvarez <jeezusjr@gmail.com>

.. _namcap: https://wiki.archlinux.org/index.php/Namcap
.. _devtools: https://www.archlinux.org/packages/extra/any/devtools
.. _Buldinig 32-bit packages on a 64-bit system: https://wiki.archlinux.org/index.php/Building_32-bit_packages_on_a_64-bit_system
