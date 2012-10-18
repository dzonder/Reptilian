Reptilian
=========

Helps to manage multiple repositories with simple commands.

I wrote this because I had to deal with multiple repositories on multiple
machines - now I just use ``rept scan`` on one machine where I keep all my
repositories, I share ``config.rept`` and use it on other machines to clone
the same repositories.

GIT, Mercurial, SVN are supported by default.

It's very beta.

Installation
------------

Requirements:

* Python >= 3.0
* VCSes which you actually use

To install (``root`` privileges required)::

   $ make install

Usage
-----

Scan directory for repositories::

   $ rept scan

This will save a configuration file ``config.rept`` with found repositories.
Feel free to modify this file to suit your needs.

Clone all missing repositories::

   $ rept clone

Fetch changes to all repositories::

   $ rept fetch

Update all repositories::

   $ rept update

:author: Michal Olech
:version: 0.1
:license: MIT
