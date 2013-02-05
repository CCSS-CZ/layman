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

    def setUp(self):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read((os.path.join(TEST_DIR,"tests.cfg")))
        self.au = LaymanAuthLiferay(cfg)

    # TODO: add test for _getUserInfo() (real JSESSIONID needed)

    def test__parseUserInfo(self):
        """Test _parseUserInfo function """

        # Prepare
        slavek = '{"resultCode":"0","userInfo":{"lastName":"Doe","email":"test@ccss.cz","roles":[{"roleName":"Power User"},{"roleName":"User"},{"roleName":"ukraine_gis"}],"userId":10432,"screenName":"test","language":"en","firstName":"John","groups":[]},"leaseInterval":1800}'

        self.au._parseUserInfo(slavek) # This should authorise user 'test'

        # Test
        self.assertEquals(self.au.authorised, True, "User is not authorised")
        self.assertEquals(type(self.au.authJson), type({}), "authJson is not an object")
        self.assertEquals(self.au.authJson["resultCode"], "0", "Result code is not a zero")
        self.assertEquals(self.au.authJson["userInfo"]["screenName"], "test", "Screen Name is not 'test'")
        self.assertEquals(self.au.authJson["userInfo"]["roles"][2]["roleName"], "ukraine_gis", "Cannot find 'ukraine_gis' role")

if __name__ == "__main__":
   suite = unittest.TestLoader().loadTestsFromTestCase(AuthTestCase)
   unittest.TextTestRunner(verbosity=2).run(suite)
