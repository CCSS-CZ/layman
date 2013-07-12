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
    gsDir  = None 
    """ Path to geoserver directory, e.g. "/data/geoserver/"
    """
    userPwd = None

    # userGroupFile = None # File users.xml
    # userGroupXml  = None # XML from users.xml

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)

        self.gsDir = self.config.get("GeoServer","gsdir")
        self.userPwd = self.config.get("GeoServer","userpwd")

    ### User Management ###

    #TODO: Get rid of the hardcoded namespaces
    # try Xml.register_namespace() and also the Xml.write(default_namespace=...)

    def createUserWithGroups(self, user, grouplist):
        """ Create new user and assign provided groups 
        Refuse, if user already exist. 
        Create the groups, if they don't exist yet """

        # Read UserGroup XML
        ugPath = self.getUserGroupPath()
        ugTree = Xml.parse(ugPath)
        ugRoot = ugTree.getroot()

        # Serach for the user
        userElem = ugRoot.find("./{http://www.geoserver.org/security/users}users/user[@name='"+user+"']")
        if (userElem):
            return(409, "User "+user+" already exists")

        # Create user and assign groups
        # We don't check for already-assigned groups that may need to be unassigned
        # as we expect to be creating a brand new user here
        self._createUser(user, self.userPwd, ugRoot)
        for gr in grouplist:
            self._createGroup(gr, ugRoot)
            self._assignGroupToUser(user, gr, ugRoot)

        # Write
        ugTree.write(ugPath)

        return (201,"User created")

    def updateUserWithGroups(self, user, grouplist):
        """ Update existing user with given groups.
        If the user does not exist, create it. 
        """

        # Read UserGroup XML
        ugPath = self.getUserGroupPath()
        ugTree = Xml.parse(ugPath)
        ugRoot = ugTree.getroot()

        # Serach for the user
        userElem = ugRoot.find("./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user[@name='"+user+"']")

        if (userElem is None):
            #print "USER NOT FOUND"
            return self.createUserWithGroups(user, grouplist)

        #print "USER FOUND"
        # The user does exist, update it
        # Check every group in GS and check for changes

        newGroups = grouplist

        groupElems = ugRoot.findall("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group")
        for grEl in groupElems:

            #print repr(grEl) + "\n"

            wasMember = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") is not None 
            groupName = grEl.attrib["name"]
            isMember  = groupName in grouplist

            if isMember:
                newGroups.remove(groupName)
            #print "group name: " + groupName + "\n"

            if wasMember and not isMember:
                #print "byl a neni: " + groupName + "\n"
                self._removeGroupFromUser(user, groupName, ugRoot)

            elif not wasMember and isMember:
                #print "nebyl a je: " + groupName + "\n"
                self._assignGroupToUser(user, groupName, ugRoot)

            # otherwise leave unchanged

        # Create and assign new groups
        for gr in newGroups:
            self._createGroup(gr, ugRoot)
            self._assignGroupToUser(user, gr, ugRoot)

        # Write
        ugTree.write(ugPath)

        return (200, "User updated")

    def deleteUser(self, user):
        """ Delete user and erase all his group membership
        """

        # Read UserGroup XML
        ugPath = self.getUserGroupPath()
        ugTree = Xml.parse(ugPath)
        ugRoot = ugTree.getroot()

        # Serach for the user
        xPath = "./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user[@name='"+user+"']"
        userElem = ugRoot.find(xPath)
        #print "xPath: " + repr(xPath)
        #print "userElem: " + repr(userElem)

        # erase group membership
        groupElems = ugRoot.findall("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group")
        for grEl in groupElems:
            memberElem = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") 
            if memberElem is not None:  
                grEl.remove(memberElem)
        
        # delete user 
        usersElem = ugRoot.find("./{http://www.geoserver.org/security/users}users")
        usersElem.remove(userElem)

        # Write
        ugTree.write(ugPath)

        return (200, "User deleted")

    def _createUser(self, user, pwd, ugRoot):
        """ Create user """
        # users.xml:
        # <user enabled="true" name="hasic1" password="crypt1:2DFyNWnqJIfUL0j8bGMUeA=="/>

        userElem = Xml.Element("{http://www.geoserver.org/security/users}user", {"enabled":"true", "name":user, "password":pwd}) 
        usersElem = ugRoot.find("./{http://www.geoserver.org/security/users}users")
        usersElem.append(userElem)

    def _createGroup(self, group, ugRoot):
        """ Create group 
        Do nothing, if it already exists """
        # users.xml:
        # <group enabled="true" name="hasici">
        # </group>

        # Search for the group
        groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
        #print "group elem: " + repr(groupElem)
        if groupElem is not None: # if it is already there
            return    # do nothing

        # Create the group
        groupElem = Xml.Element("{http://www.geoserver.org/security/users}group", {"enabled":"true", "name":group})
        groupsElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups")
        groupsElem.append(groupElem)

    def _assignGroupToUser(self, user, group, ugRoot):
        """ Assign the group membership to the user
        Do nothing, if it is already assigned """
        # users.xml:
        # <group enabled="true" name="hasici">
        #    <member username="hasic1"/>
        # </group>
               
        groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
        memberElem = groupElem.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']")
        if memberElem is not None: # if the group is already assigned
            return     # do nothing

        memberElem = Xml.Element("{http://www.geoserver.org/security/users}member", {"username":user})
        groupElem.append(memberElem)

    def _removeGroupFromUser(self, user, group, ugRoot):
        """ Remove group membership """

        groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
        if groupElem is not None:
            #print "nasel grupu"
            memberElem = groupElem.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']")

            if memberElem is not None:
                #print "nasel membra"
                groupElem.remove(memberElem)            
            #else:
            #    print "nenasel membra"
        #else:
        #    print "nenasel grupu"

    def getUserGroupPath(self):
        path = self.gsDir + "data/security/usergroup/default/users.xml"
        return path

    def gerRolePath(self):
        path = self.gsDir + "data/security/role/default/roles.xml"
        return path

    def getSecurityPath(self):
        path = self.gsDir + "data/security/layers.properties"
        return path

    ### Layer Style ###

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
