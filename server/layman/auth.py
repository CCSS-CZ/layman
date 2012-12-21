# License: ....
# authors: Michal, Jachym

# TODO: 
# * Finish LaymanAuthLiferay
# * Finish LaymanAuthHSRS
# * License

import os

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
        """Returns full abs path to target file manager directory according to
        configuration value and user

        NOTE: this method is to be overwritten according to specified
        Authorization method. This default method returns path to working
        directory, regardless, which user is logged in.

        :returns: path absolute path to target dir
        """
        
        # target dir configuration value
        dirname = os.path.abspath(
                self.config.get("fileman","targetdir")
                )

        # exists or not - create
        if not os.path.isdir(dirname):
            try:
                os.mkdir(dirname)
            except OSError,e:
                return LayMan.AuthError("Could not create target directory [%s]:%s"%\
                        (dirname, e))

        # check directory permission
        if os.access(dirname, 7):
            LayMan.AuthError("Write access denied for target directory [%s]"% (dirname))

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
