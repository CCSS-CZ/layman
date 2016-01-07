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
#import glob
import mimetypes, time
import json
import logging

from geoserver.catalog import Catalog

class GsConfig:
    """GeoServer proxy in Layman
    """

    config = None
    cat = None
    ws = None

    def __init__(self,config = None, ws = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

        self.ws = ws

        self.cat = self._getConnection()

    ### LAYERS ###

    def getLayers(self):
        layers = self.cat.get_layers()
        return layers

    def getLayer(self, layerName):
        layer = self.cat.get_layer(layerName)
        return layer

    ### FEATURE STORE ###

    def createFeatureStore(self, filePathNoExt, gsWorkspace, dataStoreName):
        """ Create "Feature store" in the gsconfig.py stle
        """
        from geoserver.util import shapefile_and_friends
        shapefile_plus_sidecars = shapefile_and_friends(filePathNoExt)

        if not gsWorkspace:
            ws = self.cat.get_default_workspace()
        else:
            ws = self.cat.get_workspace(gsWorkspace)
        self.cat.create_featurestore(dataStoreName, shapefile_plus_sidecars, ws)

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

        url = self.config.get("GeoServer","url")
        
        if url[-1] == "/":
            url = url[:-1]

        if self.ws:
            url += "/workspaces/"+self.ws

        return Catalog(url,
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
