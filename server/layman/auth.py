# License: ....
# authors: Michal, Jachym

# TODO: 
# * Finish LaymanAuthLiferay
# * Finish LaymanAuthHSRS
# * License

import os
import json
import logging

from errors import LaymanError, AuthError

class LaymanAuth: 

    config = None
    auth = None

    authorised = False

    def __init__(self,config=None):
        self._setConfig(config)

    # Service Authorisation Methods #
    
    def canread(self):
        """Can particular user read from the service?

            :returns: boolean
        """
        return False 

    def canwrite(self):
        """Can particular user write to the service?

            :returns: boolean
        """
        return False


    # User/Group configuration methods #

    def getUserName(self):
        logging.warning("[LaymanAuth][getUserName] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None

    def getFSDir(self):
        """Returns full abs path to target file manager directory according to
        configuration value and user

        NOTE: this method is to be overwritten according to specified
        Authorization method. This default method returns path to working
        directory, regardless, which user is logged in.

        :returns: path absolute path to target dir
        """
        
        # target dir configuration value
        dirname = os.path.abspath(
                self.config.get("FileMan","targetdir")
                )

        # exists or not - create
        if not os.path.isdir(dirname):
            try:
                os.mkdir(dirname)
            except OSError,e:
                raise AuthError(500,"Could not create target directory [%s]:%s"%\
                        (dirname, e))

        # check directory permission
        if not os.access(dirname, 7):
            raise AuthError(500,"Write access denied for target directory [%s]"% (dirname))

        return dirname

    def getFSGroupDir(self, desired=None):
        """ roleName ~ Group Dir. Uses getRole()
        """
        role = self.getRole(desired)
        groupDir = self.config.get("FileMan","homedir") + role["roleName"]
        return groupDir

    def getFSUserDir(self, desired=None):
        logging.warning("[LaymanAuth][getFSUserDir] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None
    
    def getDBSchema(self, desired=None):
        logging.warning("[LaymanAuth][getDBSchema] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None
    
    def getGSWorkspace(self,desired=None):
        logging.warning("[LaymanAuth][getGSWorkspace] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None

    def getRole(self, desired=None):
        logging.warning("[LaymanAuth][getRole] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None

    def getRoles(self):
        logging.warning("[LaymanAuth][getRoles] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return []

    def getAllRoles(self):
        logging.warning("[LaymanAuth][getallRoles] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return []

    def getAllRolesStr(self):
        logging.warning("[LaymanAuth][getallRoles] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None

    def canDelete(self):
        logging.warning("[LaymanAuth][getallRoles] Call of Authorisation class ancestor. Was it intended? No authorisation will be granted here. Try descendants - e.g. LaymanAuthLiferay or LaymanAuthOpen.")
        return None

    # Private Methods #

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config


class LaymanAuthLiferay(LaymanAuth):

    # JSESSIONID from Liferay, provided by the Client
    JSESSIONID = None

    # Has been succesfully authorised
    authorised = False

    # Json reply from Slavek's service to http://erra.ccss.cz/g4i-portlet/service/sso/validate/JSESSIONID request
    # Example:
    # {
    #    resultCode: "0",
    #    userInfo: {
    #       lastName: "Doe",
    #       email: "test@ccss.cz",
    #       roles: [
    #           {
    #               roleTitle: "User",
    #               roleName: "User"
    #           },
    #           {
    #               roleTitle: "pozarnaja",
    #               roleName: "hasici"
    #           }, 
    #       ],
    #       userId: 10432,
    #       screenName: "test",
    #       language: "en",
    #       firstName: "John",
    #       groups: [ ]
    #   },
    #   leaseInterval: 1800
    # }
    authJson = None

    def __init__(self,config=None,JSESSIONID=None):
        LaymanAuth.__init__(self,config)

    # Authorise 
    def authorise(self, JSESSIONID):
        """ Authorise the given JSESSIONID against the Slavek's service:
        call the service and process the response """
        logging.debug("[LaymanAuthLiferay][authorise] %s"% JSESSIONID)
        if JSESSIONID is None or JSESSIONID == "":
            raise AuthError(401, "Authentication failed: No JSESSIONID given")
        self.JSESSIONID = JSESSIONID
        content = self._getUserInfo(JSESSIONID)
        self._parseUserInfo(content)
        return self.authorised
    
    # Get the user info from Slavek's service
    def _getUserInfo(self,JSESSIONID):

        # Learn URL of Slavek's service
        url = self.config.get("Authorization","url") + JSESSIONID
        logging.debug("[LaymanAuthLiferay][_getUserInfo] Authorisation url: %s"% url)
    
        # Request the authentication
        import httplib2
        h = httplib2.Http()
        header, content = h.request(url, "GET")
        logging.debug("[LaymanAuthLiferay][_getUserInfo] response header: %s"% header)
        logging.debug("[LaymanAuthLiferay][_getUserInfo] response content: %s"% content)

        # TODO: check the header

        # Return the response
        return content

    # Parse the reply from Slavek's service
    # Parsing in separate function makes it testable 
    def _parseUserInfo(self, content):

        # Process the response
        try:
            self.authJson = json.loads(content)
            logging.debug("[LaymanAuthLiferay][_parseUserInfo] Liferay reply succesfully parsed")
        except ValueError,e:
            logging.error("[LaymanAuthLiferay][_parseUserInfo] Cannot parse Liferay reply: '%s'"% content)
            raise AuthError(500, "Cannot parse Liferay response [%s] as JSON:%s"% (content,e)) 

        if self.authJson["resultCode"] == "0":
            self.authorised = True
            logging.info("[LaymanAuthLiferay][_parseUserInfo] Authentication succesfull")
        else:
            logging.error("[LaymanAuthLiferay][_parseUserInfo] Authentication failed: Liferay does not recognise given JSESSIONID")
            raise AuthError(401, "Authentication failed: Liferay does not recognise given JSESSIONID")

    # User/Group configuration methods #

    def getUserName(self):
        if not self.authorised:
            raise AuthError(401,"I am sorry, but you are not authorised")

        if self.authJson["userInfo"] and self.authJson["userInfo"]["screenName"]:
            screenName = self.authJson["userInfo"]["screenName"]
            return screenName
        else: 
            raise AuthError(500, "Cannot determine the user name - Liferay did not provide user's screenName")

    def getFSUserDir(self):
        """Get user working directory. Dirname == screenName from Liferay
        """
        if not self.authorised:
            raise AuthError(401,"I am sorry, but you are not authorised")

        if self.authJson["userInfo"] and self.authJson["userInfo"]["screenName"]:
            fsDir = self.config.get("FileMan","homedir") + self.authJson["userInfo"]["screenName"]
            return fsDir
        else: 
            raise AuthError(500, "Cannot determine the working directory - Liferay did not provide user's screenName")

    def getDBSchema(self, desired=None):
        """ roleName ~ Schema. Uses getRole()
        """
        role = self.getRole(desired)
        schema = role["roleName"]
        return schema
    
    def getGSWorkspace(self, desired=None):
        """ roleName ~ Workspace. Uses getRole()
        """
        role = self.getRole(desired)
        ws = role["roleName"]
        return ws

    def getRole(self, desired=None):
        """ Checks if the user is authorised.
        Checks the roles. 
        If the desired role name is given and it is listed in the user's roles list, the desired role is returned.
        The first role is returned otherwise. 
        Returns json {roleName: "police", roleTitle: "Policie Ceske republiky"}
        """
        logging.debug("[LaymanAuthLiferay][getRole]")
        if not self.authorised:
            logging.error("[LaymanAuthLiferay][getRole] The user is not authorised")
            raise AuthError(401, "I am sorry, but you are not authorised")
        if self.authJson["userInfo"] and self.authJson["userInfo"]["roles"]:
            roles = self.authJson["userInfo"]["roles"]
            if len(roles) < 1:
                logging.error("[LaymanAuthLiferay][getRole] Cannot determine the workspace - Liferay provided empty list of roles")
                raise AuthError(500,"Cannot determine the workspace - Liferay provided empty list of roles")            

            theRole = roles[0]
            for r in roles:
                if desired == r["roleName"]:
                    theRole = r

            #lower
            theRole["roleName"] = theRole["roleName"].lower()
            roleName = theRole["roleName"]
            logging.debug("[LaymanAuthLiferay][getRole] The role: '%s'"% roleName)
            return theRole
        else: 
            logging.error("[LaymanAuthLiferay][getRole] Cannot determine the workspace - Liferay did not provide user's roles")
            raise AuthError(500,"Cannot determine the workspace - Liferay did not provide user's roles")

    def getRoleStr(self, desired=None):
        """ returns string representation of getRole()
        """
        roleJson = self.getRole(desired)
        roleStr = json.dumps(roleJson)
        return (500,roleStr)

    def getRoles(self, filtered=True):
        """ Returns list of roles: 
            [
               {
                   roleTitle: "User",
                   roleName: "User"
               },
               {
                   roleTitle: "pozarnaja",
                   roleName: "hasici"
               } 
           ]
        """
        logging.debug("[LaymanAuthLiferay][getRoles]")

        if not self.authorised:
            logging.error("[LaymanAuthLiferay][getRoles] The user is not authorised")
            raise AuthError(401,"I am sorry, but you are not authorised")

        if self.authJson["userInfo"] and self.authJson["userInfo"]["roles"]:
            roles = self.authJson["userInfo"]["roles"]
            if len(roles) < 1:
                logging.error("[LaymanAuthLiferay][getRoles] Cannot determine the workspace - Liferay provided empty list of roles")
                raise AuthError(500,"Cannot determine the workspace - Liferay provided empty list of roles")            

            # lower()
            for rr in roles:
                rr["roleName"] = rr["roleName"].lower()

            # filter
            if filtered:
                roles = self.filterRoles(roles)

            rolesStr = json.dumps(roles)
            logging.debug("[LaymanAuthLiferay][getRoles] The roles: '%s'"% rolesStr)
            return roles

        else: 
            logging.error("[LaymanAuthLiferay][getRoles] Cannot determine the workspace - Liferay did not provide user's roles")
            raise AuthError(500,"Cannot determine the workspace - Liferay did not provide user's roles")

    def filterRoles(self, roles):        
        """ filter roles based on the ignore list
        """
        # get configuration
        ignore = self.config.get("Authorization", "ignoreroles")
        if ignore is None or ignore == "":
            return roles

        # make list, trim and lower()
        ignorelist = map(lambda g: g.strip().lower(), ignore.split(','))        

        # filter
        newRoles = []
        for r in roles:
            if r["roleName"] in ignorelist:
                continue
            else:       
                newRoles.append(r)
 
        return newRoles

    def getRolesStr(self, filtered=True):
        """ returns string representation of getRoles() json
        """
        rolesJson = self.getRoles(filtered)
        rolesStr = json.dumps(rolesJson)
        return (200, rolesStr)

    def getAllRoles(self, filtered=True):
        """ Returns list of all roles as JSON. We assume this is not secret. """

        # Learn URL of AllRoles service
        url = self.config.get("Authorization","allroles") # http://erra.ccss.cz/g4i-portlet/service/list/roles/en
        logging.debug("[LaymanAuthLiferay][getAllRoles] AllRoles url: %s"% url)
    
        # Request all roles from LifeRay
        import httplib2
        h = httplib2.Http()
        header, content = h.request(url, "GET")
        logging.debug("[LaymanAuthLiferay][getAllRoles] response header: %s"% header)
        logging.debug("[LaymanAuthLiferay][getAllRoles] response content: %s"% content)

        # Parse the response
        try:
            allRolesJson = json.loads(content)
            logging.debug("[LaymanAuthLiferay][getAllRoles] AllRoles reply succesfully parsed")
        except ValueError,e:
            logging.error("[LaymanAuthLiferay][getAllRoles] Cannot parse AllRoles reply: '%s'"% content)
            raise AuthError(500, "Cannot parse GET All Roles response [%s] as JSON:%s"% (content,e)) 
        
        roles = allRolesJson["roles"]

        # lower()
        for rr in roles:
            rr["roleName"] = rr["roleName"].lower()

        # Filter
        if filtered:
            roles = self.filterRoles(roles)

        # Return roles
        logging.debug("[LaymanAuthLiferay][getAllRoles] Return roles: %s"% str(roles))
        return roles

    def getAllRolesStr(self, filtered=True):
        """ Returns list of all roles as string. We assume this is not secret. """
        allRolesJson = self.getAllRoles()
        allRolesStr = json.dumps(allRolesJson)
        return (200, allRolesStr)

    # Service Authorisation Methods #

    def canDelete(self):
        canDelete = False

        roles = self.getRoles()
        for r in roles:
            if r["roleName"] == "lmadmin":
                canDelete = True
                break
        return canDelete

    def canread(self):
        return self._getrights()["canread"] # Just an example!

    def canwrite(self):
        return # TODO


class LaymanAuthHSRS(LaymanAuth):
    pass

class LaymanAuthOpen(LaymanAuth):
    """Open system for authorization
    Everybody can do everything (read/write access without
    authentification/authorization

    NOTE: Do not use, unless you know, what you are doing
    """

    authorised = True

    def canread(self):
        return True 

    def canwrite(self):
        return True

    def canDelete(self):
        return True

    def getUserName(self):
        return "honza"

    def getGSWorkspace(self,desired=None):
        return self.config.get("Authorization","gsworkspace",self.getRole())

    def getRole(self, desired=None):
        """Take rule from configuration value"""
        return {"roleName":"hasici",
                "roleTitle":"Soptici"}

    def getRoles(self):
        """Take rule from configuration value"""
        return [self.getRole(), {"roleName":"policajti", "roleTitle":"Svestky"}]

    def getRolesStr(self):
        """ returns string representation of getRoles() json
        """
        rolesJson = self.getRoles()
        rolesStr = json.dumps(rolesJson)
        return (200,rolesStr)

    def getFSUserDir(self):
        """Get user working directory. Dirname == screenName from Liferay
        """

        return self.config.get("FileMan","homedir") + self.getRole()["roleName"]

    def getDBSchema(self, desired=None):
        return self.config.get("Authorization","role")

    def getAllRoles(self):
        allRoles = self.getRoles()
        allRoles.append({"roleName":"dak","roleTitle":"Dakota"})
        allRoles.append({"roleName":"lak","roleTitle":"Lakota"})
        #print allRoles
        return allRoles

    def getAllRolesStr(self):
        rolesJson = self.getAllRoles()
        rolesStr = json.dumps(rolesJson)
        return (200,rolesStr)

