# License: ....
# authors: Michal, Jachym

# TODO: 
# * Finish LaymanAuthLiferay
# * Finish LaymanAuthHSRS
# * License

import os
import json

class LaymanAuth: 

    config = None
    auth = None

    def __init__(self,config=None):
        self._setConfig(config)

    # Service Authorisation Methods #
    
    def canread(self):
        """Can particular user read from the service?

            :returns: boolean
        """
        return True # NOTE: by default is everything allowed

    def canwrite(self):
        """Can particular user write to the service?

            :returns: boolean
        """
        return True # NOTE: by default is everything allowed


    # User/Group configuration methods #

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
                raise AuthError("Could not create target directory [%s]:%s"%\
                        (dirname, e))

        # check directory permission
        if not os.access(dirname, 7):
            raise AuthError("Write access denied for target directory [%s]"% (dirname))

        return dirname

    def getDBSchema(self):
        pass
    
    def getGSWorkspace(self):
        pass

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
    #           { roleName: "Power User" },
    #           { roleName: "User" },
    #           { roleName: "ukraine_gis" }
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
        self.JSESSIONID = JSESSIONID
        content = self._getUserInfo(JSESSIONID)
        self._parseUserInfo(content)
        return self.authorised
    
    # Get the user info from Slavek's service
    def _getUserInfo(self,JSESSIONID):

        # Learn URL of Slavek's service
        url = self.config.get("Authorization","url") + JSESSIONID
    
        # Request the authentication
        import httplib2
        h = httplib2.Http()
        resp, content = h.request(url, "GET")

        # TODO: Do we want to check the header?

        # Return the response
        return content

    # Parsing in separate function makes it testable 
    def _parseUserInfo(self, content):

        # Process the response
        try:
            self.authJson = json.loads(content)
        except ValueError,e:
            raise AuthError("Cannot parse Liferay response [%s] as JSON:%s"% (content,e)) 

        if self.authJson["resultCode"] == "0":
            self.authorised = True
        else:
            raise AuthError("Authentication failed: Liferay does not recognise given JSESSIONID")

    # User/Group configuration methods #

    def getFSDir(self):
        """Get user working directory. Dirname == screenName from Liferay
        """
        # TODO: Where should we check the self.time ??
        # TODO: Do we want to store the directory in the config file?
        if not self.authorised:
            raise AuthError("I am sorry, but you are not authorised")

        if self.authJson["userInfo"] and self.authJson["userInfo"]["roles"]:
            fsDir = self.config.get("FileMan","homedir") + self.authJson.userInfo.screenName
            # TODO: do some checks
            # TODO: create if it does not exist
            return fsDir
        else: 
            raise AuthError("Cannot determine the working directory - Liferay did not provide user's screenName")

    def getDBSchema(self, desired):
        """ Role ~ Schema. Uses getRole()
        """
        return self.getRole(desired)
    
    def getGSWorkspace(self, desired=None):
        """ Role ~ Workspace. Uses getRole()
        """
        return self.getRole(desired)

    def getRole(self, desired=None):
        """ Checks if the user is authorised.
        Checks the roles. 
        If the desired role is given and it is listed in the user's roles list, the desired role is returned.
        The first role is returned otherwise. 
        """
        if not self.authorised:
            raise AuthError("I am sorry, but you are not authorised")
        if self.authJson["userInfo"] and self.authJson["userInfo"]["roles"]:
            roles = self.authJson["userInfo"]["roles"]
            if len(roles) < 1:
                raise AuthError("Cannot determine the workspace - Liferay provided empty list of roles")            

            theRole = roles[0]["roleName"]
            for r in roles:
                if desired == r["roleName"]:
                    theRole = r["roleName"]

            return theRole
        else: 
            raise AuthError("Cannot determine the workspace - Liferay did not provide user's roles")

    # Service Authorisation Methods #

    def canread(self):
        return self._getrights()["canread"] # Just an example!

    def canwrite(self):
        return # TODO


class LaymanAuthHSRS(LaymanAuth):
    pass

class AuthError(Exception): 
    """Auhorization error class
    """
