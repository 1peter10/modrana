#!/usr/bin/python
#----------------------------------------------------------------------------
# A modRana module providing various kinds of information.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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
from base_module import ranaModule
import os

def getModule(m,d,i):
  return(info(m,d,i))

class info(ranaModule):
  """A modRana information handling module"""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.versionString = "unknown version"
    self.versionFilePath = 'version.txt'
    # try read the version file
    if os.path.exists(self.versionFilePath):
      try:
        f = open(self.versionFilePath, 'r')
        versionString = f.read()
        f.close()
        # is it really string ?
        versionString = str(versionString)
        self.versionString = versionString
      except Exception, e:
        print "loading version info failed"
        print e


  def drawMenu(self, cr, menuName):
    if menuName == 'infoAbout':
      print "dadasdasd"
      menus = self.m.get('menu', None)
      if menus:
        nop = "set:menu:infoAbout"
        button1 = ('', 'generic', nop)
        button2 = ('', 'generic', nop)
        web = "www.modrana.org"
        email = "modrana@gmail.com"
        text = "modRana version:\n\n%s\n\n\n\nFor questions or feedback,\n\ncontact the <b>modRana</b> project:\n\n%s\n\n%s\n\n" % (self.versionString,web,email)
        box = (text ,nop)
        menus.drawThreePlusOneMenu(cr, 'infoAbout', 'set:menu:info', button1, button2, box)

    

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
