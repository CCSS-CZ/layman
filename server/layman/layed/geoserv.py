# Lincense: ...
# authors: Michal, Jachym

import os, sys
import mimetypes, time
import json
import logging

import httplib2
from urlparse import urlparse

class GsRest:
    """GeoServer REST API
    """

    config = None
    h = None        # Http()
    url = None      # http://erra.ccss.cz/geoserver/rest

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)
        self._setHttp()

    ### LAYERS ###

    def getLayers(self):

        url = self.url + "/layers.json"
        headers, response =  self.h.request(url,'GET')
        return headers, response

    ### PRIVATE ###

    def _setHttp(self):
        self.h = httplib2.Http()
        self.url = self.config.get("GeoServer","url")
        username = self.config.get("GeoServer","user")
        password = self.config.get("GeoServer","password")
        self.h.add_credentials(username, password)
        print self.url
        print username
        print password
        netloc = urlparse(self.url).netloc
        self.h.authorizations.append(
                httplib2.BasicAuthentication(
                        (username, password),
                        netloc,
                        self.url,
                        {},
                        None,
                        None,
                        self.h
                        ))

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config
