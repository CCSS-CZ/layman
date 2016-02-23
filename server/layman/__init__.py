#
#    LayMan - the Layer Manager
#
#    Copyright (C) 2016 Czech Centre for Science and Society
#    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
#    Mailto: sredl@ccss.cz, charvat@ccss.cz
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

                # GET "http://localhost:8080/layman/files/<user>"
                if path[0] == "files" and len(path) >= 2:

                    from fileman import FileMan
                    fm = FileMan()

                    # Everyone can get only his/her own files 
                    userName = self.auth.getUserName()
                    if userName != path[1]:
                        logging.error("[LayMan][GET] %s is not authorized to get files of %s"% (userName, path[1]))
                        raise AuthError(401, "Sorry, you are not authorized to get files of %s"% path[1])

                    #     /files/<user>
                    # was /fileman
                    if len(path) == 2:
                        (code, retval) = fm.getFiles(self.auth.getFSUserDir())

                    #     /files/<user>/<file>
                    # was /fileman/<file> 
                    elif len(path) == 3:
                        (code, retval) = fm.getFile(self._getTargetFile(path[2]))

                    #     /files/<user>/<file>/details
                    # was /fileman/detail/<file>
                    elif len(path) == 4 and\
                        path[3] == "details":
                        (code, retval) = fm.getFileDetails(self._getTargetFile(path[2]))

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                # Get the list of tables in db (or other data)
                elif path[0] == 'data':
                
                    # /data    
                    if len(path) == 1:
                        from layed import LayEd
                        le = LayEd()

                        userName = self.auth.getUserName()
                        roles = self.auth.getRoles()
                        (code,retval) = le.getData(roles, userName)

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                # /sync
                elif path[0] == "sync" and len(path) == 2:

                    # /sync/data
                    if path[1] == "data":
                        from layed import LayEd
                        le = LayEd()    
                        roles = self.auth.getRoles()
                        (code, retval) = le.syncDataPad(roles)

                    # /sync/layers
                    elif path[1] == "layers":
                        from layed import LayEd
                        le = LayEd()
                        roles = self.auth.getRoles()
                        (code, retval) = le.syncLayerPad(roles)

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                # /groups
                elif path[0] == "groups" and len(path) == 2:
                        # /groups/mine
                        if path[1] == "mine":
                            (code, retval) = self.auth.getRolesStr()

                        # /groups/all
                        elif path[1] == "all":
                            (code, retval) = self.auth.getAllRolesStr()

                        else:
                            (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                # Get the list of ckan packages
                elif path[0] == 'ckan':

                    # /ckan
                    if len(path) == 1:
                        from layed import LayEd
                        le = LayEd()

                        inpt = web.input(limit="20", start="0", ckanUrl=None)
                        userName = self.auth.getUserName()
                        roles = self.auth.getRoles()

                        (code,retval) = le.getCkanResources(inpt.limit, inpt.start, inpt.ckanUrl) 
                        #(code,retval) = le.getCkanPackages(roles, userName, inpt.limit, inpt.start, inpt.ckanUrl) 

                    else:
                        (code, retval) = self._callNotSupported(restMethod="GET", call=origName)

                elif path[0] == 'layers':

                    from layed import LayEd
                    le = LayEd()

                    #     /layers
                    # was /layed[?usergroup=FireBrigade]
                    if len(path) == 1:
                        """ Get the json of the layers.
                        The layers of all groups allowed are returned
                        in json, ordered by group (i.e. workspace)
                        """
                        roles = self.auth.getRoles()
                        userName = self.auth.getUserName()
                        (code,retval) = le.getLayers(roles, userName)

                    #     /layers/<group>
                    # was /layed[?usergroup=FireBrigade]
                    elif len(path) == 2:
                        role = self.auth.getRole(path[1])
                        if role != path[1]:
                            logging.error("[LayMan][GET] Not authorized to get layers of %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to get the layers of %s group"% path[1])
                        roles = [role]
                        userName = self.auth.getUserName()
                        (code,retval) = le.getLayers(roles, userName)

                    #     /layers/<group>/<layer>
                    # was /layed/config/<layer>?usergroup=FireBrigade
                    elif len(path) == 3:
                        gsWorkspace = self.auth.getGSWorkspace(path[1])
                        if gsWorkspace != path[1]:
                            logging.error("[LayMan][GET] Not authorized to get layer of %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to get the details of a layer from the %s group"% path[1])
                        layerName = path[2]
                        (code, retval) = le.getLayerDetails(gsWorkspace, layerName)

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
                path = [d for d in os.path.split(origName) if d]

                if len(path) > 0:

                    # POST "http://localhost:8080/layman/files/<user>"
                    if path[0] == "files" and len(path) == 2:
                        from fileman import FileMan
                        fm = FileMan()

                        # Everyone can post only in his/her own directory
                        userName = self.auth.getUserName()
                        if userName != path[1]:
                            logging.error("[LayMan][POST] %s is not authorized to post files into %s's directory"% (userName, path[1]))
                            raise AuthError(401, "Sorry, you are not authorized to post files into %s's directory"% path[1])

                        # Request params
                        inpt = web.input(filename={}, newfilename="")
                        
                        # User dir
                        fsUserDir = self.auth.getFSUserDir()

                        # Chek 'source' parameter ['url'|'payload']
                        if "source" in inpt and inpt["source"].lower() == "url":    
                            # Check URL param
                            if not inpt["url"] or inpt["url"] == "":
                                # Get from url requested, but url not given
                                code = 400
                                message = "URL source requested, but URL not given"
                            else:
                                # Get file from URL 
                                (code, message) = fm.postFileFromUrl(fsUserDir, inpt["url"])
                        else:
                            # Get file data from request payload
                            newFilename = inpt["newfilename"]
                            if not newFilename:
                                newFilename = inpt["filename"].filename
                            (code, message) = fm.postFileFromPayload(fsUserDir, newFilename, inpt["filename"].file.read()) 
                   
                        web.header("Content-type", "text/html")

                    # POST /layman/user
                    # data: {screenName: "user", roles: [{roleTitle, roleName}, {roleTitle, roleName}]}
                    elif path[0] == "user":
                        from userprefs import UserPrefs
                        up = UserPrefs(config)
                        data = web.data()
                        logging.debug(data)
                        (code, message) = up.createUser(userJsonStr=data)

                    #     /datalayers/<group>?fileName=Rivers.shp
                    # was /layed?fileName=Rivers.shp&usergroup=RescueRangers"
                    elif path[0] == "datalayers" and len(path) == 2:
                        from layed import LayEd
                        le = LayEd(config)

                        inpt = web.input()

                        if not inpt.fileName:
                            raise LaymanError(
                                400, "'fileName' parameter missing")

                        checkRole = self.auth.getRole(path[1])
                        logging.debug("[LayMan][POST] checkRole: '%s', path[1]: '%s'"% (checkRole, path[1]))
                        if checkRole["roleName"] != path[1]:
                            logging.error("[LayMan][POST] Not authorized to post files into %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to post files into %s group"% path[1])

                        fileName = inpt.fileName
                        userName = self.auth.getUserName()
                        fsUserDir = self.auth.getFSUserDir()
                        fsGroupDir = self.auth.getFSGroupDir(path[1])
                        dbSchema = self.auth.getDBSchema(path[1])
                        gsWorkspace = self.auth.getGSWorkspace(path[1])
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

                    #      /layers/<group>
                    # was: /publish or /data
                    elif path[0] == "layers" and len(path) == 2:
                        from layed import LayEd
                        le = LayEd(config)
                        inpt = web.input()

                        # Check authorization
                        checkRole = self.auth.getRole(path[1])
                        if checkRole["roleName"] != path[1]:
                            logging.error("[LayMan][POST] Not authorized to post files into %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to post files into %s group"% path[1])

                        # Obligatory parameters
                        if not "dataname" in inpt:
                            raise LaymanError(
                                400, "'dataname' parameter missing")
                        if not "datatype" in inpt:
                            raise LaymanError(
                                400, "'datatype' parameter missing")
                        if not "crs" in inpt:
                            raise LaymanError(
                                400, "'crs' parameter missing")

                        dataName = inpt.dataname
                        dataType = inpt.datatype
                        userName = self.auth.getUserName()
                        dbSchema = self.auth.getDBSchema(path[1])
                        gsWorkspace = self.auth.getGSWorkspace(path[1])
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
                                                            dataName, dataType, gsWorkspace, userName,
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

                # PUT /files/<user>/file.shp"
                if path[0]  == "files" and len(path) == 3:
                    from fileman import FileMan
                    fm = FileMan()

                    # Everyone can PUT only his/her own files 
                    userName = self.auth.getUserName()
                    if userName != path[1]:
                        logging.error("[LayMan][PUT] %s is not authorized to put files of %s"% (userName, path[1]))
                        raise AuthError(401, "Sorry, you are not authorized to update files of %s"% path[1])

                    fileName = path[-1]
                    data = web.data()
                    (code, message) = fm.putFile(self._getTargetFile(
                                                 fileName), data)

                # PUT /data/<group>/{table|view|file}/<data>?fileName=Rivers.shp
                elif path[0] == "data" and len(path) == 4:
                    from layed import LayEd
                    le = LayEd()

                    # Check authorization for the given group
                    checkRole = self.auth.getRole(path[1])
                    if checkRole["roleName"] != path[1]:
                        logging.error("[LayMan][PUT] Not authorized to PUT data for %s group"% path[1])
                        raise AuthError(401, "Sorry, you are not authorized to put data in %s group"% path[1])

                    # fileName must be given
                    inpt = web.input()
                    if not inpt.fileName:
                        raise LaymanError(400, "'fileName' parameter must be given")

                    # Note: currently all vectors are stored in database and all rasters are stored in filesystem.
                    # If some vector is to be stored in the fs or some raster in the db, 
                    # LayEd.updateData() must be adjusted and receive path[2] as a parameter
                    
                    fsUserDir = self.auth.getFSUserDir()
                    fsGroupDir = self.auth.getFSGroupDir(path[1])
                    dbSchema = self.auth.getDBSchema(path[1])
                    gsWorkspace = self.auth.getGSWorkspace(path[1])

                    (code, message) = le.updateData(path[3], gsWorkspace, fsUserDir, fsGroupDir, dbSchema, inpt.fileName)

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

                # PUT /layers/<group>/<layer> 
                # was /layed/config/<layer>?usergroup=FireBrigade
                elif path[0] == "layers" and len(path) == 3:
                    from layed import LayEd
                    le = LayEd()

                    # Check authorization for the given group
                    checkRole = self.auth.getRole(path[1])
                    if checkRole["roleName"] != path[1]:
                        logging.error("[LayMan][PUT] Not authorized to PUT layer for %s group"% path[1])
                        raise AuthError(401, "Sorry, you are not authorized to put layer in %s group"% path[1])

                    data = web.data()
                    data = json.loads(data)  # string -> json

                    fsUserDir = self.auth.getFSUserDir()
                    fsGroupDir = self.auth.getFSGroupDir(path[1])
                    dbSchema = self.auth.getDBSchema(path[1])
                    gsWorkspace = self.auth.getGSWorkspace(path[1])

                    (code, message) = le.putLayerConfig(gsWorkspace,
                                                        path[2], data,
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

                    # /files/<user>/file.shp"
                    if path[0] == "files" and len(path) == 3:
                        from fileman import FileMan
                        fm = FileMan()

                        # Everyone can DELETE only his/her own files 
                        userName = self.auth.getUserName()
                        if userName != path[1]:
                            logging.error("[LayMan][DELETE] %s is not authorized to delete files of %s"% (userName, path[1]))
                            raise AuthError(401, "Sorry, you are not authorized to delete files of %s"% path[1])

                        (code, message) = fm.deleteFile(self._getTargetFile(path[-1]))

                    # /user/<username>
                    elif path[0] == "user" and len(path) == 2:
                        userName = path[1]
                        from userprefs import UserPrefs
                        up = UserPrefs(config)
                        (code, message) = up.deleteUser(userName)

                    #     /layers/<group>/<layer>
                    # was /layed/<layer>
                    elif path[0] == "layers" and len(path) == 3:
                        from layed import LayEd
                        le = LayEd()

                        # Check authorization for the given group
                        checkRole = self.auth.getRole(path[1])
                        if checkRole["roleName"] != path[1]:
                            logging.error("[LayMan][DELETE] Not authorized to DELETE layer from %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to delete layer from %s group"% path[1])

                        gsWorkspace = self.auth.getGSWorkspace(path[1])
                        dbSchema    = self.auth.getDBSchema(path[1])
                        logging.info("[LayMan][DELETE] Delete layer '%s'"% path[2] )
                        logging.info("[LayMan][DELETE] Delete from workspace '%s'"% gsWorkspace)
                        # Delete layer only
                        (code, message) = le.deleteLayer(gsWorkspace, path[2], dbSchema, deleteTable=False)

                    #     /datalayers/<group>/<layer>
                    elif path[0] == "datalayers" and len(path) == 3:
                        from layed import LayEd
                        le = LayEd()

                        # Check authorization for the given group
                        checkRole = self.auth.getRole(path[1])
                        if checkRole["roleName"] != path[1]:
                            logging.error("[LayMan][DELETE] Not authorized to DELETE layer from %s group"% path[1])
                            raise AuthError(401, "Sorry, you are not authorized to delete layer from %s group"% path[1])

                        gsWorkspace = self.auth.getGSWorkspace(path[1])
                        dbSchema    = self.auth.getDBSchema(path[1])
                        logging.info("[LayMan][DELETE] Delete layer and data '%s'"% path[2] )
                        logging.info("[LayMan][DELETE] Delete from workspace '%s'"% gsWorkspace)
                        # Delete layer and data
                        (code, message) = le.deleteLayer(gsWorkspace, path[2], dbSchema, deleteTable=True)

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
        elif code in (501, "501", "notimplemented"):
            # web.notimplemented() # not implemented
            # TODO - set 501 code manually
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

