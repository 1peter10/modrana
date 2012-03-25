#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana QML GUI module
# * it inherits everything in the base GUI module
# * overrides default functions and handling
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------

import sys
import re
import os
import traceback
import cStringIO

# PySide
from PySide import QtCore
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtDeclarative import *

# modRana imports
from base_gui_module import GUIModule
from datetime import datetime

def newlines2brs(text):
  """ QML uses <br> instead of \n for linebreak """
  return re.sub('\n', '<br>', text)


class Logger:
  def __init__(self, log=True):
    pass
    self.log=log

  def debug(self, message):
    if self.log:
      print message

logger = Logger(log=False)

def getModule(m,d,i):
    return(QMLGUI(m,d,i))

class QMLGUI(GUIModule):
  """A Qt + QML GUI module"""

  def __init__(self, m, d, i):
    GUIModule.__init__(self, m, d, i)

    # some constants
    self.msLongPress = 400
    self.centeringDisableThreshold = 2048
    size = (800,480) # initial window size

    # window state
    self.fullscreen = False

    # Create Qt application and the QDeclarative view
    class ModifiedQDeclarativeView(QDeclarativeView):
      def __init__(self, modrana):
        QDeclarativeView.__init__(self)
        self.modrana = modrana

      def closeEvent(self, event):
        print "shutting down"
        self.modrana.shutdown()

    self.app = QApplication(sys.argv)
    self.view = ModifiedQDeclarativeView(self.modrana)
    self.window = QMainWindow()
    self.window.resize(*size)
    self.window.setCentralWidget(self.view)
    self.view.setResizeMode(QDeclarativeView.SizeRootObjectToView)
#    self.view.setResizeMode(QDeclarativeView.SizeViewToRootObject)

    # add image providers
    self.iconProvider = IconImageProvider()
    self.view.engine().addImageProvider("icons",self.iconProvider)
    # add tiles provider
    self.tilesProvider = TileImageProvider(self)
    self.view.engine().addImageProvider("tiles",self.tilesProvider)

    rc = self.view.rootContext()
    # make options accessible from QML
    options = Options(self.modrana)
    rc.setContextProperty("options", options)
    # make GPS accessible from QML
    gps = GPSDataWrapper(self.modrana, self)
    rc.setContextProperty("gps", gps)
    # make the platform accessible from QML
    platform = Platform(self.modrana)
    rc.setContextProperty("platform", platform)

    self.window.closeEvent = self._qtWindowClosed
    #self.window.show()

    self.rootObject = None

    self._location = None # location module
    self._mapTiles = None # map tiles module

    self._notificationQueue = []

  def firstTime(self):
    self._location = self.m.get('location', None)
    self._mapTiles = self.m.get('mapTiles', None)

  def getIDString(self):
    return "QML"

  def isFullscreen(self):
    return self.window.isFullScreen()

  def toggleFullscreen(self):
    if self.window.isFullScreen():
      self.window.showNormal()
    else:
      self.window.showFullScreen()

  def setFullscreen(self, value):
    if value == True:
      self.window.showFullScreen()
    else:
      self.window.showNormal()

  def setCDDragThreshold(self, threshold):
    """set the threshold which needs to be reached to disable centering while dragging
    basically, larger threshold = longer drag is needed to disable centering
    default value = 2048
    """
    self.centeringDisableThreshold = threshold

  def startMainLoop(self):
    """start the main loop or its equivalent"""

#    print "QML start main loop"

    if self.modrana.dmod.startInFullscreen():
      self.toggleFullscreen()

    # Create an URL to the QML file
    url = QUrl('modules/gui_modules/gui_qml/qml/main.qml')
    # Set the QML file and show
    self.view.setSource(url)
    # get the root object
    self.rootObject = self.view.rootObject()

    # start main loop
    self.window.show()

    # handle any notifications that might have come before firstTime
    # (the GUI is not available before firstTime)
    if self._notificationQueue:
      for item in self._notificationQueue:
        self.notify(*item)

    self.app.exec_()
#    print "QML main loop started"

  def _qtWindowClosed(self, event):
    print('Qt window closing down')
    self.modrana.shutdown()

  def stopMainLoop(self):
    """stop the main loop or its equivalent"""
    # notify QML GUI first
    """NOTE: due to calling Python properties
    from onDestruction handlers causing
    segfault, we need this"""
    #self.rootObject.shutdown()

    # quit the application
    self.app.exit()
    self.modrana.shutdown()

  def hasNotificationSupport(self):
    return True

  def notify(self, text, msTimeout=5000, icon=""):
    """trigger a notification using the Qt Quick Components
    InfoBanner notification"""

    # QML uses <br> instead of \n for linebreak
    text = newlines2brs(text)
    print("QML GUI notify:\n message: %s, timeout: %d" % (text, msTimeout))
    if self.rootObject:
      self.rootObject.notify(text,msTimeout)
    else:
      self._notificationQueue.append((text, msTimeout, icon))

class Platform(QtCore.QObject):
  """make stats available to QML and integrable as a property"""
  def __init__(self, modrana):
    QtCore.QObject.__init__(self)
    self.modrana = modrana

  @QtCore.Slot(result=bool)
  def isFullscreen(self):
    return self.modrana.gui.isFullscreen()

  @QtCore.Slot()
  def toggleFullscreen(self):
    self.modrana.gui.toggleFullscreen()

  @QtCore.Slot(bool)
  def setFullscreen(self, value):
    self.modrana.gui.setFullscreen(value)

  #  @QtCore.Slot()
  #  def minimise(self):
  #    return self.mieru.platform.minimise()

  #  @QtCore.Slot(result=bool)
  #  def showMinimiseButton(self):
  #    """
  #    Harmattan handles this by the Swype UI and
  #    on PC this should be handled by window decorator
  #    """
  #    return self.mieru.platform.showMinimiseButton()

  @QtCore.Slot(result=bool)
  def showQuitButton(self):
    """
    Harmattan handles this by the Swype UI and
    on PC it is a custom to have the quit action in the main menu
    """
    return self.modrana.dmod.needsQuitButton()

  @QtCore.Slot(result=bool)
  def incompleteTheme(self):
    """
    The "base" theme is incomplete at the moment (March 2012),
    use fail-safe or local icons.
    Hopefully, this can be removed once the themes are in better shape.
    """
    # the Fremantle theme is incomplete
    return self.modrana.dmod.getDeviceIDString() == "n900"


class IconImageProvider(QDeclarativeImageProvider):
  """the IconImageProvider class provides icon images to the QML layer as
  QML does not seem to handle .. in the url very well"""
  def __init__(self):
    QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)

  def requestImage(self, iconPath, size, requestedSize):
    try:
      #TODO: theme name caching ?
      f = open('themes/%s' % (iconPath),'r')
      img=QImage()
      img.loadFromData(f.read())
      f.close()
      return img
      #return img.scaled(requestedSize)
    except Exception, e:
      print("QML GUI: icon image provider: loading icon failed", e)
      print iconPath
      print 'themes/%s' % (iconPath)

class TileImageProvider(QDeclarativeImageProvider):
  """
  the TileImageProvider class provides images images to the QML map element
  """
  def __init__(self, gui):
    QDeclarativeImageProvider.__init__(self, QDeclarativeImageProvider.ImageType.Image)
    self.gui = gui

  def requestImage(self, tileInfo, size, requestedSize):
    """
    the tile info should look like this:
    layerID/zl/x/y
    """
    try:
      # split tileInfo
      (layer,z,x,y) = tileInfo.split("/")
      print "LAYER"
      print layer
      z = int(z)
      x = int(x)
      y = int(y)
      tileData = self.gui._mapTiles.getTile(layer, z, x, y)
      # create a file-like object
      f = cStringIO.StringIO(tileData)
      # create image object
      img=QImage()
      # lod the image from in memory buffer
      img.loadFromData(f.read())
      # cleanup
      f.close()

      return img
      #return img.scaled(requestedSize)
    except Exception, e:
      print("QML GUI: icon image provider: loading tile failed", e)
      print tileInfo
      traceback.print_exc(file=sys.stdout)



# from AGTL
class Fix():
  BEARING_HOLD_EPD = 90 # arbitrary, yet non-random value
  last_bearing = 0
  # tracking the minimum difference between a received fix time and
  # our current internal time.
  min_timediff = datetime.utcnow() - datetime.utcfromtimestamp(0)

  def __init__(self,
               position = None,
               altitude = None,
               bearing = None,
               speed = None,
               sats = 0,
               sats_known = 0,
               dgps = False,
               quality = 0,
               error = 0,
               error_bearing = 0,
               timestamp = None):
    self.position = position
    self.altitude = altitude
    self.bearing = bearing
    self.speed = speed
    self.sats = sats
    self.sats_known = sats_known
    self.dgps = dgps
    self.quality = quality
    self.error = error
    self.error_bearing = error_bearing
    if timestamp == None:
      self.timestamp = datetime.utcnow()
    else:
      self.timestamp = timestamp

class FixWrapper(QtCore.QObject):

  def __init__(self, fix):
    QtCore.QObject.__init__(self)
    self.data = fix

  changed = QtCore.Signal()

  def update(self, fix):
    self.data = fix
    logger.debug("Fix updated with data from %r" % fix)
    self.changed.emit()

  def _lat(self):
    if self.data.position != None:
      return self.data.position[0]
    else:
      return -1

  def _lon(self):
    if self.data.position != None:
      return self.data.position[1]
    else:
      return -1

  def _altitude(self):
    return self.data.altitude if self.data.altitude != None else 0

  def _speed(self):
    return self.data.speed if self.data.speed != None else 0

  def _bearing(self):
    return self.data.bearing if self.data.bearing != None else 0

  def _error(self):
    return float(self.data.error)

  def _valid(self):
    return (self.data.position != None)

  def _altitude_valid(self):
    return self.data.altitude != None

  def _speed_valid(self):
    return self.data.speed != None

  lat = QtCore.Property(float, _lat, notify=changed)
  lon = QtCore.Property(float, _lon, notify=changed)
  altitude = QtCore.Property(float, _altitude, notify=changed)
  speed = QtCore.Property(float, _speed, notify=changed)
  bearing = QtCore.Property(float, _bearing, notify=changed)
  error = QtCore.Property(float, _error, notify=changed)
  valid = QtCore.Property(bool, _valid, notify=changed)
  speedValid = QtCore.Property(bool, _speed_valid, notify=changed)
  altitudeValid = QtCore.Property(bool, _altitude_valid, notify=changed)



class GPSDataWrapper(QtCore.QObject):

  changed = QtCore.Signal()
  changed_target = QtCore.Signal()
  changed_distance_bearing = QtCore.Signal()

  def __init__(self, modrana, gui):
    QtCore.QObject.__init__(self)
    self.modrana = modrana
    self.gui = gui
#    self.modrana.connect('good-fix', self._on_good_fix)
#    self.modrana.connect('no-fix', self._on_no_fix)
#    self.modrana.connect('target-changed', self._on_target_changed)
    self.modrana.watch('locationUpdated',self._posChangedCB)

    pos = self.modrana.get('pos', None)
    speed = self.modrana.get('speed', 0)
    bearing = self.modrana.get('bearing', 0)
    elevation = self.modrana.get('elevation', 0)
    fix = Fix(pos, elevation, bearing, speed)
    self.gps_data = FixWrapper(fix)
    self.gps_last_good_fix = FixWrapper(fix)
    self.gps_has_fix = False
    self.gps_status = ''
    #self.astral = Astral()

  @QtCore.Slot(bool, float, float, bool, float, bool, float, float, QtCore.QObject)
  def positionChanged(self, valid, lat, lon, altvalid, alt, speedvalid, speed, error, timestamp):
    if valid:
      pos = (lat,lon)
      self._on_good_fix(Fix(pos, alt, bearing, speed))

  def _posChangedCB(self, key, oldValue, newValue):
    """position changed callback"""

    # check validity
    pos = self.modrana.get('pos', None)
    if pos:
      if self.gui._location:
        self._on_good_fix(self.gui._location.getFix())
    else:
      self._on_no_fix()

  def _on_good_fix(self, fix):
    logger.debug("Received good fix")
    self.gps_data.update(fix)
    self.gps_last_good_fix.update(fix)
    self.gps_has_fix = True
    self.changed_distance_bearing.emit()
    self.changed.emit()

  def _on_no_fix(self):
    self.gps_data.update(gps_data)
    self.gps_has_fix = False
    self.gps_status = "unknown"
    self.changed_distance_bearing.emit()
    self.changed.emit()

  def _on_target_changed(self, target, distance, bearing):
    self._target_valid = (target != None)
    self._target = CoordinateWrapper(target) if target != None else CoordinateWrapper(geo.Coordinate(0, 0))
    self.gps_target_distance = distance
    self.gps_target_bearing = bearing
    self.changed_distance_bearing.emit()
    self.changed_target.emit()
    logger.debug("Target is now set to %r" % target)

  #    def _sun_angle_valid(self):
  #        return self.astral.get_sun_azimuth_from_fix(self.gps_last_good_fix) != None
  #

  def _target(self):
    return self._target

  def _target_valid(self):
    return self._target_valid

  def _gps_data(self):
    return self.gps_data

  def _gps_last_good_fix(self):
    return self.gps_last_good_fix

  def _gps_has_fix(self):
    return self.gps_has_fix

  def _gps_target_distance_valid(self):
    return self.gps_target_distance != None

  def _gps_target_distance(self):
    logger.debug("Target distance is %r" % self.gps_target_distance)
    return float(self.gps_target_distance) if self._gps_target_distance_valid()  else 0

  def _gps_target_bearing(self):
    try:
      return float(self.gps_target_bearing)
    except TypeError:
      return 0

  def _gps_status(self):
    return self.gps_status


  data = QtCore.Property(QtCore.QObject, _gps_data, notify=changed)
  lastGoodFix = QtCore.Property(QtCore.QObject, _gps_last_good_fix, notify=changed)
  hasFix = QtCore.Property(bool, _gps_has_fix, notify=changed)
#  targetValid = QtCore.Property(bool, _target_valid, notify=changed_target)
#  target = QtCore.Property(QtCore.QObject, _target, notify=changed_target)
#  targetDistanceValid = QtCore.Property(bool, _gps_target_distance_valid, notify=changed_distance_bearing)
#  targetDistance = QtCore.Property(float, _gps_target_distance, notify=changed_distance_bearing)
#  targetBearing = QtCore.Property(float, _gps_target_bearing, notify=changed_distance_bearing)
  status = QtCore.Property(str, _gps_status, notify=changed)

class Options(QtCore.QObject):
    """make options available to QML and integrable as a property"""
    def __init__(self, modrana):
        QtCore.QObject.__init__(self)
        self.modrana = modrana

    """ like this, the function can accept
    and return different types to and from QML
    (basically anything that matches some of the decorators)
    as per PySide developers, there should be no perfromance
    penalty for doing this and the order of the decorators
    doesn't mater"""
    @QtCore.Slot(str, bool, result=bool)
    @QtCore.Slot(str, int, result=int)
    @QtCore.Slot(str, str, result=str)
    @QtCore.Slot(str, float, result=float)
    def get(self, key, default):
      """get a value from Mierus persistant options dictionary"""
      print "GET"
      print key, default, self.modrana.get(key, default)
      return self.modrana.get(key, default)

    @QtCore.Slot(str, bool)
    @QtCore.Slot(str, int)
    @QtCore.Slot(str, str)
    @QtCore.Slot(str, float)
    def set(self, key, value):
      """set a keys value in Mierus persistant options dictionary"""
      print "SET"
      print key, value
      return self.modrana.set(key, value)