/*
 * main.go - Application entry point
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

var (
	pacmanConf  *alpm.PacmanConfig
	handle      *alpm.Handle
	officialDbs = make(map[OfficialDb]alpm.Db)
	localDb     *alpm.Db
)

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
	InitAlpm()

	if handle.Release() != nil {
		log.Criticalln("Could not release libalpm!")
		os.Exit(1)
	}
}
