# Lincense: ...
# authors: Michal, Jachym

import os, sys
import mimetypes, time
import json
import logging

import httplib2
from urlparse import urlparse

class CkanApi:
    """Ckan API v.3 
    """

    config = None
    h = None        # Http()
    url = None      # http://ckan.ccss.cz/api/3

    jsonHeader = {
        "Content-type": "application/json"#,
        #"Accept": "application/json"
    }

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)
        self._setHttp()

    ### CKAN API v.3

    # package_list - list of packages (=datasets)
    # eg: http://ckan.ccss.cz/api/3/action/package_list
    def getPackageList(self, limit="0", offset="0"):
        """ Get package list """
        url = self.url + "/action/package_list"
        if limit != "0":
            url = url + "?limit=" + limit + "&offset=" + offset
        headers, response =  self.h.request(url,'GET')
        return headers, response

    # package_show - details for the given package (=dataset)
    def getPackageShow(self, id):
        """ Show particlaur package
        id - id of the package. Can be retrieved by getPackageList """
        url = self.url + "/action/package_show?id=" + id
        headers, response =  self.h.request(url,'GET')
        return headers, response
        
    ### GENERAL ###

    def getUrl(self, url):
        """ Get given url, authenticated."""
        logging.debug("[CkanApi][getUrl] GET URL: %s"% url)        
        head, cont =  self.h.request(url,'GET')
        if (not head['status'] or head['status']!='200'):
            logging.debug("[CkanApi][getUrl] Response headers: %s"% head)        
            logging.debug("[CkanApi][getUrl] Response content: %s"% cont)        
        return head, cont

    def postUrl(self, url, data):
        """ Post given url, authenticated."""
        logging.debug("[CkanApi][postUrl] POST URL: %s"% url)        
        head, cont =  self.h.request(url,'POST', data, self.jsonHeader)
        logging.debug("[CkanApi][postUrl] Response headers: %s"% head)        
        logging.debug("[CkanApi][postUrl] Response content: %s"% cont)        
        return head, cont

    def putUrl(self, url, data):
        """ Put given url, authenticated."""
        logging.debug("[CkanApi][putUrl] PUT URL: %s"% url)        
        head, cont =  self.h.request(url,'PUT', data, self.jsonHeader)
        logging.debug("[CkanApi][putUrl] Response headers: %s"% head)        
        logging.debug("[CkanApi][putUrl] Response content: %s"% cont)        
        return head, cont

    def deleteUrl(self, url):
        """ Delete given url, authenticated."""
        logging.debug("[CkanApi][deleteUrl] DELETE URL: %s"% url)        
        head, cont =  self.h.request(url,'DELETE')
        logging.debug("[CkanApi][deleteUrl] Response headers: %s"% head)        
        logging.debug("[CkanApi][deleteUrl] Response content: %s"% cont)        
        return head, cont

    ### PRIVATE ###

    def _setHttp(self):
        self.h = httplib2.Http()
        self.url = self.config.get("CKAN","CkanApiUrl")
        # username = self.config.get("GeoServer","user")
        # password = self.config.get("GeoServer","password")
        # self.h.add_credentials(username, password)
        #netloc = urlparse(self.url).netloc
        #self.h.authorizations.append(
        #        httplib2.BasicAuthentication(
        #                (username, password),
        #                netloc,
        #                self.url,
        #                {},
        #                None,
        #                None,
        #                self.h
        #                ))

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config
