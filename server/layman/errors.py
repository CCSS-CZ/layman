# License: ....
# authors: Michal, Jachym

class LaymanError(Exception):
    """Layman error class
    """
    code = 500
    message = "Layman exception: "

    def __init__(self, code, message):
        self.code = code
        self.message += message

    def __str__(self):
        return repr(self.code) + ": " + self.message

class AuthError(LaymanError):
    """Auth error class
    """
    message = "Auth Error: "

