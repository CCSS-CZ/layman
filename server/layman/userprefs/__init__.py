#
#    LayMan - the Layer Manager
#
#    Copyright (C) 2016 Czech Centre for Science and Society
#    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
#    Mailto: sredl@ccss.cz, charvat@ccss.cz
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys
#import glob
import mimetypes, time
import json
import logging
import zipfile
import web

from layman.errors import LaymanError
from layman.layed.gsxml import GsXml

class UserPrefs:
    """User preferences manager of LayMan
    """

    config = None
    tempdir = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

    def createUser(self, userJsonStr):
        """ Create user and assign group membership
        userJsonStr: '{screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}'
        return 409 Conflict if the user already exists
        """            
        logging.debug("[UserPrefs][createUser] %s"% userJsonStr)
        
        userJson = json.loads(userJsonStr)
        user = userJson["screenName"]
        grouplist = []
        for g in userJson["roles"]:
            grouplist.append(g["roleName"])

        gsx = GsXml(self.config)
        (code, message) = gsx.createUserWithGroups(user, grouplist)
        return (code, message)

    def updateUser(self, userJsonStr):
        """ Update user 
        userJson: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
        if the user does not exist yet, create it.
        """                        
        logging.debug("[UserPrefs][updateUser] %s"% userJsonStr)

        userJson = json.loads(userJsonStr)
        user = userJson["screenName"]
        grouplist = []
        for g in userJson["roles"]:
            grouplist.append(g["roleName"])

        gsx = GsXml(self.config)
        (code, message) = gsx.updateUserWithGroups(user, grouplist)
        return (code, message)

    def deleteUser(self, userName):
        """ Delete user
        """    
        logging.debug("[UserPrefs][deleteUser] %s"% userName)

        gsx = GsXml(self.config)
        (code, message) = gsx.deleteUser(userName)
        return (code, message)

