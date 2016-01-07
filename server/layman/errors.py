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

class LaymanError(Exception):
    """Layman error class
    """
    code = 500
    message = "Layman exception: "
    innerMessage = ""

    def __init__(self, code, message):
        self.code = code
        self.message += message
        self.innerMessage = message

    def __str__(self):
        return repr(self.code) + ": " + self.message

class AuthError(LaymanError):
    """Auth error class
    """
    message = "Auth Error: "

