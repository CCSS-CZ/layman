# License: ....
# authors: Michal, Jachym

# TODO: 
# * Finish LaymanAuthLiferay
# * Finish LaymanAuthHSRS
# * License

class LaymanAuth: 

    config = None
    auth = None

    # User info
    uname = None
    ugroup = None
    validityTime = None
    # passwd = None

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
        pass

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

    def __init__(self,JSESSIONID=None):
        self.JSESSIONID = JSESSIONID
        self._getUserInfo()
    
    # Get the user info from Slavek's service
    # JSESSIONID => name, group, time, maybe passwd
    def _getUserInfo():
        pass # TODO

    # ???
    def _getrights(self):
        """Download user rights from given service based on JSESSIONID
        """

        url = self.config.get("authorization","url")
        # ... TODO
        

    # User/Group configuration methods #

    def getFSDir(self):
        pass #TODO: get the dir from the users configfile

    def getDBSchema(self):
        pass #TODO: get the schema from users configfile
    
    def getGSWorkspace(self):
        pass #TODO: get the ws from the users configfile


    # Service Authorisation Methods #

    def canread(self):
        return self._getrights()["canread"] # Just an example!

    def canwrite(self):
        return # TODO


class LaymanAuthHSRS(LaymanAuth):
    pass
