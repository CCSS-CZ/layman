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
    gsDataDir  = None 
    """ Path to geoserver directory, e.g. "/data/geoserver/"
    """
    userPwd = None

    caseSensitive = True # False => convert the names to lowercase # TODO: make sure we use it all around # TODO: should we rahter remove it?

    # userGroupFile = None # File users.xml
    # userGroupXml  = None # XML from users.xml

    def __init__(self,config = None):
        """constructor
        """
        self._setConfig(config)

        self.gsDataDir = self.config.get("GeoServer","datadir")
        self.userPwd = self.config.get("GeoServer","userpwd")

    ### USERS & GROUPS ###

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
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            userElem = ugRoot.find("./{http://www.geoserver.org/security/users}users/user[@name='"+user+"']")
        else: # Python 2.6 or less
            userElem = self._xPath26Find(ugRoot, "./{http://www.geoserver.org/security/users}users/user", "name", user)
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

        if self.caseSensitive is False:
            grouplist = map(str.lower, grouplist)

        # Read UserGroup XML
        ugPath = self.getUserGroupPath()
        ugTree = Xml.parse(ugPath)
        ugRoot = ugTree.getroot()

        # Serach for the user
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            userElem = ugRoot.find("./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user[@name='"+user+"']")
        else: # Python 2.6 or less
            userElem = self._xPath26Find(ugRoot,"./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user","name",user)

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
            if sys.hexversion >= 0x02070000: # Python 2.7 or more
                wasMember = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") is not None 
            else: # Python 2.6 or less
                wasMember = self._xPath26Find(grEl, "{http://www.geoserver.org/security/users}member", "username", user) is not None 

            groupName = grEl.attrib["name"]
            if self.caseSensitive is False:
                groupName = groupName.lower()
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

        # Search for the user
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            userElem = ugRoot.find("./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user[@name='"+user+"']")
        else: # Python 2.6 or less
            userElem = self._xPath26Find(ugRoot, "./{http://www.geoserver.org/security/users}users/{http://www.geoserver.org/security/users}user","name",user)

        #print "userElem: " + repr(userElem)

        # erase group membership
        groupElems = ugRoot.findall("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group")
        for grEl in groupElems:
            if sys.hexversion >= 0x02070000: # Python 2.7 or more
                memberElem = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") 
            else: # Python 2.6 or less
                memberElem = self._xPath26Find(grEl,"{http://www.geoserver.org/security/users}member", "username", user) 
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
        """ Create group. 
        Create also the basic group role and assign it to the group.
        Secure the corresponding workspace for this group.
        If the group already exists, make sure that the group role does exist and is properly assigned. But don't touch the workspace security settings."""

        # Search for the group
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
        else: # Python 2.6 or less
            groupElem = self._xPath26Find(ugRoot, "./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group", "name", group)
        brandNew = False
        if groupElem is None: 
            # Create the group
            groupElem = Xml.Element("{http://www.geoserver.org/security/users}group", {"enabled":"true", "name":group})
            groupsElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups")
            groupsElem.append(groupElem)
            brandNew = True

        # Create and assign the group role
        role = self.createGroupRole(group)

        # If the group was newly created, secure the corresponding workspace
        if brandNew:
            from layman.layed.gssec import GsSec
            gss = GsSec(self.config)
            gss.secureWorkspace(ws=group, rolelist=[role])

    def _assignGroupToUser(self, user, group, ugRoot):
        """ Assign the group membership to the user
        Do nothing, if it is already assigned """
        # users.xml:
        # <group enabled="true" name="hasici">
        #    <member username="hasic1"/>
        # </group>
               
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
            memberElem = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") 
        else: # Python 2.6 or less
            groupElem = self._xPath26Find(ugRoot, "./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group", "name", group)
            memberElem = self._xPath26Find(grEl,"{http://www.geoserver.org/security/users}member", "username", user) 
        if memberElem is not None: # if the group is already assigned
            return     # do nothing

        memberElem = Xml.Element("{http://www.geoserver.org/security/users}member", {"username":user})
        groupElem.append(memberElem)

    def _removeGroupFromUser(self, user, group, ugRoot):
        """ Remove group membership """

        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            groupElem = ugRoot.find("./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group[@name='"+group+"']")
        else: # Python 2.6 or less
            groupElem = self._xPath26Find(ugRoot, "./{http://www.geoserver.org/security/users}groups/{http://www.geoserver.org/security/users}group", "name", group)
        if groupElem is not None:
            #print "nasel grupu"
            if sys.hexversion >= 0x02070000: # Python 2.7 or more
                memberElem = grEl.find("{http://www.geoserver.org/security/users}member[@username='"+user+"']") 
            else: # Python 2.6 or less
                memberElem = self._xPath26Find(grEl,"{http://www.geoserver.org/security/users}member", "username", user) 

            if memberElem is not None:
                #print "nasel membra"
                groupElem.remove(memberElem)            
            #else:
            #    print "nenasel membra"
        #else:
        #    print "nenasel grupu"

    def getUserGroupPath(self):
        os.path.join(self.gsDataDir, "security", "usergroup", "default", "users.xml")
        return path

    ### ROLES ###

    def createGroupRole(self, group):
        """ Create ROLE_<group> role and assign it to the group. 
        Returns role name.
        """
        # Role name
        role = self.getGroupRoleName(group)
        # Create and assign
        self.createAndAssignRole(group, role)
        return role        

    def createReadLayerRole(self, group, layer):
        """ Create READ_<group>_<layer> role and assign it to the group. 
        If it is already there, do nothing.
        Returns role name. 
        """
        # Role name
        role = self.getReadLayerRoleName(group, layer)
        # Create and assign
        self.createAndAssignRole(group, role)
        return role        
  
    def getReadLayerRoleName(self, group, layer):
        """ Get the name of the role that is defined for Read Layer Access.
        This is defined on app logic level, we don't dive into layers.properties.
        """
        # Role name
        role = "READ_" + group + "_" + layer
        return role
 
    def getGroupRoleName(self, group):
        role = "ROLE_" + group
        return role

    def getReadLayerGroups(self, group, layer):
        """ Get the list of all the groups that have 
        the role "READ_<group>_<layer>" assigned.
        """
        readGroups = []
        role = "READ_" + group + "_" + layer

        # Read Roles XML
        rrPath = self.getRolesPath()
        rrTree = Xml.parse(rrPath)
        rrRoot = rrTree.getroot()

        # <ns0:groupList>
        groupListElem = rrRoot.find("{http://www.geoserver.org/security/roles}groupList") 

        # list of such <ns0:groupRoles> that have appropriate <ns0:roleRef> children
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            groupRolesElems = groupListElem.findall(".//{http://www.geoserver.org/security/roles}roleRef[@roleID='"+role+"']/..")
        else: # Python 2.6 or less
            groupRolesElems = self._xPath26Findall(groupListElem, ".//{http://www.geoserver.org/security/roles}roleRef", "roleID", role, "..")
        #groupRolesElems = groupListElem.findall(".//{http://www.geoserver.org/security/roles}roleRef/..")

        # Get the names
        for gre in groupRolesElems:
            groupname = gre.get("groupname")           
            readGroups.append(groupname)
            logging.debug("[GsXml]getReadLayerGroups[]Layer %s:%s is given to * %s *"% (group, layer, groupname))

        return readGroups
 
    def createAndAssignRole(self, group, role):
        """ Create role of the given name and assign it to the group.
        If it is already there, do nothing. 
        """
        # Read Roles XML
        rrPath = self.getRolesPath()
        rrTree = Xml.parse(rrPath)
        rrRoot = rrTree.getroot()

        # Create role and assign it to the group
        changed1 = self._createRole(role, rrRoot)
        changed2 = self._assignRoleToGroup(group, role, rrRoot)

        # Write
        if changed1 or changed2:
            rrTree.write(rrPath)

    def assignRoleToUsersAndGroups(self, role, grouplist, userlist):
        """ Assign Role To Users And Groups.
        Unassign from the rest.
        We assume, that the role, users and groups already exist.
        """

        logging.debug("[GsXml][assignRoleToUsersAndGroups] Params: role '%s', userlist '%s', grouplist '%s'"% (str(role), str(userlist), str(grouplist)))

        # Read Roles XML
        rrPath = self.getRolesPath()
        rrTree = Xml.parse(rrPath)
        rrRoot = rrTree.getroot()

        # Assign role to groups
        self._assignRoleToUsersOrGroups(role, ug="group", uglist=grouplist, rrRoot=rrRoot)

        # Assign role to users
        self._assignRoleToUsersOrGroups(role, ug="user", uglist=userlist, rrRoot=rrRoot)

        # Write
        rrTree.write(rrPath)

        return (200, "Roles assigned")

    def _assignRoleToUsersOrGroups(self, role, ug, uglist, rrRoot):

        if uglist is None:
            uglist = []

        if self.caseSensitive is False:
            uglist = map(str.lower, uglist)

        newRecords = uglist # list of possible users/groups that do not have their record in the roles file yet

        #print "[_assignRoleToUsersOrGroups] " + role + " " + ug + " " + str(uglist)

        # Go throug the existing records and check for changes
        ugRolesElems = rrRoot.findall("./{http://www.geoserver.org/security/roles}"+ug+"List/{http://www.geoserver.org/security/roles}"+ug+"Roles")
        for ugrEl in ugRolesElems:

            # Check for the role
            if sys.hexversion >= 0x02070000: # Python 2.7 or more
                roleRefEl = ugrEl.find("{http://www.geoserver.org/security/roles}roleRef[@roleID='"+role+"']")
            else: # Python 2.6 or less
                roleRefEl = self._xPath26Find(ugrEl, "{http://www.geoserver.org/security/roles}roleRef", "roleID", role)

            wasMember = roleRefEl is not None 
            ugName = ugrEl.attrib[ug+"name"]
            if self.caseSensitive is False:
                ugName = ugName.lower()
            isMember  = ugName in uglist

            #print str(newRecords)
            #print ugName

            if ugName in newRecords:
                newRecords.remove(ugName) # tick off

            # Unassign
            if wasMember and not isMember:
                ugrEl.remove(roleRefEl) # both elems do exist here

            # Assign
            elif not wasMember and isMember:
                roleRefElem = Xml.Element("{http://www.geoserver.org/security/roles}roleRef", {"roleID":role})
                ugrEl.append(roleRefElem)

            # otherwise leave unchanged

        # Go through the possibly remaining users/groups from the given list
        for nr in newRecords:
            
            # Create the user/group record
            ugRolesElem = Xml.Element("{http://www.geoserver.org/security/roles}"+ug+"Roles", {ug+"name":nr})
            ugListElem  = rrRoot.find("./{http://www.geoserver.org/security/roles}"+ug+"List")
            ugListElem.append(ugRolesElem)

            # Assign the role
            roleRefElem = Xml.Element("{http://www.geoserver.org/security/roles}roleRef", {"roleID":role})
            ugRolesElem.append(roleRefElem)

    def _createRole(self, role, rrRoot):
        """ Create Role. If exists, do nothing. """

        changed = False

        # Check for the role
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            roleElem = rrRoot.find("./{http://www.geoserver.org/security/roles}roleList/{http://www.geoserver.org/security/roles}role[@id='"+role+"']")
        else: # Python 2.6 or less
            roleElem = self._xPath26Find(rrRoot, "./{http://www.geoserver.org/security/roles}roleList/{http://www.geoserver.org/security/roles}role", "id", role)

        if roleElem is None:
            # Create the role
            roleElem     = Xml.Element("{http://www.geoserver.org/security/roles}role", {"id":role}) 
            roleListElem = rrRoot.find("./{http://www.geoserver.org/security/roles}roleList")
            roleListElem.append(roleElem)      
            changed = True
        
        return changed 

    def _assignRoleToGroup(self, group, role, rrRoot):
        """ Assign role to group. If already assigned, do nothing. """

        changed = False

        # Check the group record
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            groupRolesElem = rrRoot.find("./{http://www.geoserver.org/security/roles}groupList/{http://www.geoserver.org/security/roles}groupRoles[@groupname='"+group+"']")
        else: # Python 2.6 or less
            groupRolesElem = self._xPath26Find(rrRoot,"./{http://www.geoserver.org/security/roles}groupList/{http://www.geoserver.org/security/roles}groupRoles","groupname",group)

        if groupRolesElem is None:
            # Create the group record
            groupRolesElem = Xml.Element("{http://www.geoserver.org/security/roles}groupRoles", {"groupname":group})
            groupListElem  = rrRoot.find("./{http://www.geoserver.org/security/roles}groupList")
            groupListElem.append(groupRolesElem)
            changed = True

        # Check if the role is already assigned
        if sys.hexversion >= 0x02070000: # Python 2.7 or more
            roleRefElem = groupRolesElem.find("./{http://www.geoserver.org/security/roles}roleRef[@roleID='"+role+"']")
        else: # Python 2.6 or less
            roleRefElem = self._xPath26Find(groupRolesElem,"./{http://www.geoserver.org/security/roles}roleRef","roleID",role)

        if roleRefElem is None:
            # Assign the role
            roleRefElem = Xml.Element("{http://www.geoserver.org/security/roles}roleRef", {"roleID":role})
            groupRolesElem.append(roleRefElem)
            changed = True

        return changed

    def getRolesPath(self):
        path = os.path.join(self.gsDataDir, "security","role","default","roles.xml")
        return path

    ### LAYER STYLE ###

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
        path = os.path.join(self.gsDataDir, "workspaces", layerWorkspace, dataStoreName, layerName , "layer.xml")
        return path

    def getStyleXmlPath(self, styleWorkspace, styleName): 
        if styleWorkspace == None: # Style with no workspace
            path = os.path.join(self.gsDataDir, "styles", styleName, ".xml")
        else: # Style from a workspace
            path = os.path.join(self.gsDataDir, "workspaces", styleWorkspace, "styles", styleName, ".xml")
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

    def _xPath26Find(self, xml, chain, var, value):
        elems = xml.findall(chain)
        elem = None
        if elems is not None:
            for celem in elems:
                if celem.get(var) == value:
                    elem = celem
        return elem

    def _xPath26Findall(self, xml, chain1, var, value, chain2):
        """ Findall with XPath for Python 2.6 or lower
            xml.findall(chain1[@var=value]/chain2)            
        """
        elems1 = xml.findall(chain1)
        elems2 = []
        if elems1 is not None:
            for e1 in elems1:
                if e1.get(var) == value:
                    es2 = e1.findall(chain2)
                    elems2 += e2

        return elems2

