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
	"aur"
	"log"
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
			// log.Debugln("Detected official db:", odb)
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

type AurCheckResult int

const (
	AUR_CHECK AurCheckResult = iota
	AUR_CURRENT
	AUR_OUT_OF_DATE
	AUR_NEW_VERSION
	AUR_MISSING
)

type AurInfo struct {
	result  AurCheckResult
	pkg     alpm.Package
	aurInfo *aur.PkgInfo
}

func AurChecker(job AurInfo, done chan<- bool) {
	// log.Debugln("Receiving:", job.pkg.Name())
	pInfo, err := aur.GetInfo(job.pkg.Name())
	cName := logger.AnsiEscape(logger.BOLD, logger.WHITE,
		job.pkg.Name(), logger.OFF)
	if err != nil {
		mLabel := logger.AnsiEscape(logger.BOLD,
			logger.RED, "[MISSING]", logger.OFF)
		log.Println(mLabel, cName)
		done <- true
		return
	}
	if alpm.VerCmp(job.pkg.Version(), pInfo.Version) != 0 {
		job.result = AUR_NEW_VERSION
		nVerLabel := logger.AnsiEscape(logger.BOLD,
			logger.CYAN, "[NEW VERSION]", logger.OFF)
		arrow := logger.AnsiEscape(logger.BOLD, logger.RED, "=>",
			logger.OFF)
		log.Println(nVerLabel, cName, "("+job.pkg.Version(), arrow,
			pInfo.Version+")")
		done <- true
		return
	}

	curLabel := logger.AnsiEscape(logger.BOLD, logger.GREEN,
		"[CURRENT]", logger.OFF)
	log.Println(curLabel, cName, "=", job.pkg.Version())
	done <- true
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

func AurCheckManager(jobs []alpm.Package, aChan chan<- AurInfo) {
	for _, job := range jobs {
		// log.Debugln("Sending:", job.Name())
		aChan <- AurInfo{AUR_CHECK, job, nil}
	}
	close(aChan)
}

func AurCheckRunner(done chan bool, aChan chan AurInfo) {
	for job := range aChan {
		go AurChecker(job, done)
	}
}

func CheckExternalPackages() {
	packages := ExternalPackageList()

	aChan := make(chan AurInfo)
	done := make(chan bool, len(packages))

	go AurCheckManager(packages, aChan)
	go AurCheckRunner(done, aChan)

	// Wait for all of the goroutines to post results
	for i := 0; i < len(packages); i++ {
		<-done // Blocks waiting for a receive (discards the value)
	}
}

func main() {
	log.Flags = 0

	// Read the config and get the handle
	Init()

	CheckExternalPackages()

	if handle.Release() != nil {
		log.Criticalln("Could not release libalpm!")
		os.Exit(1)
	}
}
