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

    jsonHeader = {
        "Content-type": "application/json"#,
        #"Accept": "application/json"
    }

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

    def getLayer(self, workspace, name):
        #print "*** GSREST *** getLayer ***"
        url = self.url + "/layers/" + workspace + ":" + name + ".json"
        #print "*** url ***"
        #print url
        headers, response =  self.h.request(url,'GET')
        #print "*** headers ***"
        #print headers
        #print "*** response ***"
        #print response
        return headers, response        

    def putLayer(self, workspace, name, data):
        url = self.url + "/layers/" + workspace + ":" + name + ".json"
        #print "*** GSREST *** putLayer ***"
        #print "*** url ***"
        #print url
        #print "*** data ***"
        #print data
        headers, response =  self.h.request(url,'PUT', data, self.jsonHeader)
        #print "*** headers ***"
        #print headers
        #print "*** response ***"
        #print response
        return headers, response        

    def deleteLayer(self, workspace, name):
        url = self.url + "/layers/" + workspace + ":" + name + ".json"
        headers, response =  self.h.request(url,'DELETE')
        return headers, response        

    ### FEATURE TYPES ###

    def getFeatureTypes(self, workspace, datastore):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + datastore + "/featuretypes.json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def postFeatureTypes(self, workspace, datastore, data):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + datastore + "/featuretypes.json"
        headers, response =  self.h.request(url,'POST', data, self.jsonHeader)
        return headers, response        

    def getFeatureType(self, workspace, datastore, name):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + datastore + "/featuretypes/" + name + ".json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def putFeatureType(self, workspace, datastore, name, data):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + datastore + "/featuretypes/" + name + ".json"
        headers, response =  self.h.request(url,'PUT',data, self.jsonHeader)
        return headers, response        

    def deleteFeatureType(self, workspace, datastore, name):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + datastore + "/featuretypes/" + name + ".json"
        headers, response =  self.h.request(url,'DELETE')
        return headers, response        

    ### DATA STORES ###

    def getDataStores(self, workspace):
        url = self.url + "/workspaces/" + workspace + "/datasores.json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def postDataStores(self, workspace, data):
        url = self.url + "/workspaces/" + workspace + "/datasores.json"
        headers, response =  self.h.request(url,'POST', data, self.jsonHeader)
        return headers, response        

    def getDataStore(self, workspace, name):
        url = self.url + "/workspaces/" + workspace + "/datasores/" +  name + ".json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def putDataStore(self, workspace, name, data):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + name + ".json"
        headers, response =  self.h.request(url,'PUT',data, self.jsonHeader)
        return headers, response        

    def deleteDataStore(self, workspace, name):
        url = self.url + "/workspaces/" + workspace + "/datasores/" + name + ".json"
        headers, response =  self.h.request(url,'DELETE')
        return headers, response        

    ### WORKSPACES ###

    def getWorkspaces(self):
        url = self.url + "/workspaces.json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def postWorkspaces(self, data):
        url = self.url + "/workspaces.json"
        headers, response =  self.h.request(url,'POST', data, self.jsonHeader)
        return headers, response        

    def getWorkspace(self, name):
        url = self.url + "/workspaces/" +  name + ".json"
        headers, response =  self.h.request(url,'GET')
        return headers, response        

    def putWorkspace(self, name, data):
        url = self.url + "/workspaces/" + name + ".json"
        headers, response =  self.h.request(url,'PUT',data, self.jsonHeader)
        return headers, response        

    def deleteDataStore(self, name):
        url = self.url + "/workspaces/" + name + ".json"
        headers, response =  self.h.request(url,'DELETE')
        return headers, response        

    ### GENERAL ###

    def getUrl(self, url):
        """ Get given url, authenticated."""
        ##print "*** GSREST *** getUrl ***"
        ##print "*** url ***"
        ##print url
        headers, response =  self.h.request(url,'GET')
        ##print "*** headers ***"
        ##print headers
        ##print "*** response ***"
        ##print response
        return headers, response        

    def postUrl(self, url, data):
        """ Post given url, authenticated."""
        headers, response =  self.h.request(url,'POST', data, self.jsonHeader)
        return headers, response        

    def putUrl(self, url, data):
        """ Put given url, authenticated."""
        #print "*** GSREST *** putUrl ***"
        ##print "*** url ***"
        ##print url
        ##print "*** data ***"
        ##print data
        headers, response =  self.h.request(url,'PUT', data, self.jsonHeader)
        #print "*** headers ***"
        #print headers
        #print "*** response ***"
        #print response
        return headers, response        

    def deleteUrl(self, url):
        """ Delete given url, authenticated."""
        headers, response =  self.h.request(url,'DELETE')
        return headers, response        

    ### PRIVATE ###

    def _setHttp(self):
        self.h = httplib2.Http()
        self.url = self.config.get("GeoServer","url")
        username = self.config.get("GeoServer","user")
        password = self.config.get("GeoServer","password")
        self.h.add_credentials(username, password)
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
