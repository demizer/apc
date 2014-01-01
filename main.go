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
	"github.com/codegangsta/martini"
	"github.com/codegangsta/martini-contrib/render"
	"os"
)

type Page struct {
	Title string
	Header string
	PackageList []string
	InstalledPackages int
	OutOfDatePackages int
}

func main() {
	log.SetLevel(log.LEVEL_DEBUG)

	alpm, err := NewAlpm()
	if err != nil {
		log.Critical(err)
		os.Exit(1)
	}

	log.Debugln(len(alpm.InstalledPackages()))

	// sPkgs, err := alpm.StalePackages()
	// if err != nil {
		// log.Critical(err)
		// os.Exit(1)
	// }
	// for _, pkg := range sPkgs {
		// log.Debugln(pkg.Name())
	// }

	p := &Page{Title: "Arch Package Companion", Header: "APC"}
	m := martini.Classic()
	m.Use(render.Renderer())

	m.Get("/", func(r render.Render) {
		log.Debugln(os.Getwd())
		r.HTML(200, "layout", p)
	})

	m.Run()

	err = alpm.Release()
	if err != nil {
		log.Critical(err)
		os.Exit(1)
	}
}
