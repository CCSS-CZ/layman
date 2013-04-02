# Lincese: ...
# authors: Michal, Jachym

# TODO: 
# * License

import os,sys
import ConfigParser
import string
import web
import logging

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
                fileman/detail/<filename> 
                fileman/<filename> 
        """
        if not self.auth.authorised:
            self._setReturnCode(401) # Unauthorized 
            return "Authorisation failed. You need to log-in into the Liferay first."    

        retval = None
        code = None

        # GET "http://localhost:8080/layman/fileman/"
        path = [d for d in name.split(os.path.sep) if d]
        if path[0] == "fileman":
            
            from fileman import FileMan
            fm = FileMan()

            # TODO: Where do we check the authorisation?

            # /fileman
            if len(path) == 1:
                logging.info("** LayMan ** GET /fileman **")
                (code, retval) = fm.getFiles(self.auth.getFSDir())

            # /fileman/<file>
            elif len(path) == 2:
                (code, retval) = fm.getFile(self._getTargetFile(path[1]))

            # /fileman/detail/<file>
            elif len(path) == 3 and\
                path[1] == "detail":
                (code, retval) = fm.getFileDetails(self._getTargetFile(path[2]))

        elif path[0] == 'layed':

            from layed import LayEd
            le = LayEd()

            # TODO: Where do we check the authorisation?

            if len(path) == 1:
                # /layed[?group=FireBrigade]
                """ Get the json of the layers.
                If workspace parameter is specified, only the layers 
                of the given workspace are returned. 
                Otherwise, the layers of all groups allowed are returned
                in proprietary json, ordered by group (i.e. workspace)
                """
                logging.info("** LayMan ** GET /layed **")
                inpt = web.input(group=None)
                if inpt.group == None: # workspace not given, go for all
                    groups = self.auth.getRoles()
                else: # workspace given, go for one
                    gsWorkspace = self.auth.getGSWorkspace(inpt.group)
                    groups = [gsWorkspace]
                (code,retval) = le.getLayers(workspaces=groups)

            elif len(path) == 2:               
                # /layed/workspaces
                if path[1] == "workspaces":
                    retval = le.getWorkspaces()
                # /layed/groups
                if path[1] == "groups":
                    retval = self.auth.getRoles()

            elif len(path) == 3:
                # /layed/config/<layer>?group=FireBrigade
                if path[1] == "config":
                    layerName = path[2]
                    inpt = web.input(group=None)
                    gsWorkspace = self.auth.getGSWorkspace(inpt.group)
                    retval = le.getLayerConfig(gsWorkspace, layerName)
                # /layed/workspaces/<ws>
                if path[1] == "workspaces":
                    retval = le.getWorkspace(path[2])

        elif path[0] == "geoserver":
            from layed.gsconfig import GsConfig
            g = GsConfig()
            code = 200

            if path[1] == "style" and len(path) == 3:
                retval = g.getStyle(path[2])
                web.header("Content-type", "text/xml")
            
        # default handler
        else:
            code = 404
            retval = "Call [%s] not supported. I'm sorry, mate..." % name

        self._setReturnCode(code)
        return retval

    def POST(self, name=None):

        global config
        if not self.auth.authorised:
            self._setReturnCode(401) # Unauthorized 
            return "Authorisation failed. You need to log-in into the Liferay first."    

        retval = None
        code = None
        
        name = [d for d in os.path.split(name) if d]

        if len(name) > 0:
            # POST "http://localhost:8080/layman/fileman/file.shp"
            if name[0] == "fileman":
                from fileman import FileMan
                fm = FileMan()
                # Jachyme, what we expect here to receive from the client?
                # Where is it documented?
                inpt = web.input(filename={}, newfilename="")
                newFilename = inpt["newfilename"]
                if not newFilename: 
                    newFilename = inpt["filename"].filename
                newFilename = self._getTargetFile(newFilename,False)
                (code, retval) = fm.postFile(newFilename,inpt["filename"].file.read())  # FIXME Security: we
                                                                 # shoudl read file size up to X megabytes
                web.header("Content-type", "text/html")
                web.ok() # 200
                return retval 
            # POST "http://localhost:8080/layman/layed?fileName=Rivers.shp&group=RescueRangers"
            elif name[0] == "layed":
                from layed import LayEd
                le = LayEd(config)
                inpt = web.input(group=None)
                if not inpt.fileName:
                    pass #TODO - name required
                fileName = inpt.fileName
                fsDir       = self.auth.getFSDir()
                dbSchema    = self.auth.getDBSchema()
                gsWorkspace = self.auth.getGSWorkspace(inpt.group)
                layerName   = le.publish(fsDir, dbSchema, gsWorkspace, fileName)
                return "{success: true, message: 'File [%s] published as layer [%s] published'}" %\
                    (fileName, layerName)
        else:
            self._setReturnCode(404)
            return "Call not supported. I'm sorry, mate..."

    def PUT(self, name=None):

        if not self.auth.authorised:
            self._setReturnCode(401) # Unauthorized 
            return "Authorisation failed. You need to log-in into the Liferay first."    

        retval = None
        code = None

        path = [d for d in name.split(os.path.sep) if d]

        # PUT "http://localhost:8080/layman/fileman/file.shp"
        if path[0]  == "fileman":
            from fileman import FileMan
            fm = FileMan()
            fileName = path[-1]
            data = web.data()
            (code, retval) = fm.putFile(self._getTargetFile(fileName),data)
            self._setReturnCode(code)
            return retval
        elif path[0] == "geoserver":
            from layed.gsconfig import GsConfig
            gs = GsConfig()

            # /geoserver/style/style_name
            if path[1] == "style":
                gs.putStyle(path[2],web.data())
        # /layed/config/<layer>?group=FireBrigade
        elif path[0] == "layed" and len(path) == 3:
            layerName = path[2]
            inpt = web.input(group=None)
            gsWorkspace = self.auth.getGSWorkspace(inpt.group)
            data = web.data()
            retval = le.putLayerConfig(gsWorkspace, layerName, data)
        else:
            web.notfound()
            return "Call not supported. I'm sorry, mate..."

    def DELETE(self, name=None):

        if not self.auth.authorised:
            self._setReturnCode(401) # Unauthorized 
            return "Authorisation failed. You need to log-in into the Liferay first."    

        retval = None
        code = None

        # DELETE "http://localhost:8080/layman/fileman/file.shp"
        path = [d for d in name.split(os.path.sep) if d]
        if len(name) > 0:

            if path[0] == "fileman":
                    from fileman import FileMan
                    fm = FileMan()
                    fileName = name[8:]
                    (code, retval) = fm.deleteFile(self._getTargetFile(path[-1])) 
                    self._setReturnCode(code)
                    return retval 
            # /layed/<layer>?group=FireBrigade
            elif path[0] == "layed" and len(path) == 2:
                layerName = path[1]
                inpt = web.input(group=None)
                gsWorkspace = self.auth.getGSWorkspace(inpt.group)
                retval = le.deleteLayer(gsWorkspace, layerName)
                return retval
            else:
                web.notfound()
                return "{success: false, message: 'File [%s] not found '}" % path[-1]

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

        if service.lower() == "liferay":
            # Get the JSESSIONID from Client's request
            # and create LaymanAuth instance based on that
            from auth import LaymanAuthLiferay
            JSESSIONID = web.cookies().get("JSESSIONID")
            self.auth = LaymanAuthLiferay() 
            self.auth.authorise(JSESSIONID)
        elif service.lower() == "hsrs":
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

    def _getTargetFile(self,fileName,asFile=False):
        """Return desired file absolute path

        :param: fileName file name

        :param: asFile return file object or just string

        :returns: string real path or file object
        """

        targetname = os.path.realpath( os.path.join(
                            self.auth.getFSDir(),fileName)
                    )

        if asFile:
            return open(targetname)
        else:
            return targetname

    def _setReturnCode(self, code):
        """Set be return code

        :param: code
        :type code: integer or string
        """

        if code in (200, "ok"):
            web.ok()
        elif code in (201, "created"):
            web.created()
        elif code in (401, "unauthorized"):
            web.unauthorized()
        elif code in (404, "notfound"):
            web.notfound()
        elif code in (409,"conflict"):
            web.conflict()
        elif code in (500, "internalerror"):
            web.internalerror()
