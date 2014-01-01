====================================
Arch Package Companion Specification
====================================
:Modified: Wed Jan 01 03:00 2014

Arch Package Companion is a HTML5 application for managing packages in Arch
Linux. APC incorporates the Arch User Repository and builds the packages in a
systemd container. APC shows the user up-to-date information about the package
state of the host system in a clean HTML5 interface.

--------
Overview
--------

-----
INBOX
-----

------------
Requirements
------------

Overview
========

* Not a pacman replacement

* Written in Go

* HTTPS for local network

* AUR support

* sqlite datastore

* system-d containers

* Test Driven Development

Architecture
============

APC is written in the Go programming language which allows fast and stable
development of compiled applications with a strong focus on networked
applications.

APC is designed to be used with pacman, not as a replacement.

The web client connects to an APC server on the local machine. From this web
based client the user can manage package installation including packages from
the Arch User Repository.

Once the server is running, the user can login into APC from the local network
over HTTPS to administer packages. The application is shown to the user in a
web browser and the user can update the package database by clicking a refresh
button. APC can be set to automatically update the package database at set time
intervals.

Once in the application, the user is shown system package data, such as
available updates (with notable packages emphasized). The updates shown include
packages from AUR. The list of the notable packages can be configured.

The primary view of the HTML5 application is the list of installed applications
with host system package statistics. The list should highlight which packages
have available updates. A topbar will be used to show the application banner,
as well as package statistics and toolbar-like button buttons and menus. 

If the desired package is located in AUR, then the package will be built in a
systemd container. The output process is shown in the UI, like Travis Ci. APC
allows for editing of PKGBUILDS in the browser.

--------
FEATURES
--------

sqlite Datastore
================

* Clear text file?

* The sqlite database will be saved to "~/.config/apc".

* The database will contain all package sources downloaded from AUR, as well as
  previous versions.

* Settings are stored in the database and configurable in the web app.

HTTPS
=====

* The server must use HTTPS for security (local network focus)
  
Package Management
==================

* Package status is shown on the UI at all times.

Search
------

* A search bar is displayed on the UI at all times.

Editing
-------

* The editor specified in the $EDITOR environment variable is used to edit AUR
  packages.

* APC can be configured to use a built in colorized text editor.

Installing or Updating
----------------------

* Packages that are to be installed or updated are deferred to pacman.

AUR
---

* Integrated into package search

* Automatic updates (configurable, not default)

* Download packages from AUR and store in database.

* Build packages in container.

Process Output Display
======================

* Travis CI like worker output display.

Syntax Coloring
===============

* A syntax coloring library is used for displaying UI such as package diffs or
  colorized console output.

* The diff (https://github.com/sergi/go-diff) should be shown colorized so that
  changes are easy to see for the user. https://neil.fraser.name/writing/diff/
  
* For implementing this in Go, a pygments type library must be found or
  created.
