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

    def createUser(self, userJson):
        """ Create user and assign group membership
        userJson: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
        return 409 Conflict if the user already exists
        """            
        logging.debug("[UserPrefs][createUser] %s"% userJson)
        # TODO
        return (201,"User created")

    def updateUser(self, userJson):
        """ Update user 
        userJson: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
        if the user does not exist yet, create it.
        """                        
        logging.debug("[UserPrefs][updateUser] %s"% userJson)
        # TODO
        return (200, "User updated")

    def deleteUser(self, userName):
        """ Delete user
        """    
        logging.debug("[UserPrefs][deleteUser] %s"% userName)
        # TODO
        return (200,"User deleted")

