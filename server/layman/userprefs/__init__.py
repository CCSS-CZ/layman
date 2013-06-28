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

        # create tempdir
        self.tempdir = self.config.get("FileMan","tempdir")
        if not os.path.exists(self.tempdir):
            os.mkdir(self.tempdir)

    #
    # POST methods
    #

    def add(self,username,roles):
            
        logging.debug("UserPrefs.add() added user: %s"% username)

        return ("created","User:'%s'" % created)

    def update(self,username,roles):
            
        logging.debug("UserPrefs.add() added user: %s"% username)

        return ("created","User:'%s'" % created)

    def remove(self,username,roles):
            
        logging.debug("UserPrefs.add() added user: %s"% username)

        return ("created","User:'%s'" % created)

