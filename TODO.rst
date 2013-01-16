Things to Do
============
:Added: Fri Nov 16 12:53:07 PST 2012
:Modified: Tue Dec 11 12:02:35 PST 2012

This file is a list of fixes and features to implement for the Arch ZFS
packaging project. This list is ever changing and ordered my priority, the
first list item being the most important.

We use a todo list because it is distributed with the code and easier to use
offline. Bugs should be reported to the issue tracker at
github.com/demizer/archzfs/issues. A distributed issue tracker is being
investigated for the project.

The List
--------

* [TODO]: Repository handling

  * Repositories can be configured for each host, such as lithium.

  * the 'none' repository directory contains packages that do not have a
    repository.

* [TODO]: Add metadata to the PKGBUILD.GROUPS dictionary.

  This metadata will be used to control which groups are including when using
  the build, source, and repackage commands.

* [TODO]: "--repo" should copy the sources to the repo directory.

  The current repo_post_cb() uses a bash script to copy the sources. Remove
  this script and integrate it into the "--repo" argument. Still keep the
  repo_post_cb().

* [FIX]: Find a way to detect NFS mounts and stop nfs service.

  The systemd service file breaks because the nfs server is still running. I
  will have to figure out a way to detect if nfs is running on the zfs pools
  and stop the sfs kernel before stopping the service.

* [FIX]: Error on boot in initcpio hook

  "cannot import 'rpool': pool may be in use from other system use '-f' to
  import anyway.

  * This error does not happen when using "zpool export rpool" after unmounting
    pools and before reboot.

* [TODO]: post_install()

  * should call modprobe zfs. What happens during an upgrade from the repo?

  * should call systemctl daemon-reload. Check to see if this is safe first!

* [TODO]: DO NOT delete delta files! Breaks pacman if they are missing.

* [FIX]: Make md5sums search in __strip_md5sums() a regex.

* [TODO]: Test unit file for device stoppage when the device is busy.

  Currently when the device is busy the unit becomes listed as failed because
  zfs can unmount a busy device. Have it be a little more graceful.

* [TODO]: Add support for quickly uploading packages to AUR.

* [TODO]: Build packages in clean chroot environment.

  I can build an install without messing with my work environment.

* [TODO]: Update ArchWiki ZFS article with latest information about ZFS

  * Update archwiki about using package deltas.

  * Add mkinitcpio hook information to the webpage and ArchWiki:

  - How to view hook help

      mkinitcpio -H zfs

  * systemd unit file documentation

    Add the following to the webpage docs and archwiki.

    .. code-block:: console

        # systemctl enable zfs
        # systemctl start zfs
        # systemctl status zfs
        # systemctl stop zfs
        # systemctl disable zfs

  * Add documentation to ZFS wiki about hostid

    * hostid currently being used by spl can be viewed at

      cat /proc/sys/kernel/spl/hostid

    * The hostid is stored in the zfs pool itself, and if it differs from the
      hostid in /etc/hostid, zfs will refuse to import the "foreign" pool. The
      pool will have to be forcefully imported "zfs import -f" or
      spl_hostid=ffffffff will have to be used on the kernel command line.

      hostid

    * The file /etc/hostid should not ever be changed. Using /usr/bin/hostid
      reports different values every reboot.

    * Spl first trys to get the hostid from the kernel parameter, then
      /etc/hostid, last is /usr/bin/hostid.

    * My current hostid is 007f0100 with no hostid file.

    * Use zdb to see metadata of zfs pools, it also contains the hostid used when
      creating the pool.

    * When /etc/hostid does not exist, /usr/bin/hostid will output a different
      value on every reboot. If /etc/hostid does exist, then /usr/bin/hostid will
      use that value.

    * printf "\x01\x02\x03\x04" > /etc/hostid produces 01 02 03 04 in the
      /etc/hostfile on hexedit.

    * /usr/bin/hostid produces 04030201 after reading /etc/hostid. Not sure
      why... possible endianess? Checking hostid.c.

    * gethostid() returns a 32bit unique identifier. This is what should be in
      /etc/hostid

    * dmesg | grep SPL shows the hostid used when loading the SPL kernel module.

    * My hostid should be 007F0100. This is what /usr/bin/hostid returns when
      /etc/hostid does not exist.

    * /etc/hostid is not a text file and is not null terminated and is strictly 4
      bytes.

    * http://phoxis.org/2010/01/28/little-big-endian-conversion/ A nice
      explanation of lsb. Apparently I was thinking of it backwards. LSB is at
      the end on little endian systems!

    * /etc/hostid exists in the file system. Need to inform users to save it
      before installing otherwise a conflict will prevent spl-utils from being
      installed.

* [TODO]: Update archzfs webpage

  * Mention on the archzfs webpage that old package sources can be got from the
    sources/ directories.

  * systemd unit file information.

  * Update archzfs webpage with update procedure. Get it from log.rst

  * Add documentation to archzfs webpage about package deltas

    Enable UseDeltas in pacman.conf and install xdelta.

* [TODO]: Add support for pkgrel per package per group.

  When I needed to update the systemd unit file, I would've had to update all
  of the packages.

* [FIX]: If the repository is not updated, then repo_post_cb() should not be
  used.

* [TODO]: Add support for unit testing.

* [TODO]: Add proper exception support. Raise errors with error objects.  log
  should not handle exiting the script.

* [FIX]: Bugfixes for repository processing.

  - What happens when no is specified for the first conflicting package and the
    all on the next?

  - The packages are being overwritten, but git is showing no changes. Also,
    there are no packages to add or update. I need to verify this is correct.

* [FIX]: ``./build.py -m`` is still picking up old source versions.

* Change hacking.rst to hacking_manual.rst.

* Move all docs to ``docs/`` directory.

* [FIX]: Copy built package sources to ``archzfs/sources`` instead of
  ``archzfs/x86_64/sources/``.

* [FIX]: Make md5sums a PKGBUILD.py global.

* [FIX]: Documentation.

  - Update README

    - Rewrite "How to build" section. The first package to install should be
      spl-utils.

    - Add argument usage details

    - Add note about using with systemd and no specific support in ZOL

    - Add note about package signing.

    - Add note about package not being stable because of kernel differences,
      http://zfsonlinux.org/faq.html#WhyShouldIUseA64BitSystem

    - Add info to hacking.rst about building 32bit version of ZOL.

    - Figure out how to stop modified time update when fixing merge conflicts!
      When doing git rebase and editing merge conflics, the updated modified
      time causes even more problems and is not avoidable currently. The only
      way I was able to fix a merge conflict was by using the nano editor.

    - Write about making clean commits to the issue of the commit. Branches
      should be used for even the most minor changes. I spent an hour today
      splitting out 4 separate changes from my original work in adding repo
      support. It was a mess!

    - Move hacking.rst to docs directory

  - Change git workflow to github flow.

    - Master is always deployable

    - Create descriptiive branches from master

  - Update ZFS archwiki with arch-zfs building info.

  - Add notes about using this todo checklist section. TODOs should be marked
    complete in the git message and include the hacking.rst todo and the fixes
    to the code in the same commit.

  - Document branching for this project in the Git section in hacking.rst.

    - Feature branch naming; '0.1-Feature' or 'feature'?

    - Merging branches with '--no-ff'

    - Branching off fixes should be named 'Bugfix: <issue>'

* [TODO]: Make an unoficial user repository and host in the packages binaries
  directory of the github repo.

  - [TODO]: PKGBUILD.REPOPOSTCB() function called after the repo has been updated.

    This can be used to call update scripts and what not.

  - [TODO]: Repo Unit Tests

    - [TODO]: Check for errors when using 'repo-add --verify'

      If the sigs differ, ask the user what to do.

    - [TODO]: Using PKGBUILD.REPOPOSTCB(), This directory will be copied to my
              local website directory and committed.

  - [TODO]: The package sources should be copied to website project directory.

  - [TODO]: Document package signing and how to add my key in README.rst, see
    demizerone.com

* [TODO]: Make build.py:get_files_list() not reference spl, zfs.

* [TODO]: Build DKMS packages.

* [TODO]: Build git packages.

* [TODO]: Add support for chroot environments.

* [TODO]: Split up PackageGroup().__organize().

  This function has too much responsibility. It needs to be broken up into
  possibly three separate functions.

  1. if self.only_pkgbs is very nasty.

  #. When using only "--repo", it is not needed.

* [TODO]: Rebuild logging using the logging package

* [TODO]: Allow different options for separate package group

  If I want to build the split packages with repo, and only want to build the
  source packages for AUR, I have to use two separate commands. This could be
  alleviated by allowing option per package group on the command line or a
  config file.

  - [TODO]: Fix creation of binaries/aur when only creating package sources.

* [TODO]: Implement support for detecting if the sources have already been
  built. If so, notify the user.

* [TODO]: Implement error handling on makepkg failure. Check error and ask user
  if he/she wants to install the last built package and try again.

  - Test what happens when building with no install and the packages are not
    installed.

* [TODO]: From AUR comments: The initcpio hook is not good enough. You should
          wait till /dev/zfs comes up in zfs_mount_handler().

* [TODO]: Add support for building i686 packages.

  - Add ``--32bit`` argument to build 32bit packages.

  - Add ``--64bit`` argument to build 64bit packages.

    If none are specified then 64bit is the default.

  - Add ``linux32 makepkg -src --config ~/.makepkg.i686.conf`` to build
    arguments.

  - Add note to README about 32bit support being untested and potentially
    unstable due to the FAQ notes.

* [TODO]: Add support for different upstream source types such as zip. We
  currently only support '\*.tar.\*'.

* [TODO]: i18n script.

* [TODO]: Break generated md5sums lines into multiple lines.

* [TODO]: Add support for checking packages with namcap.

* [TODO]: Take a look at systemd support: https://github.com/zfsonlinux/zfs/pull/847

* [TODO]: Make bracket matching in __parse() a recursive function.

* [TODO]: Add support to detect different directory structures between spl and
          spl-split. In the split packages, it is necessary to manually delete
          directories to get them to match the spl package built with-config
          kernel (or user). The manual file handling needs to be adjusted from
          time to time, so I would like to write functionality to detect
          changes between the two packages automatically so I can be notified
          when to take a closer look without having to do it everytime there is
          an update.

* [TODO]: Auto upload package sources to AUR.

  - Look at aurvote to see how this could possibly be done.

* [TODO]: Output PDF documentation.

