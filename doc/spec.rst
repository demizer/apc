====================================
Arch Package Companion Specification
====================================
:Modified: Fri Jan 03 11:59:27 PDT 2014

Arch Package Companion is a HTML5 application for managing packages in Arch
Linux. APC incorporates the Arch User Repository and builds the packages in a
systemd container. APC shows the user up-to-date information about the package
state of the host system in a clean HTML5 interface.

-----
INBOX
-----

* Figure out where to add information about the local repository management.

* Add PKGBUILD editing to feature overview.

* Add automatic AUR updates to feature overview.

* Add process output display to feature overview.

* Add chroot management to the feature list.

------------
Requirements
------------

Overview
========

* A frontend to Pacman with AUR support

* Automatic package database sync

* HTML5 application written in Go

* Test Driven Development

* Secure websockets

* sqlite datastore

* system-d build containers

* Local package repository management

Architecture
============

APC is written in the Go programming language which allows fast and stable
development of compiled applications with a strong focus on networked
applications.

APC uses pacman to perform all package operations.

Installation
------------

At installation, a key and certificate are generated for HTTPS authentication.
The user should be encouraged to review the man page for information concerning
HTTPS. They should be encouraged to get a CA signed certificate to improve
security and suppress browser warnings.

The user should also be notified to activate the apc sync tool in the root
crontab.

APC Sync Tool
~~~~~~~~~~~~~

The activation script should be installed to "/etc/apc/apc-sync". This script
invokes apc in sync mode. While in this mode, apc syncs the package database
and checks AUR for package updates. If any package statistics change, the
changes are saved to the datastore. The default time for activation is 15
minutes. A notification (through notify-send) will be sent when new updates are
found.

Activation
----------

The user activates APC by using the apc.desktop link or from the command line.
If used from the command line, the application will update the user with
process output. Once the apc command is issued, the user is asked for the root
password using sudo (gksudo). When the correct root password is given to the
sudo command, APC will start a server listening on http://localhost:1111/apc.
If the sudo command fails, APC exits immediately.

User Interface
--------------

Once the server has started, the APC application is shown to the user in the
default web browser. If the browser tab is closed, the apc process is closed.
If the browser tab becomes inactive for a period of time, the APC process is
closed.

TODO: COMPLETE THIS SECTION, NOT SURE YET OF THE VIEW.

The default view of the application is a split view with a topbar, a list of
packages on the left side, and a... list of installed packages. If any of the
packages in the list are out-of-date, the list item is highlighted. The list is
divided between official packages, AUR packages, and local packages.

The package statistics of the host system, such as available package updates
(with notable packages emphasized) as well as package updates from AUR. The
list of the notable packages can be configured.

The primary view of the HTML5 application is the list of installed applications
with host system package statistics. The list should highlight which packages
have available updates. A topbar will be used to show the application banner,
as well as package statistics and toolbar-like button buttons and menus.

TODO: END COMPLETE THIS SECTION, NOT SURE YET OF THE VIEW.

AUR
---

If a desired package is located in AUR, then the package will be built in a
systemd container. The output process is shown in the UI, like Travis Ci. APC
allows for editing of PKGBUILDS in the browser.

Repo Management
---------------

Built packages can be added to a repository. The user can configure if they
want it to be signed or not.

--------
FEATURES
--------

Detailed below are the features that APC implements. They are ordered by
importance.

Security
========

Authentication
--------------

* APC will not store passwords of any kind.

* APC is ran as root, but not as a service.

* The sync tool should be run as a root service (systemd).

* APC requires the root password for login.

Datastore
---------

* The sql data store is stored in "/var/cache/pacman" with 755 permissions.

* The APC configuration file is stored at "/etc/apc/conf"

HTTPS
-----

* The server must use HTTPS for security (local network focus)

* By default, APC only accepts connections from the local network.

* The key and certificate should be self signed and kept in "/etc/apc/certs"

* Secure Websockets (wss)

  * http://blog.kaazing.com/2012/02/28/html5-websocket-security-is-strong/

  * https://devcenter.heroku.com/articles/websocket-security

  * http://lucumr.pocoo.org/2012/9/24/websockets-101/

* The Go Websocket library from the Go Authors

  * http://godoc.org/code.google.com/p/go.net/websocket

Sqlite Datastore
================

* The sqlite database will be saved to "~/var/cache/apc".

* Clear text file.

* The database will contain all package sources downloaded from AUR, as well as
  previous versions.

User Interface
==============

APC uses the AngularJS framework for displaying the user interface on the
client side. The client uses the RestAPI of the APC server. The CSS framework
is provided by Angular-Bootstrap.

* http://angularjs.org/
* http://www.thinkster.io/
* https://www.ng-book.com/
* http://angular-ui.github.io/bootstrap/

Authentication
--------------

When the user activates the APC application using the commandline or desktop
link, APC asks for root permissions using gksudo. When the browser containing
the APC application is closed, the APC process is terminated.

The apc-sync tool should be run as a root cron job.

Process Output Display
----------------------

Whenever APC uses shell commands, the output should be displayed in the
browser. This feature is similar to the output displayed by Travis Ci.

Search
------

A search bar is displayed on the UI at all times (above the package list).

Package Statistics
------------------

Package status is shown on the UI at all times (in the topbar).

Editing
=======

For local PKGBUILDS, or packages retrieved from AUR, the application should
allow for quick edits using a built in editor. The default editor of the host
can also be used if the user wishes.

* The editor specified in the $EDITOR environment variable is used to edit AUR
  packages.

* APC can be configured to use a built in colorized text editor.

* An external editor can be used for diff merging (vimdiff)

Syntax Coloring
---------------

* A syntax coloring library is used for displaying UI such as package diffs or
  colorized console output.

* The diff (https://github.com/sergi/go-diff) should be shown colorized so that
  changes are easy to see for the user. https://neil.fraser.name/writing/diff/

* For implementing this in Go, a pygments type library must be found or
  created.

Package Management
==================

Installing or Updating
----------------------

Packages that are to be installed or updated are deferred to pacman.

AUR
---

Integration with AUR is a highlight feature of APC, and mostly the reason for
its existence.

* Integrated into the search feature.

* Automatic updates (configurable, not default)

* Download packages from AUR and store in database.

* Build packages in container.

Local Repositories
------------------

TODO

Systemd Container Management
============================

TODO

--------------
Implementation
--------------

Phase Overview
==============

Phase 1
=======

Phase 2
=======

Phase 3
=======
