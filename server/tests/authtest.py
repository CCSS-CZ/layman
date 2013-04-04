import os,sys
import unittest
import ConfigParser

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
INSTALL_DIR = os.path.abspath(os.path.join(TEST_DIR,".."))
sys.path.append(os.path.join(INSTALL_DIR))

#import layman.auth
from layman.auth import LaymanAuthLiferay, AuthError

class AuthTestCase(unittest.TestCase):
    """Test of the auth module"""

    au = None
    slavek = None

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.au = LaymanAuthLiferay(cfg)

        self.slavek = '{"resultCode":"0","userInfo":{"lastName":"Doe","email":"test@ccss.cz","roles":[{"roleName":"Power User","roleTitle":"Silny uzivatel"},{"roleName":"User","roleTitle":"uzivatel"},{"roleName":"ukraine_gis","roleTitle":"UA GIS"}],"userId":10432,"screenName":"test","language":"en","firstName":"John","groups":[]},"leaseInterval":1800}'

        self.au._parseUserInfo(self.slavek) # This should authorise user 'test'

    # TODO: add test for _getUserInfo() (real JSESSIONID needed)

    def test__parseUserInfo(self):
        """Test _parseUserInfo function """
        # Test
        self.assertEquals(self.au.authorised, True, "User is not authorised")
        self.assertEquals(type(self.au.authJson), type({}), "authJson is not an object")
        self.assertEquals(self.au.authJson["resultCode"], "0", "Result code is not a zero")
        self.assertEquals(self.au.authJson["userInfo"]["screenName"], "test", "Screen Name is not 'test'")
        self.assertEquals(self.au.authJson["userInfo"]["roles"][2]["roleName"], "ukraine_gis", "Cannot find 'ukraine_gis' roleName")
        self.assertEquals(self.au.authJson["userInfo"]["roles"][2]["roleTitle"], "UA GIS", "Cannot find 'UA GIS' roleTitle")

    def test_getRole(self):

        self.assertEquals( "Power User", self.au.getRole()["roleName"], "Get role fails - 1" )
        self.assertEquals( "ukraine_gis", self.au.getRole("ukraine_gis")["roleName"], "Get role fails - 2a" )
        self.assertEquals( "UA GIS", self.au.getRole("ukraine_gis")["roleTitle"], "Get role fails - 2b" )
        self.assertEquals( "Power User", self.au.getRole("NoSuchRole")["roleName"], "Get role fails - 3" )

    def test_getRoles(self):

        result = self.au.getRolesStr()
        self.assertEquals( '[{"roleName": "Power User", "roleTitle": "Silny uzivatel"}, {"roleName": "User", "roleTitle": "uzivatel"}, {"roleName": "ukraine_gis", "roleTitle": "UA GIS"}]', result, "getRoles() failed, returned: '" + result + "'") 

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(AuthTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
