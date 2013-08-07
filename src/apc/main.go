package main

import (
	"os"
	"time"
	"logger"
)

type Package struct {
	Name string
	LastRetrieve time.Time
	Installed bool
	Info *os.FileInfo
	Repo string
	Path string
}

func main() {
	log.Debugln("Hello, world!")
}
