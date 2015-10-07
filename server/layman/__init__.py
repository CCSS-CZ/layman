# Lincese: ...
# authors: Michal, Jachym

# TODO:
# * License

import os
import sys
import ConfigParser
import web
import logging
import json
import traceback

from errors import LaymanError, AuthError

# global variables
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
config = None
__all__ = ["layed", "fileman", "auth"]


class LayMan:
    """Layer manager server part implementation"""

    request = None

    # LaymanAuth
    # Either LaymanAuthLiferay or LaymanAuthHSRS
    auth = None

    def __init__(self):
        """Constructor
        """
        try:
            self._setconfiguration()
            self._setauth()

        except LaymanError as le:
            return self._handleLaymanError(le)

        except Exception as e:
            return self._handleException(e)


    #
    # REST methods
    #

    def GET(self, name=None):

        try:
                logging.info("[LayMan][GET] %s" % name)
                params = repr(web.input())
                logging.info("[LayMan][GET] Parameters: %s ... %s" %
                    (str(params)[:500], str(params)[-500:]))

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

                elif path[0] == 'publish':
                    
                    from layed import LayEd
                    le = LayEd()

                    roles = self.auth.getRoles()
                    userName = self.auth.getUserName()
                    (code,retval) = le.getLayers(roles, userName)

                # Get the list of tables in db (or other data)
                elif path[0] == 'data':
                
                    # /data    
                    if len(path) == 1:
                        from layed import LayEd
                        le = LayEd()

                        userName = self.auth.getUserName()
                        roles = self.auth.getRoles()
                        (code,retval) = le.getData(roles, userName)

                    elif len(path) == 2:

                        # /layed/groups
                        if path[1] == "groups":
                            (code, retval) = self.auth.getRolesStr()

                        # /layed/allgroups
                        elif path[1] == "allgroups":
                            (code, retval) = self.auth.getAllRolesStr()

                        else:
                            (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                # Get the list of ckan packages
                elif path[0] == 'ckan':

                    # /ckan
                    if len(path) == 1:
                        from layed import LayEd
                        le = LayEd()

                        userName = self.auth.getUserName()
                        roles = self.auth.getRoles()
                        (code,retval) = le.getCkanPackages(roles, userName, limit="20", offset="0") # TODO - get CKAN limit from client

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
                        userName = self.auth.getUserName()
                        (code,retval) = le.getLayers(roles, userName)

                    elif len(path) == 2:

                        # /layed/workspaces
                        if path[1] == "workspaces":
                            (code, retval) = le.getWorkspaces()

                        # /layed/groups
                        elif path[1] == "groups":
                            (code, retval) = self.auth.getRolesStr()

                        # /layed/allgroups
                        elif path[1] == "allgroups":
                            (code, retval) = self.auth.getAllRolesStr()

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
                        #if len(path) > 3:
                        #    ws = path[-2]
                        g = GsConfig()
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
                logging.info("[LayMan][POST] Parameters: %s ... %s"%\
                        (str(params)[:500], str(params)[-500:]))

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

                        # Request params
                        inpt = web.input(filename={}, newfilename="")

                        # Chek 'source' parameter ['url'|'payload']
                        if "source" in inpt and inpt["source"].lower() == "url":    
                            # Check URL param
                            if not inpt["url"] or inpt["url"] == "":
                                # Get from url requested, but url not given
                                code = 400
                                message = "URL source requested, but URL not given"
                            else:
                                # Get file from URL 
                                (code, message) = fm.postFileFromUrl(inpt["url"])
                        else:
                            # Get file data from request payload
                            newFilename = inpt["newfilename"]
                            if not newFilename:
                                newFilename = inpt["filename"].filename
                            newFilename = self._getTargetFile(newFilename,False)
                            (code, message) = fm.postFile(newFilename, inpt["filename"].file.read())  # FIXME Security: we
                                                                                 # shoudl read file size up to X megabytes
                   
                        web.header("Content-type", "text/html")

                    # POST /layman/user
                    # data: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
                    elif name[0] == "user":
                        from userprefs import UserPrefs
                        up = UserPrefs(config)
                        data = web.data()
                        logging.debug(data)
                        (code, message) = up.createUser(userJsonStr=data)

                    # POST "http://localhost:8080/layman/layed?fileName=Rivers.shp&usergroup=RescueRangers"
                    elif name[0] == "layed":
                        from layed import LayEd
                        le = LayEd(config)
                        inpt = web.input(usergroup=None)
                        if not inpt.fileName:
                            raise LaymanError(
                                400, "'fileName' parameter missing")
                        fileName = inpt.fileName
                        userName = self.auth.getUserName()
                        fsUserDir = self.auth.getFSUserDir()
                        fsGroupDir = self.auth.getFSGroupDir(inpt.usergroup)
                        dbSchema = self.auth.getDBSchema(inpt.usergroup)
                        gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                        crs = inpt.crs # native crs
                        tsrs = inpt.tsrs # target srs
                        cpg = inpt.cpg # code page

                        secureLayer = False
                        if "secureLayer" in inpt:
                            if inpt.secureLayer.lower() == "true":
                                secureLayer = True

                        (code, layerName, message) = le.importAndPublish(fsUserDir, fsGroupDir,
                                                     dbSchema, gsWorkspace,
                                                     fileName, userName, crs, tsrs, cpg, inpt, secureLayer)
                        # Set Location header
                        if code == 201 and layerName is not None:
                            location = layerName # TODO: provide full URI here             
                            web.header("Location", location)

                    elif name[0] == "publish" or name[0] == "data":
                        from layed import LayEd
                        le = LayEd(config)
                        inpt = web.input()

                        # Obligatory parameters
                        if not "schema" in inpt:
                            raise LaymanError(
                                400, "'schema' parameter missing")
                        if not "view" in inpt:
                            raise LaymanError(
                                400, "'view' parameter missing")
                        if not "crs" in inpt:
                            raise LaymanError(
                                400, "'crs' parameter missing")

                        viewName = inpt.view
                        userName = self.auth.getUserName()
                        dbSchema = self.auth.getDBSchema(inpt.schema)
                        gsWorkspace = self.auth.getGSWorkspace(inpt.schema)
                        crs = inpt.crs

                        secureLayer = False
                        if "secureLayer" in inpt:
                            if inpt.secureLayer.lower() == "true":
                                secureLayer = True

                        # Optional parameters
                        styleName = None
                        styleWs = None                        
                        if "style" in inpt:
                            styleName = inpt.style
                        if "style_ws" in inpt:
                            styleWs = inpt.style_ws

                        (code, layerName, message) = le.publishFromDbToGs(dbSchema, 
                                                            viewName, gsWorkspace, userName,
                                                            crs, inpt, styleName, styleWs, secureLayer)

                        # Set Location header
                        if code == 201 and layerName is not None:
                            location = layerName # TODO: provide full URI here             
                            web.header("Location", location)

                    else:
                        (code, message) = self._callNotSupported(restMethod="POST",
                                                                 call=origName)

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

        try:
                logging.info("[LayMan][PUT] %s"% name)
                params = repr(web.input())
                logging.info("[LayMan][PUT] Parameters: %s ... %s"%\
                        (str(params)[:500], str(params)[-500:]))

                global config
                if not self.auth.authorised:
                    logging.error("[LayMan][PUT] Unauthorised")
                    raise AuthError(401, "Authorisation failed. Are you logged-in?")

                code = 404    # 200, 404...
                message = "Call not supported: PUT "+name+" Please check the API doc or report a bug if appropriate."

                path = [d for d in name.split(os.path.sep) if d]

                # PUT "http://localhost:8080/layman/fileman/file.shp"
                if path[0]  == "fileman":
                    from fileman import FileMan
                    fm = FileMan()
                    fileName = path[-1]
                    data = web.data()
                    (code, message) = fm.putFile(self._getTargetFile(
                                                 fileName), data)

                # PUT /layman/user/
                # data: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
                elif path[0] == "user":
                    from userprefs import UserPrefs
                    up = UserPrefs(config)
                    data = web.data()
                    logging.debug(data)
                    (code, message) = up.updateUser(userJsonStr=data)

                elif path[0] == "geoserver":
                    from layed.gsconfig import GsConfig

                    # /geoserver/style/style_name
                    if path[1] == "style":
                        #ws = None
                        #if len(path) > 3:
                        #    ws = path[-2]
                        gsc = GsConfig()
                        # If PUT Style fails, gsconfig throws an exception
                        try:
                            gsc.putStyle(path[-1], web.data())
                            (code, message) = (200, "PUT Style OK")
                        except Exception as e:
                            code = 500
                            message = "PUT Style failed: " + str(e)

                # /layed/config/<layer>?usergroup=FireBrigade
                elif path[0] == "layed" and len(path) == 2:
                    from layed import LayEd
                    le = LayEd()
                    layerName = path[1]
                    inpt = web.input(usergroup=None)
                    gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                    data = web.data()
                    data = json.loads(data)  # string -> json

                    usergroup = inpt.usergroup
                    if (not usergroup) and ("usergroup" in data.keys()):
                        logging.debug("[LayMan][PUT] Usergroup not provided in params, but given in data: %s"% data["usergroup"])
                        usergroup = data["usergroup"]

                    fsUserDir = self.auth.getFSUserDir()
                    fsGroupDir = self.auth.getFSGroupDir(usergroup)
                    dbSchema = self.auth.getDBSchema(usergroup)
                    gsWorkspace = self.auth.getGSWorkspace(usergroup)

                    (code, message) = le.putLayerConfig(gsWorkspace,
                                                        layerName, data,
                                                        fsUserDir, fsGroupDir,
                                                        dbSchema)

                success = self._setReturnCode(code)
                retval = self._jsonReply(code, message, success)
                return retval

        except LaymanError as le:
            return self._handleLaymanError(le)

        except Exception as e:
            return self._handleException(e)

    def DELETE(self, name=None):

        try:
                logging.info("[LayMan][DELETE] %s"% name)
                params = repr(web.input())
                logging.info("[LayMan][DELETE] Parameters: %s ... %s"%\
                        (str(params)[:500], str(params)[-500:]))

                if not self.auth.authorised:
                    logging.error("[LayMan][DELETE] Unauthorised")
                    raise AuthError(401, "Authorisation failed. Are you logged-in?")

                code = 404    # 200, 404...
                message = "Call not supported: DELETE "+name+" Please check the API doc or report a bug if appropriate."

                path = [d for d in name.split(os.path.sep) if d]
                if len(name) > 0:

                    # Uncomment to check delete rights
                    # TODO: Check delete rights based on the ownership further on, 
                    # where the owner of the resource is known
                    # 
                    #if path[0] != "fileman" and not self.auth.canDelete():
                    #        logging.error("[LayMan][DELETE] Only admin can DELETE")
                    #        raise AuthError(401, "Authorisation failed. Only Administrator can delete")

                    # /fileman/file.shp"
                    if path[0] == "fileman":
                            from fileman import FileMan
                            fm = FileMan()
                            fileName = name[8:]
                            (code, message) = fm.deleteFile(self._getTargetFile(path[-1]))

                    # /user/<username>
                    elif path[0] == "user" and len(path) == 2:
                        userName = path[1]
                        from userprefs import UserPrefs
                        up = UserPrefs(config)
                        (code, message) = up.deleteUser(userName)

                    # /layed/<layer>
                    elif path[0] == "layed" and len(path) == 2:
                        from layed import LayEd
                        le = LayEd()
                        layerName = path[1]
                        inpt = web.input(usergroup=None)
                        
                        deleteTable = True
                        if "deleteTable" in inpt:
                            if inpt["deleteTable"].lower() == "false":
                                deleteTable = False
                        
                        gsWorkspace = self.auth.getGSWorkspace(inpt.usergroup)
                        dbSchema    = self.auth.getDBSchema(inpt.usergroup)
                        logging.info("[LayMan][DELETE] Delete layer '%s'"% layerName )
                        logging.info("[LayMan][DELETE] Delete from workspace '%s'"% gsWorkspace)
                        (code, message) = le.deleteLayer(gsWorkspace, layerName, dbSchema, deleteTable)

                    # /publish/<layer>
                    elif path[0] == "publish" and len(path) == 2:
                        from layed import LayEd
                        le = LayEd()
                        layerName = path[1]
                        inpt = web.input()
                        if not "schema" in inpt:
                            raise LaymanError(
                                400, "'schema' parameter missing")

                        gsWorkspace = self.auth.getGSWorkspace(inpt.schema)
                        dbSchema    = self.auth.getDBSchema(inpt.schema)
                        logging.info("[LayMan][DELETE] Delete layer '%s'"% layerName )
                        logging.info("[LayMan][DELETE] Delete from workspace '%s'"% gsWorkspace)
                        (code, message) = le.deleteLayer(gsWorkspace, layerName, dbSchema, deleteTable=False)

                success = self._setReturnCode(code)
                retval  = self._jsonReply(code, message, success)
                return retval

        except LaymanError as le:
            return self._handleLaymanError(le)

        except Exception as e:
            return self._handleException(e)

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
            self.auth = LaymanAuthLiferay(config)
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

        if success:
            logging.debug("[LayMan][_setReturnCode] Code: '%s'" % code)
        else:
            logging.error("[LayMan][_setReturnCode] Code: '%s'" % code)

        return success

    def _jsonReply(self, code, message, success):

        jsonReply = {}
        jsonReply["success"] = success
        jsonReply["message"] = message
        retval = json.dumps(jsonReply)
        if success:
            logging.debug("[LayMan][_jsonReply] Reply with: '%s'" % retval)
        else:
            logging.error("[LayMan][_jsonReply] Reply with: '%s'" % retval)
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

