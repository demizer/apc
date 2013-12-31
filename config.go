/*
 * config.go - Configuration handling functions
 *
 * Copyright (c) 2013 - The APC Authors
 *
 * MIT Licensed. See LICENSE for details.
 */
package main

import (
	"github.com/demizer/go-alpm"
	"os"
)

const PACMAN_CONF_PATH = "/etc/pacman.conf"

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

