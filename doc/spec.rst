====================================
Arch Package Companion Specification
====================================
:Modified: Sun Jun 02 18:16 2013

Arch Package Companion (APC) is a distributed package manager for Arch Linux
based systems.

-----
INBOX
-----

Sun Jun 02 18:16 2013: Use 2-factor authentication:

    * https://tools.ietf.org/html/rfc6238
    * http://scottlinux.com/2013/06/02/use-google-authenticator-for-two-factor-ssh-authentication-in-linux/

---------
Rationale
---------

Managing a single Arch Linux based system can be tedius at times, managing
three or four systems on a local network can be a pain. APC gives the user a
clean web based GUI to search for and install packages into all configured and
available machines at once.

------------
Requirements
------------

Architecture
============

APC is written in the Go programming language which allows fast and stable
development of compiled applications with a strong focus on networked
applications.

APC uses a client/server architecture. A server is started on each host using
systemd with root permissions. For this reason, it is recommended to only use
APC on internal networks. A strong password is also required to log into APC
from any internal configured host.

The web client connects to an APC server on the local machine. From this web
based client the user can search for and install, or update packages on
multiple systems.

Once the server is running on all desired systems, the user can login APC from
any internal system to administer packages on configured hosts. The server will
sync the pacman database and report out of date packages to the web client. To
ease the load on the update servers, the database sync is only performed once.
The user can then view and select packages to update.

APC can also search for packages to install.
