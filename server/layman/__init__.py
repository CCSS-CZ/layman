# Lincese: ...
# authors: Michal, Jachym

# TODO: 
# * License

import os,sys
import ConfigParser
import string
import web
import logging
import json
import traceback

from errors import LaymanError, AuthError

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

        try:
                logging.info("[LayMan][GET] %s"% name)
                params = repr(web.input())
                logging.info("[LayMan][GET] Parameters: %s"% params)
                
                if not self.auth.authorised:
                    logging.error("[LayMan][GET] Unauthorised")
                    raise AuthError(401, "Authorisation failed. Are you logged-in?")

                code = None    # 200, 404...         
                retval = None  # success: returned value. failure: error message.
                origName = name
                path = [d for d in name.split(os.path.sep) if d]

                # GET "http://localhost:8080/layman/fileman/"
                if path[0] == "fileman":
                    
                    from fileman import FileMan
                    fm = FileMan()

                    # /fileman
                    if len(path) == 1:
                        logging.info("[LayMan][GET /fileman]")
                        (code, retval) = fm.getFiles(self.auth.getFSUserDir())

                    # /fileman/<file>
                    elif len(path) == 2:
                        (code, retval) = fm.getFile(self._getTargetFile(path[1]))

                    # /fileman/detail/<file>
                    elif len(path) == 3 and\
                        path[1] == "detail":
                        (code, retval) = fm.getFileDetails(self._getTargetFile(path[2]))

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                elif path[0] == 'layed':

                    from layed import LayEd
                    le = LayEd()

                    # /layed[?usergroup=FireBrigade]
                    if len(path) == 1:
                        """ Get the json of the layers.
                        If usergroup parameter is specified, only the layers 
                        of the corresponding workspace are returned. 
                        Otherwise, the layers of all groups allowed are returned
                        in proprietary json, ordered by group (i.e. workspace)
                        """
                        logging.info("[LayMan][GET /layed]")
                        inpt = web.input(usergroup=None)
                        if inpt.usergroup == None: # workspace not given, go for all
                            roles = self.auth.getRoles()
                        else: # workspace given, go for one
                            role = self.auth.getRole(inpt.usergroup)
                            roles = [role]
                        (code,retval) = le.getLayers(roles)

                    elif len(path) == 2:               

                        # /layed/workspaces
                        if path[1] == "workspaces":
                            (code, retval) = le.getWorkspaces()

                        # /layed/groups
                        elif path[1] == "groups":
                            (code, retval) = self.auth.getRolesStr()

                        else:
                            (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                    elif len(path) == 3:

                        # /layed/config/<layer>?usergroup=FireBrigade
                        if path[1] == "config":
                            layerName = path[2]
                            inpt = web.input(usergroup=None)
                            gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                            (code, retval) = le.getLayerConfig(gsWorkspace, layerName)

                        # /layed/workspaces/<ws>
                        elif path[1] == "workspaces":
                            (code, retval) = le.getWorkspace(path[2])

                        else:
                            (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                elif path[0] == "geoserver":
                    ws = None
                    g = None

                    from layed.gsconfig import GsConfig
                    code = 200

                    if path[1] == "style" and len(path) >= 3:
                        if len(path) > 3:
                            ws = path[-2]
                        g = GsConfig(ws = ws)
                        retval = g.getStyle(path[-1])                
                        web.header("Content-type", "text/xml")
                    
                else:
                    (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                success = self._setReturnCode(code)
                if not success: 
                    retval  = self._jsonReply(code, message=retval, success=success)
                # else: we return the returned value directly
                return retval

        except LaymanError as le:
            return self._handleLaymanError(le)

        except Exception as e:
            return self._handleException(e)

    def POST(self, name=None):

        try:
                logging.info("[LayMan][POST] %s"% name)
                params = repr(web.input())
                logging.info("[LayMan][POST] Parameters: %s"% params)
                
                global config
                if not self.auth.authorised:
                    logging.error("[LayMan][POST] Unauthorised")
                    raise AuthError(401, "Authorisation failed. Are you logged-in?")

                code = None             
                message = None
                origName = name
                name = [d for d in os.path.split(origName) if d]

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
                        (code, message) = fm.postFile(newFilename, inpt["filename"].file.read())  # FIXME Security: we
                                                                         # shoudl read file size up to X megabytes
                        web.header("Content-type", "text/html")

                    # POST "http://localhost:8080/layman/layed?fileName=Rivers.shp&usergroup=RescueRangers"
                    elif name[0] == "layed":
                        from layed import LayEd
                        le = LayEd(config)
                        inpt = web.input(usergroup=None)
                        if not inpt.fileName:
                            raise LaymanError(400, "'fileName' parameter missing")
                        fileName    = inpt.fileName
                        fsUserDir   = self.auth.getFSUserDir()
                        fsGroupDir  = self.auth.getFSGroupDir(inpt.usergroup)
                        dbSchema    = self.auth.getDBSchema(inpt.usergroup)
                        gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                        (code, message) = le.publish(fsUserDir, fsGroupDir, dbSchema, gsWorkspace, fileName)
                        #retval = "{success: true, message: 'File "+fileName+" published as layer "+layerName+"'}" 

                else:
                    (code, message) = self._callNotSupported(restMethod="POST", call=origName)

                success = self._setReturnCode(code) 
                retval  = self._jsonReply(code, message, success)
                return retval

        except LaymanError as le:
            return self._handleLaymanError(le)

        except Exception as e:
            return self._handleException(e)

    def PUT(self, name=None):

        logging.info("[LayMan][PUT] %s"% name)
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
                # gs.putStyle(path[2],web.data())
                ws = None
                if len(path) > 3:
                    ws = path[-2]
                gs = GsConfig(ws = ws)
                gs.putStyle(path[-1],web.data())

        # /layed/config/<layer>?usergroup=FireBrigade
        elif path[0] == "layed" and len(path) == 2:
            from layed import LayEd
            le = LayEd()
            layerName = path[1]
            inpt = web.input(usergroup=None)
            gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
            data = web.data()
            retval = le.putLayerConfig(gsWorkspace, layerName, data)

        else:
            web.notfound()
            return "Call not supported. I'm sorry, mate..."

    def DELETE(self, name=None):

        logging.info("[LayMan][DELETE] %s"% name)
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

            # /layed/<layer>?usergroup=FireBrigade
            elif path[0] == "layed" and len(path) == 2:
                logging.info("[LayMan][DELETE /layed/<layer>]")
                from layed import LayEd
                le = LayEd()
                layerName = path[1]
                inpt = web.input(usergroup=None)
                gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                dbSchema    = self.auth.getDBSchema(inpt.usergroup)
                logging.info("[LayMan]Delete layer '%s'"% layerName )
                logging.info("[LayMan]Delete from workspace '%s'"% gsWorkspace)
                retval = le.deleteLayer(gsWorkspace, layerName, dbSchema)
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
        elif service.lower() == "open":
            from auth import LaymanAuthOpen
            self.auth = LaymanAuthOpen()
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
                            self.auth.getFSUserDir(),fileName)
                    )

        if asFile:
            return open(targetname)
        else:
            return targetname

    def _callNotSupported(self, restMethod, call):
        logMes = "[LayMan]["+restMethod+"] Call not supported: " + call
        logging.error(logMes)
        code = 404
        retval = "Call not supported. Please check the API doc or report a bug if appropriate."
        return (code, retval)

    def _setReturnCode(self, code):
        """Set the return code

        :param: code
        :type code: integer or string
        returns success: [True|False] 
        """
        success = False

        if code in (200, "200", "ok"):
            web.ok()
            success = True
        elif code in (201, "201", "created"):
            web.created()
            success = True
        elif code in (400, "400", "badrequest"):
            web.badrequest()
        elif code in (401, "401", "unauthorized"):
            web.unauthorized()
        elif code in (404, "404", "notfound"):
            web.notfound()
        elif code in (409, "409", "conflict"):
            web.conflict()
        elif code in (500, "500", "internalerror"):
            web.internalerror()

        return success

    def _jsonReply(self, code, message, success):

        jsonReply = {}
        jsonReply["success"] = success
        jsonReply["message"] = message
        retval = json.dumps(jsonReply)
        return retval

    def _handleLaymanError(self, laymanErr):
        """ Handle LaymanError exception
        """
        tb = traceback.format_exc()
        logging.debug(tb)

        message = str(laymanErr)
        logging.error("[LayMan][_handleLaymanError] Layman Error exception: '%s'"% message)
        success = self._setReturnCode(laymanErr.code)    
        retval = self._jsonReply(laymanErr.code, message, success)
        return retval

    def _handleException(self, ex):
        """ Handle unexpected Exception
        """
        tb = traceback.format_exc()
        logging.debug(tb)

        message = str(ex)
        logging.error("[LayMan][_handleException] Unexpected exception: '%s'"% message)
        self._setReturnCode(500)    
        retval = self._jsonReply(500, message, success=False)
        return retval

