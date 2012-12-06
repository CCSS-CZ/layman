# Lincese: ...
# authors: Michal, Jachym

# TODO: 
# * License

import os,sys
import ConfigParser

# global variables
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
config = None
__all__ = ["layed","fileman","auth"]

class LayMan:
    """Layer manager server part implementation"""

    request = None

    def __init__(self):
        """Constructor
        """

        self._setconfiguration()
        self._setauth()

    #
    # REST methods
    #
    def GET(self,name=None):
        """Dispatch client request
           Supported calls:
                fileman/getfiles.json
                fileman/getfiledetails.json 
        """
        # GET "http://localhost:8080/layman/fileman/"
        if name == "fileman" or name == "fileman/":
            from fileman import FileMan
            fm = FileMan()
            retval = fm.getFiles()
            return retval
        # GET "http://localhost:8080/layman/fileman/file.shp"
        elif name == "fileman/getfiledetails.json": # TODO: should be "fileman/file.shp", split the string and check it
            from fileman import FileMan
            fm = FileMan()
            retval = fm.getFileDetails("filename")
            return retval
        else:
            return "Call not supported. I'm sorry, mate..."

    def POST(self, name=None):
        return "Hallo world! POST"
        pass

    def PUT(self, name=None):
        return "Hallo world! PUT"
        pass

    def DELETE(self, name=None):
        return "Hallo world! DELETE"
        pass

    #
    # Private methods
    #
    def _setauth(self):
        """Get and set authorization
        """
        service = config.get("Authorization","service")

        if service == "liferay":
            from auth import LaymanAuthLiferay
            self.auth = LaymanAuthLiferay()
        elif service == "hsrs":
            from auth import LaymanAuthHSRS
            self.auth = LaymanAuthHSRS()
        # NOTE: everybody can do anything by default
        # should be probabely fixed in the future
        else:
            from auth import LaymanAuth
            self.auth = LaymanAuth()

    def _setconfiguration(self):
        """Get configuration files"""

        cfgfiles = None
        global INSTALL_DIR
        global config

        # get configuration files

        # from environment variable
        if os.getenv("LAYMAN_CFG"):
            cfgfiles = (os.getenv("LAYMAN_CFG"))

        # Windows or Unix
        else:
            if sys.platform == 'win32':
                cfgfiles = (os.path.join(INSTALL_DIR, "layman.cfg"))
            else:
                homePath = os.getenv("HOME")
                if homePath:
                    cfgfiles = (os.path.join(INSTALL_DIR, "layman.cfg"),
                                "/etc/layman.cfg",
                                os.path.join(os.getenv("HOME"),".layman.cfg" ))
                else: 
                    cfgfiles = (os.path.join(INSTALL_DIR,"layman.cfg"), "/etc/pywps.cfg")
            
        config = ConfigParser.SafeConfigParser()
        config.readfp(open(os.path.join(INSTALL_DIR,"defaults.cfg")))
        config.read(cfgfiles)
