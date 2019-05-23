import requests
import json

# Export Logger to main module
from .logger import Logger


class LoginRequest:
    """Representation of Archiva's loginRequest

    Attributes:
            u (str): login user
            p (str): login password

    See:
            http://archiva.apache.org/docs/1.4-M4/rest-docs-redback-rest-api/el_ns0_loginRequest.html
    """

    def __init__(self, user, password):
        self.u = user
        self.p = password

    def get_xml(self):
        """Returns XML representation"""

        return f"<loginRequest>\
		<username>{self.u}</username>\
		<password>{self.p}</password>\
		</loginRequest>"


class ErrorResponse(Exception):
    """Custom exception for request errors produced in a Session

    Attributes:
            status_code (int): http response status code
            error_messages (object): set if Archiva returns error object
    """

    def __init__(self, status_code, error_messages=[]):
        super().__init__(
            f"Status Code: {status_code}; Error Messages: {error_messages}")
        self.status_code = status_code
        self.error_messages = error_messages


class Session:
    """Represents Archiva Session

    Attributes:
            host (str): Archiva instance host; it should include protocol and port
            user (str): Archiva session user
            password (str): Archiva session password
            *set_referer (bool): if True, all requests are sent with header "Referer: {host}"
            logger (archiva.Logger): session logger; defaults to "WARN" log level
            session_cookie (str): authenticated token

    Notes:
            - Caller should use `with` (RAII) pattern
            - Caller should try-except `json.decoder.JSONDecodeError`, `archiva.ErrorResponse` on any operation over session
    """

    def __init__(self, host, user, password, *, set_referer=False, logger=Logger()):
        self.host = host
        self.user = user
        self.password = password
        self.set_referer = set_referer
        self.logger = logger

    def __enter__(self):
        """RAII implementation; login on enter"""
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        """RAII implementation; logout on exit"""
        self.logout()

    def extract_session_cookie(set_cookie_value):
        """Internal utility method to extract JSESSIONID from Set-Cookie"""
        start_idx = set_cookie_value.find("JSESSIONID")
        end_idx = set_cookie_value.find(";", start_idx)
        return set_cookie_value[start_idx:end_idx]

    def login(self):
        """Login using user:password to get session token

        See:
                http://archiva.apache.org/docs/1.4-M4/rest-docs-redback-rest-api/resource_LoginService.html#path__loginService_logIn.html

        """

        # data is sent as xml and json response is expected
        headers = {
            "Content-Type": "application/xml",
            "Accept": "application/json"}
        if self.set_referer:
            headers["Referer"] = self.host

        # make request
        uri = f"{self.host}/restServices/redbackServices/loginService/logIn"
        self.logger.i(f"POST {uri}")
        res = requests.post(uri,
                            headers=headers,
                            data=LoginRequest(self.user, self.password).get_xml())

        if res.status_code != 200:
            # if not 200 OK it coult be:
            try:
                body = res.json()
                # authentication error (most probable)
                if "errorMessages" in body:
                    for err in body["errorMessages"]:
                        self.logger.e(err["errorKey"])
                    raise ErrorResponse(res.status_code, body["errorMessages"])
                # unknown error
                else:
                    raise ErrorResponse(res.status_code, body)
            except json.decoder.JSONDecodeError as e:
                # unexpected error
                if e.doc == "":
                    raise ErrorResponse(res.status_code)
                raise
        else:
            # login succesful; set session_cookie as auth token
            self.session_cookie = Session.extract_session_cookie(
                res.headers["Set-Cookie"])

    def logout(self):
        """Logout from Archiva session

        See:
                http://archiva.apache.org/docs/1.4-M4/rest-docs-redback-rest-api/resource_LoginService.html#path__loginService_logout.html

        """

        # must refer to current session
        headers = {"Cookie": self.session_cookie}
        if self.set_referer:
            headers["Referer"] = self.host

        # make request
        uri = f"{self.host}/restServices/redbackServices/loginService/logout"
        self.logger.i(f"GET {uri}")
        requests.get(uri, headers=headers)

    def get_versions_list(self, package_group, package_name):
        """versionsList endpoint

        Args:
                package_group (str): package group
                package_name (str): package name

        Returns:
                response(obj): if 200 OK; Archiva schema
                        {
                                'versions': [...]
                        }

        Raises:
                ErrorResponse if != 200 OK

        See:
                http://archiva.apache.org/docs/1.4-M4/rest-docs-archiva-rest-api/resource_BrowseService.html#path__browseService_versionsList_-g-_-a-.html
        """

        # must be authenticated
        headers = {
            "Cookie": self.session_cookie,
            "Accept": "application/json"}
        if self.set_referer:
            headers["Referer"] = self.host

        # make request
        uri =\
            f"{self.host}/restServices/archivaServices/\
browseService/versionsList/{package_group}/{package_name}"
        self.logger.i(f"GET {uri}")
        res = requests.get(uri, headers=headers)

        if res.status_code == 200:
            # if 200 OK, result should be json
            return res.json()
        else:
            # unexpected
            self.logger.e(f"status code: {res.status_code}")
            raise ErrorResponse(res.status_code)

    def get_download_infos(self, package_group, package_name, package_version):
        """downloadInfos endpoint

        Args:
                package_group (str): package group
                package_name (str): package name
                package_version (str): package version

        Returns:
                response(obj): if 200 OK; Archiva schema
                        [ { 'artifactId': '<packageName>',
                            'bundleDescription': None,
                            'bundleDocUrl': None,
                            'bundleExportPackage': None,
                            'bundleExportService': None,
                            'bundleImportPackage': None,
                            'bundleLicense': None,
                            'bundleName': None,
                            'bundleRequireBundle': None,
                            'bundleSymbolicName': None,
                            'bundleVersion': None,
                            'classifier': None,
                            'context': '<context>',
                            'fileExtension': '<fileExtension>',
                            'goals': None,
                            'groupId': '{package_group}',
                            'id': '<id == filename>',
                            'packaging': '<packaging ==? fileExtension>',
                            'path': '<path>',
                            'prefix': None,
                            'repositoryId': '<repositoryId>',
                            'scope': None,
                            'size': '<packageSize>',
                            'type': '<type ==? fileExtension>',
                            'url': '<downloadUrl>',
                            'version': '{packageVersion}'}]

        Raises:
                ErrorResponse if != 200 OK

        See:
                http://archiva.apache.org/docs/1.4-M4/rest-docs-archiva-rest-api/resource_BrowseService.html#path__browseService_artifactDownloadInfos_-g-_-a-_-v-.html
        """

        # must be authenticated
        headers = {"Cookie": self.session_cookie}
        if self.set_referer:
            headers["Referer"] = self.host

        # make request
        uri =\
            f"{self.host}/restServices/archivaServices/\
browseService/artifactDownloadInfos/{package_group}/{package_name}/{package_version}"
        self.logger.i(f"GET {uri}")
        res = requests.get(uri, headers=headers)

        if res.status_code == 200:
            # if 200 OK, result should be json
            return res.json()
        else:
            # unexpected
            self.logger.e(f"status code: {res.status_code}")
            raise ErrorResponse(res.status_code)

    def download(self, g, n, v):
        """Download Package

        Args:
                g (str): package group
                n (str): package name
                v (str): package version

        Returns:
                filename (str): if file was written; if 200 OK
                False: if there was no content associated to (g, n, v)

        Raises:
                See: `Session.get_download_info`

                ErrorResponse if != 200 OK when trying to GET download_info["url"]
        """

        # get download info
        download_infos = self.get_download_infos(g, n, v)
        if len(download_infos) > 0:
            download_info = download_infos[0]
        else:
            return False

        # get download url and output filename
        url = download_info["url"]
        filename = download_info["id"]

        # must be authenticated
        headers = {"Cookie": self.session_cookie}
        if self.set_referer:
            headers["Referer"] = self.host

        # make request
        self.logger.i(f"GET {url}")
        res = requests.get(url, headers=headers, allow_redirects=True)

        if res.status_code == 200:
            # if 200 OK, write content to file "filename"
            with open(filename, "wb") as f:
                f.write(res.content)
            return filename
        else:
            # this should not happen, since download url was successfully
            # retrieved from self.get_download_infos
            self.logger.e(f"status code: {res.status_code}")
            raise ErrorResponse(res.status_code)
