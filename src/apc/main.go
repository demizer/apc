/*
 * main.go - Application entry point
 *
 * Copyright (c) 2013 - The APC Authors
 *
 * MIT Licensed. See LICENSE for details.
 */

package main

import (
	"alpm"
	"logger"
	"os"
)

var log = logger.New(logger.CRITICAL, os.Stdout)

// ParseConfig parses the pacman config if it exists and returns a PacmanConfig
// object.
func ParseConfig() (*alpm.PacmanConfig, error) {
	fconf, err := os.Open(PACMAN_CONF_PATH)
	if err != nil {
		return nil, err
	}
	conf, err := alpm.ParseConfig(fconf)
	if err != nil {
		return nil, err
	}
	return &conf, nil
}

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

var (
	pacmanConf  *alpm.PacmanConfig
	handle      *alpm.Handle
	officialDbs = make(map[OfficialDb]alpm.Db)
	localDb     *alpm.Db
)

// Determines if the package is from an officially supported repo such as core,
// extra, or community.
func IsOfficialPackage(pkg alpm.Package) bool {
	name := pkg.Name()
	for _, db := range officialDbs {
		if _, err := db.PkgByName(name); err == nil {
			// TODO: Fix logger to allow setting log level on
			// default logger!!
			// log.Debugln("IsOfficialPackage():", name, "is from",
				// db.Name())
			return true
		}
	}
	// log.Debugln("IsOfficialPackage():", name, "is NOT an official package")
	return false
}

func InitPacmanDbs() error {
	dbs, err := handle.SyncDbs()
	if err != nil {
		return err
	}
	for _, db := range dbs.Slice() {
		if odb := OfficialDbFromString(db.Name()); odb > UnofficialDb {
			log.Debugln("Detected official db:", odb)
			officialDbs[odb] = db
		}
	}
	if localDb, err = handle.LocalDb(); err != nil {
		return err
	}
	return nil
}

func Init() {
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
	if err := InitPacmanDbs(); err != nil {
		log.Criticalln(err)
		os.Exit(1)
	}
}

func main() {
	// Read the config and get the handle
	Init()

	for _, pkg := range localDb.PkgCache().Slice() {
		if !IsOfficialPackage(pkg) {
			log.Println(pkg.Name())
		}
	}

	if handle.Release() != nil {
		log.Criticalln("Could not release libalpm!")
		os.Exit(1)
	}
}
