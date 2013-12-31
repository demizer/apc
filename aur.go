/*
 * aur.go - Application entry point
 *
 * Copyright (c) 2013 - The APC Authors
 *
 * MIT Licensed. See LICENSE for details.
 */

package main

import (
	"github.com/demizer/go-alpm"
	"github.com/demizer/go-elog"
	"github.com/demizer/apc/aur"
)

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
	cName := log.AnsiEscape(log.ANSI_BOLD, log.ANSI_WHITE,
		job.pkg.Name(), log.ANSI_OFF)
	if err != nil {
		mLabel := log.AnsiEscape(log.ANSI_BOLD,
			log.ANSI_RED, "[MISSING]", log.ANSI_OFF)
		log.Println(mLabel, cName)
		done <- true
		return
	}
	if alpm.VerCmp(job.pkg.Version(), pInfo.Version) != 0 {
		job.result = AUR_NEW_VERSION
		nVerLabel := log.AnsiEscape(log.ANSI_BOLD,
			log.ANSI_CYAN, "[NEW VERSION]", log.ANSI_OFF)
		arrow := log.AnsiEscape(log.ANSI_BOLD, log.ANSI_RED, "=>",
			log.ANSI_OFF)
		log.Println(nVerLabel, cName, "("+job.pkg.Version(), arrow,
			pInfo.Version+")")
		done <- true
		return
	}

	curLabel := log.AnsiEscape(log.ANSI_BOLD, log.ANSI_GREEN,
		"[CURRENT]", log.ANSI_OFF)
	log.Println(curLabel, cName, "=", job.pkg.Version())
	done <- true
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

