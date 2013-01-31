# Lincense: ...
# authors: Michal, Jachym

import os, sys
#import glob
import mimetypes, time
import json
import logging
import urllib2, base64

class FileMan:
    """File manager of LayMan
    """

    config = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    def putStyle(self, style):
        """Put style into geoserver
        """

        request = urllib2.Request(self.config.get("Geoserver","restapi"))
        userpass=base64.encodestring('%s:%s' %\
                (self.getconfig.get("Geoserver","user"), 
                 self.getconfig.get("Geoserver","password")).replace('\n', '')
        )

        request.add_header("Authorization","Basic %s" % userpass)

        # POST
        result = urllib2.urlopen(request)






