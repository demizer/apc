============================
APC - Arch Package Companion
============================

apc is a package building tool for Arch Linux. It builds AUR packages in a
chroot environment for i686 and x86_64 and adds the compiled packages to a
repository.

---------------
Getting started
---------------

1. Clone the repository

#. Initialize the git submodules

   .. code:: console

     $ git submodule init
     $ git submodule update

#. Setup the workspace

   The apc authors use https://github.com/divoxx/goproj for managing Go
   workspaces.

#. Set PATH

   .. code:: console

     $ export PATH="$(pwd)/bin:${PATH}"

#. Install

   .. code:: console

     $ src/apc/
     $ go install

#. Run

   .. code:: console

     $ apc

-----
Usage
-----

APC is command based.

-C, --clean     Remove compiled packages

-------
Authors
-------

Jesus Alvarez
