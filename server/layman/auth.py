# License: ....
# authors: Michal, Jachym

# TODO: 
# * Finish LaymanAuthLiferay
# * Finish LaymanAuthHSRS
# * License

class LaymanAuth: 

    config = None
    auth = None

    def __init__(self,config=None):
        self._setConfig(config)
    
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

    def _setConfig(self,config):
        """Get and set configuration files parser
        """
        if config:
            self.config = config
        else:
            from layman import config
            self.config =  config

class LaymanAuthLiferay(LaymanAuth):

    def _getrights(self):
        """Download user rights from given service based on JSESSIONID
        """

        url = self.config.get("authorization","url")
        # ... TODO
        
    def canread(self):
        return self._getrights()["canread"] # Just an example!

    def canwrite(self):
        return # TODO

class LaymanAuthHSRS(LaymanAuth):
    pass
