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

        request = RequestWithMethod("PUT",self.config.get("Geoserver","restapi")+"/style",style)
        userpass=base64.encodestring('%s:%s' %\
                (self.config.get("Geoserver","user"), 
                 self.config.get("Geoserver","password")).replace('\n', '')
        )

        request.add_header("Authorization","Basic %s" % userpass)
        request.add_header("Content-type","application/vnd.ogc.sld+xml")

        # POST
        result = urllib2.urlopen(request)




class RequestWithMethod(urllib2.Request):
  def __init__(self, method, *args, **kwargs):
    self._method = method
    urllib2.Request.__init__(self,*args, **kwargs)
  def get_method(self):
    return self._method


