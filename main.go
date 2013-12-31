/*
 * main.go - Application entry point
 *
 * Copyright (c) 2013 - The APC Authors
 *
 * MIT Licensed. See LICENSE for details.
 */

package main

import (
	"github.com/demizer/go-elog"
	"os"
)

func main() {
	alpm, err := NewAlpm()
	if err != nil {
		log.Critical(err)
		os.Exit(1)
	}

	CheckExternalPackages(alpm)

	err = alpm.Release()
	if err != nil {
		log.Critical(err)
		os.Exit(1)
	}
}
