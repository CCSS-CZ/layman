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

    def __init__(self, config=None, url=None):
        """constructor
        """
        self._setConfig(config)

        # Check if we were given CKAN URL from the client
        # If yes, use it, otherwise use the one from our config file
        if url is None or url.strip() == "":
            self.url = self.config.get("CKAN","CkanApiUrl")
        else:
            if url[-1] != "/":
                url += "/"
            self.url = url + "api/3"

        self._setHttp()

    ### CKAN API v.3

    def getResourceSearch(self, rFormat, limit=None, offset=None):
        """ get resources of specified resource format
        """
        url = self.url + "/action/resource_search?query=format:" + rFormat
        if limit is not None:
            url += "&limit=" + str(limit)
        if offset is not None:
            url += "&offset=" + str(offset)

        headers, response =  self.h.request(url,'GET')
        return headers, response

    # package_list - list of packages (=datasets)
    # eg: http://ckan.ccss.cz/api/3/action/package_list
    def getPackageList(self, limit="0", offset="0"):
        """ Get package list """
        url = self.url + "/action/package_list"
        if limit != "0":
            url = url + "?limit=" + limit + "&offset=" + offset
        logging.debug("[CkanApi][getPackageList] GET URL: %s"% url)        
        head, cont =  self.h.request(url,'GET')
        if (not head['status'] or head['status']!='200'):
            logging.debug("[CkanApi][getUrl] Response headers: %s"% head)        
            logging.debug("[CkanApi][getUrl] Response content: %s"% cont)        
        return head, cont

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
