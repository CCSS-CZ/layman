# Lincense: ...
# authors: Michal, Jachym

import os, sys
#import glob
import mimetypes, time
import json
import logging

from geoserver.catalog import Catalog

class GeoServer:
    """GeoServer proxy in Layman
    """

    config = None
    cat = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

        self.cat = self._getConnection()

    ### LAYERS ###

    def getLayers(self):
        layers = self.cat.get_layers()
        return layers

    def getLayer(self, layerName):
        layer = self.cat.get_layer(layerName)
        return layer

    ### STYLE ###

    def getStyle(self, name):
        """Get style from geoserver
        """

        (name, suff) = os.path.splitext(name)
        style =  self.cat.get_style(name)
        return style.sld_body

    def postStyle(self, name, style):
        """Post new style into geoserver
        """

        return self.cat.create_style(name,style,overwrite=False)

    def putStyle(self, name, style):
        """Put existing style into geoserver
        """

        return self.cat.create_style(name,style,overwrite=True)

    ### Private ###

    def _getConnection(self):
        return Catalog(self.config.get("GeoServer","url"),
                self.config.get("GeoServer","user"), 
                 self.config.get("GeoServer","password"))

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config
