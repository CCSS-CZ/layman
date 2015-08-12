# Lincense: ...

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
    
