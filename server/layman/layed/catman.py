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

import logging
from  layman.errors import LaymanError
import os
import sys

class CatMan:
    """Micka manager
    Create, get, update and delete metadata.    
    """

    config = None

    def __init__(self,config = None):
        """constructor
        """

        ## get configuration parser
        self._setConfig(config)

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

    # METADATA OF DATA

    def createDataRecord(self """, params """): # zjistit od stepana, ktery vsechny parametry jsou potreba pro minimalni validni record
    """ Create new metadata record for data
    """
        return uuid
       
    def getDataRecord(self, dataname, datagroup, datatype):
    """ Get metadata record for given data
    Params:
    dataname - name of view/table/file
    datagroup - group name (schema or directory)
    datatype - [table|view|file]""" # mohli bychom zavest nejake "dataid", pak bychom to ale museli vsude zpropagovat vcetne klienta
    # takhle v tuto chvili vypada jednoznacna reference
    # uuid bude ulozene v datapadu 

        return result # ziskana metadata v jsonu

    def updateDataRecord((self, dataname, datagroup, datatype """, params to update """): 
    """ Update metadata record of given data
    """

       return result # jak to dopadlo

    def deleteDataRecord(self, dataname, datagroup, datatype):
    """ Delete metadata record of given data 
    """

    # METADATA OF SERVICES

    # Budeme potrebovat jeste metadata sluzeb. Cilem je, aby publikovane vrstvy/sluzby byly vyhledatelne v Micce v MapComposeru...
    
