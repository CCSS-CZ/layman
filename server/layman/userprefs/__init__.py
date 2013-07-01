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

    #
    # POST methods
    #

    def add(self,username,roles):
            
        logging.debug("UserPrefs.add() added user: %s"% username)

        return (200,"User:'%s'" % username)

    def update(self,username,roles):
            
        logging.debug("UserPrefs.add() update user: %s"% username)

        return (200,"User:'%s'" % username)

    def remove(self,username,roles):
            
        logging.debug("UserPrefs.add() removed user: %s"% username)

        return (200,"User:'%s'" % removed)
