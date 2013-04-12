# Lincense: ...
# authors: Michal, Jachym

import os, sys
import mimetypes, time
import json
import logging

import xml.etree.ElementTree as Xml

class GsXml:
    """Editor of GeoServer XML config files
    """

    config = None
    gsDir = None 
    """ Path to geoserver directory, e.g. "/data/geoserver/"
    """

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)

        self.gsDir = self.config.get("GeoServer","gsdir")

    def setLayerStyle(self, layerWorkspace, dataStoreName, layerName, styleWorkspace, styleName):
        """ Set the default style of given layer.
            Set styleWorkspace to None to refer to styles with no workspace.
        """
        # Open the style XML
        stylePath = self.getStyleXmlPath(styleWorkspace, styleName)
        styleTree = Xml.parse(stylePath)
        styleRoot = styleTree.getroot()
        logging.debug("[GsXml][setLayerStyle] Assigning style '%s'"% stylePath)

        # Get the style id 
        styleId = styleRoot.find("./id").text #<style><id>
        logging.debug("[GsXml][setLayerStyle] with <Id> '%s'"% styleId)

        # Open the layer XML
        layerPath = self.getLayerPath(layerWorkspace, dataStoreName, layerName)
        layerTree = Xml.parse(layerPath)
        layerRoot = layerTree.getroot()
        logging.debug("[GsXml][setLayerStyle] to layer '%s'"% layerPath)

        # Change the default style
        layerRoot.find("./defaultStyle/id").text = styleId #<layer><defaultStyle<id>

        # Write the layer file
        layerTree.write(layerPath)
        logging.debug("[GsXml][setLayerStyle] Style assigned")

        # TODO: do some checks,
        # close & return

    def getLayerPath(self, layerWorkspace, dataStoreName, layerName):      
        path = self.gsDir + "data/workspaces/" + layerWorkspace + "/" + dataStoreName + "/" + layerName + "/layer.xml" 
        # TODO: make it platform independent
        return path

    def getStyleXmlPath(self, styleWorkspace, styleName): 
        if styleWorkspace == None: # Style with no workspace
            path = self.gsDir + "data/styles/" + styleName + ".xml"
        else: # Style from a workspace
            path = self.gsDir + "data/workspaces/" + styleWorkspace + "/styles/" + styleName + ".xml"
        return path

    ### PRIVATE ###

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config = config
