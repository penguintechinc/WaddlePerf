//go:build nosystray
// +build nosystray

package ui

import (
	"fmt"
	"github.com/sirupsen/logrus"
)

type TrayApp struct {
	serverAddr string
	logger     *logrus.Logger
}

func NewTrayApp(serverAddr string, logger *logrus.Logger) *TrayApp {
	return &TrayApp{
		serverAddr: serverAddr,
		logger:     logger,
	}
}

func (app *TrayApp) Run() error {
	return fmt.Errorf("system tray not supported in this build - compile without 'nosystray' tag to enable")
}