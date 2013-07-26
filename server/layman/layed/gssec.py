# Lincense: ... 
# authors: Michal, Jachym

import os, sys
import mimetypes, time
import logging

class GsSec:
    """Editor of GeoServer layer.properties security configuration file
    """

    config = None
    gsDir  = None 
    """ Path to geoserver directory, e.g. "/data/geoserver/"
    """

    laySec = {} 
    """ Layer security. Representation of the content of the layers.properties file.
    A dictionary is organised into the structure of a tree:
    Levels: workspace, layer, right. 
    Leaf: list of roles.
    """

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)
        self.gsDir = self.config.get("GeoServer","gsdir")

        # Read the file layer.properties into self.laySec
        self.readLayerProp()


    ### Read/Write ###

    def readLayerProp(self):
        """ Read the file layer.properties into self.laySec
        """
        # TODO: Handle and preserve comments

        with open(self.getLayerPropPath(), "r") as f:
            for line in f:

                # cut off comments
                comPos = line.find("#")
                if comPos != -1:
                    line = line[0:comPos]
                
                # remove whitespaces
                line = ''.join(line.split())

                if len(line) <= 0:
                    continue

                # here we should have st. meaningful, eg. 
                # hasici.pest.r=ROLE_HASICI,ROLE_PEST

                splitEq = line.split("=")
                if len(splitEq) < 2: 
                    continue

                splitDot = splitEq[0].split(".")
                if len(splitDot) < 3:
                    continue

                splitCom = splitEq[1].split(",")
                if len(splitCom) < 1:
                    continue
        
                # here the parsing should be more or less fine

                # interpretation
                ws = splitDot[0]
                layer = splitDot[1]
                right = splitDot[2]
                rolelist = splitCom

                print "orig rule: ws=" + ws + " layer=" + layer +" right=" + right +" rolelist=" + repr(rolelist)

                # set the rule
                self.setRule(ws, layer, right, rolelist)

    def writeLayerProp(self):
        """ Write the self.laySec into layer.properties file
        """
        # TODO: Handle and preserve comments

        with open(self.getLayerPropPath(), "w") as f:
        
            for (ws, val1) in self.laySec.iteritems():
                for (layer, val2) in val1.iteritems():          # val1 - laySec[ws]
                    for (right, rolelist) in val2.iteritems():  # val2 - laySec[ws][layer]

                        rule = ws+'.'+layer+'.'+right + '=' + ','.join(rolelist) + '\n'
                        print "rule: " + rule
                        f.write(rule)

        # the file should be automatically closed here

    ### Set/Unset Rule ###

    def setRule(self, ws, layer, right, rolelist):
        """ Sets the rule """
    
        if ws not in self.laySec:
            self.laySec[ws] = {}
        if layer not in self.laySec[ws]:
            self.laySec[ws][layer] = {}

        self.laySec[ws][layer][right] = rolelist

    def unsetRule(self, ws, layer, right):
        """ Removes (or comments out) the specified rule """
        # TODO

    ### Get access rights ###

    def getRoles(self, ws, layer, right):
        """ Get the list of roles that can perform the given right
        None means no rule specified.
        """
        if ws in self.laySec:
            if layer in self.laySec[ws]:
                if right in self.laySec[ws][layer]:
                    return self.laySec[ws][layer][right]
        else:
            return None

        # TODO: This ^ does not take into acount the '*' settings - WRONG!!!

    ### Syntactic sugar ###

    def secureWorkspace(self, ws, rolelist):
        """ Sets read, write and admin rights.
        Does not affect rules for particular layers that may already exist """
        self.setRule(ws, "*", "r", rolelist)
        self.setRule(ws, "*", "w", rolelist)
        self.setRule(ws, "*", "a", rolelist)

    ### Auxiliary functions ###

    def getLayerPropPath(self):
        return self.gsDir + "data/security/layers.properties"

    def reloadConfig(self):
        from gsrest import GsRest
        gsr = GsRest(self.config)
        gsr.putReload()

    ### PRIVATE ###

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config = config
