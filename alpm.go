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
	// "github.com/demizer/go-elog"
	"fmt"
	"os"
)

const PACMAN_CONF_PATH = "/etc/pacman.conf"

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

// Alpm is the wrapper to libalpm. Create a new instance of Alpm with
// NewAlpm(). The Alpm data type contains the handle to resource created by
// libalpm. The handle must be released manually when no longer needed by
// calling Alpm.Release().
type Alpm struct {
	handle      *alpm.Handle
	pacmanConf  *alpm.PacmanConfig
	officialDbs map[OfficialDb]alpm.Db
	localDb     *alpm.Db
}


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

// Returns a new Alpm data type.
func NewAlpm() (*Alpm, error) {
	pacmanConf, err := ParseConfig()
	if err != nil {
		return nil, err
	}

	handle, err := pacmanConf.CreateHandle()

	a := &Alpm{handle: handle, pacmanConf: pacmanConf}

	if err != nil {
		return nil, err
	}

	if err := a.InitDatabases(); err != nil {
		return nil, err
	}

	return a, nil
}

// Free the handle to the libalpm resource when it is no longer needed.
func (a *Alpm) Release() error {
	err := a.handle.Release()
	if err != nil {
		return err
	}
	return nil
}

// Initializes the official libalpm package databases.
func (a *Alpm) InitDatabases() error {
	dbs, err := a.handle.SyncDbs()
	if err != nil {
		return err
	}

	a.officialDbs = make(map[OfficialDb]alpm.Db)

	for _, db := range dbs.Slice() {
		if odb := OfficialDbFromString(db.Name()); odb > UnofficialDb {
			a.officialDbs[odb] = db
		}
	}

	if a.localDb, err = a.handle.LocalDb(); err != nil {
		return err
	}

	return nil
}

// Returns true if the package is from an officially supported repo such as
// core, extra, or community.
func (a *Alpm) IsOfficialPackage(pkg alpm.Package) bool {
	name := pkg.Name()
	for _, db := range a.officialDbs {
		if _, err := db.PkgByName(name); err == nil {
			return true
		}
	}
	return false
}

// Returns true if the package is not in the official package databases.
func (a *Alpm) IsExternalPackage(pkg alpm.Package) bool {
	return !a.IsOfficialPackage(pkg)
}

// Returns a list of packages that are not found in the official Arch Linux
// package databases.
func (a *Alpm) ExternalPackageList() []alpm.Package {
	var pkgs []alpm.Package
	for _, pkg := range a.localDb.PkgCache().Slice() {
		if a.IsExternalPackage(pkg) {
			pkgs = append(pkgs, pkg)
		}
	}
	return pkgs
}

func (a *Alpm) InstalledPackages() []alpm.Package {
	return a.localDb.PkgCache().Slice()
}

func (a *Alpm) SearchSyncDbsByName(name string) (*alpm.Package, error) {
	var pkg *alpm.Package
	var err error
	for _, db := range a.officialDbs {
		pkg, err =  db.PkgByName(name)
		if err != nil {
			continue
		} else {
			break
		}
	}
	if err != nil {
		return nil, fmt.Errorf("The package \"%s\" was not found in " +
			"the sync databases.", name)
	}
	return pkg, nil
}

// type StalePackage struct {
	// localPackage *alpm.Package
	// syncPackage *alpm.Package
// }

// func (a *Alpm) StalePackages() ([]StalePackage, error) {
	// var sPkgs []StalePackage
	// for _, pkg := range a.InstalledPackages() {
		// sPkg, err := a.SearchSyncDbsByName(pkg.Name())
		// if err != nil {
			// return nil, err
		// }
		// sPkgs = append(sPkgs, StalePackage{localPackage: &pkg,
			// syncPackage: sPkg})
		// // DO VERSION COMPARE HERE
	// }
	// return sPkgs, nil
// }
