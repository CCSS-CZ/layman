# Lincese: ...
# authors: Michal, Jachym

# TODO: 
# * License

import os,sys
import ConfigParser
import string
import web

# global variables
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
config = None
__all__ = ["layed","fileman","auth"]

class LayMan:
    """Layer manager server part implementation"""

    request = None

    # LaymanAuth
    # Either LaymanAuthLiferay or LaymanAuthHSRS
    auth = None

    # "liferay" or "hsrs"
    # service = None

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
                fileman
                fileman/<filename> 
        """
        # GET "http://localhost:8080/layman/fileman/"
        if name == "fileman" or name == "fileman/":
            from fileman import FileMan
            fm = FileMan()
            retval = fm.getFiles()
            return retval
        # GET "http://localhost:8080/layman/fileman/file.shp"
        elif len(name) > 8 and name[:7] == "fileman" and name[7] == '/' and string.find(name, '/',8) == -1:
            from fileman import FileMan
            fm = FileMan()
            fileName = name[8:]

            # uncomment once ready
            # dir = self.auth.getFSDir()
            # retval = fm.getFileDetails(fileName, dir)           

            retval = fm.getFileDetails(fileName)
            return retval 
        else:
            web.notfound() # 404
            return "Call not supported. I'm sorry, mate..." 

    def POST(self, name=None):
        # POST "http://localhost:8080/layman/fileman/file.shp"
        if len(name) > 8 and name[:7] == "fileman" and name[7] == '/' and string.find(name,'/',8) == -1:
            from fileman import FileMan
            fm = FileMan()
            fileName = name[8:]
            data = web.data()
            retval = fm.postFile(fileName, data) 
            return retval 
        else:
            web.notfound()
            return "Call not supported. I'm sorry, mate..."

    def PUT(self, name=None):
        # PUT "http://localhost:8080/layman/fileman/file.shp"
        if len(name) > 8 and name[:7] == "fileman" and name[7] == '/' and string.find(name,'/',8) == -1:
            from fileman import FileMan
            fm = FileMan()
            fileName = name[8:]
            data = web.data()
            retval = fm.putFile(fileName, data) 
            return retval
        else:
            web.notfound()
            return "Call not supported. I'm sorry, mate..."

    def DELETE(self, name=None):
        # DELETE "http://localhost:8080/layman/fileman/file.shp"
        if len(name) > 8 and name[:7] == "fileman" and name[7] == '/' and string.find(name,'/',8) == -1:
            from fileman import FileMan
            fm = FileMan()
            fileName = name[8:]
            retval = fm.deleteFile(fileName) 
            return retval 
        else:
            web.notfound()
            return "Call not supported. I'm sorry, mate..."

    #
    # Private methods
    #
    def _setauth(self):
        """Get and set authorization
        """
        service = config.get("Authorization","service")
        # self.service = service

        if service == "liferay":
            from auth import LaymanAuthLiferay
            JSESSIONID = web.cookies().get("JSESSIONID")
            self.auth = LaymanAuthLiferay(JSESSIONID) 
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
