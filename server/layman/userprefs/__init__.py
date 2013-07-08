# Lincense: ...
# authors: Michal, Jachym

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

