/*
 * package.go - Application entry point
 *
 * Copyright (c) 2013 - The APC Authors
 *
 * MIT Licensed. See LICENSE for details.
 */

package main

import (
	"github.com/demizer/go-alpm"
	"github.com/demizer/go-elog"
	"os"
)

// An officially supported repository that would be found in pacman.conf.
type OfficialDb int

const (
	UnofficialDb OfficialDb = 1 + iota
	Core
	Extra
	Community
	Testing
	Multilib
	MultilibTesting
	Local
)

var dbs = [...]string{
	"UnofficialDb",
	"Core",
	"Extra",
	"Community",
	"Testing",
	"Multilib",
	"MultilibTesting",
	"Local",
}

// Returns the english name of the official package database.
func (db OfficialDb) String() string { return dbs[db-1] }

// Returns the integer equivalent of name as a OfficialDb type. Nil is
// returned if name is not an officially supported repository.
func OfficialDbFromString(name string) OfficialDb {
	if name == "core" {
		return Core
	} else if name == "extra" {
		return Extra
	} else if name == "community" {
		return Community
	} else if name == "testing" {
		return Testing
	} else if name == "multilib" {
		return Multilib
	} else if name == "multilib-testing" {
		return MultilibTesting
	}
	return UnofficialDb
}

// Determines if the package is from an officially supported repo such as core,
// extra, or community.
func IsOfficialPackage(pkg alpm.Package) bool {
	name := pkg.Name()
	for _, db := range officialDbs {
		if _, err := db.PkgByName(name); err == nil {
			// TODO: Fix log to allow setting log level on
			// default log!!
			// log.Debugln("IsOfficialPackage():", name, "is from",
			// db.Name())
			return true
		}
	}
	// log.Debugln("IsOfficialPackage():", name, "is NOT an official package")
	return false
}

func InitAlpm() {
	pacmanConf, err := ParseConfig()
	if err != nil {
		log.Criticalln(err)
		os.Exit(1)
	}
	handle, err = pacmanConf.CreateHandle()
	if err != nil {
		log.Criticalln(err)
		os.Exit(1)
	}
	if err := InitPacmanDatabases(); err != nil {
		log.Criticalln(err)
		os.Exit(1)
	}
}

func InitPacmanDatabases() error {
	dbs, err := handle.SyncDbs()
	if err != nil {
		return err
	}
	for _, db := range dbs.Slice() {
		if odb := OfficialDbFromString(db.Name()); odb > UnofficialDb {
			// log.Debugln("Detected official db:", odb)
			officialDbs[odb] = db
		}
	}
	if localDb, err = handle.LocalDb(); err != nil {
		return err
	}
	return nil
}

func ExternalPackageList() []alpm.Package {
	pkgs := make([]alpm.Package, 0)
	for _, pkg := range localDb.PkgCache().Slice() {
		if !IsOfficialPackage(pkg) {
			pkgs = append(pkgs, pkg)
		}
	}
	return pkgs
}

