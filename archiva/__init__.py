import requests
import json

from .logger import Logger

class LoginRequest:
	def __init__(self, user, password):
		self.u = user
		self.p = password

	def get_xml(self):
		return f"<loginRequest>\
		<username>{self.u}</username>\
		<password>{self.p}</password>\
		</loginRequest>"

class ErrorResponse(Exception):
	def __init__(self, status_code, error_messages=[]):
		super().__init__(f"Status Code: {status_code}; Error Messages: {error_messages}")
		self.status_code = status_code
		self.error_messages = error_messages

class Session:
	def __init__(self, host, user, password, *, set_referer=False, logger=Logger()):
		self.host = host
		self.user = user
		self.password = password
		self.set_referer = set_referer
		self.logger = logger

	def __enter__(self):
		self.login()
		return self

	def __exit__(self, type, value, traceback):
		self.logout()

	def extract_session_cookie(set_cookie_value):
		start_idx = set_cookie_value.find("JSESSIONID")
		end_idx = set_cookie_value.find(";", start_idx)
		return set_cookie_value[start_idx:end_idx]

	def login(self):
		headers = {
			"Content-Type": "application/xml",
			"Accept": "application/json"}

		if self.set_referer:
			headers["Referer"] = self.host

		uri = f"{self.host}/restServices/redbackServices/loginService/logIn"
		
		self.logger.i(f"POST {uri}")
		
		res = requests.post(uri,
			headers=headers,
			data=LoginRequest(self.user, self.password).get_xml())

		if res.status_code != 200:
			try:
				body = res.json()
				if "errorMessages" in body:
					for err in body["errorMessages"]:
						self.logger.e(err["errorKey"])
					raise ErrorResponse(res.status_code, body["errorMessages"])
				else:
					raise ErrorResponse(res.status_code, body)
			except json.decoder.JSONDecodeError as e:
				if e.doc == "":
					raise ErrorResponse(res.status_code)
				raise
		else:
			self.session_cookie = Session.extract_session_cookie(
				res.headers["Set-Cookie"])

	def logout(self):
		headers = {"Cookie": self.session_cookie}
		if self.set_referer:
			headers["Referer"] = self.host

		uri = f"{self.host}/restServices/redbackServices/loginService/logout"

		self.logger.i(f"GET {uri}")
		requests.get(uri, headers=headers)

	def get_versions_list(self, package_group, package_name):
		headers = {"Cookie": self.session_cookie}
		if self.set_referer:
			headers["Referer"] = self.host

		uri =\
f"{self.host}/restServices/archivaServices/\
browseService/versionsList/{package_group}/{package_name}"

		self.logger.i(f"GET {uri}")
		res = requests.get(uri, headers=headers)

		if res.status_code == 200:
			return res.json()
		else:
			self.logger.e(f"status code: {res.status_code}")
			raise ErrorResponse(res.status_code)

	def get_download_infos(self, package_group, package_name, package_version):
		headers = {"Cookie": self.session_cookie}
		if self.set_referer:
			headers["Referer"] = self.host

		uri=\
f"{self.host}/restServices/archivaServices/\
browseService/artifactDownloadInfos/{package_group}/{package_name}/{package_version}"

		self.logger.i(f"GET {uri}")
		res = requests.get(uri, headers=headers)

		if res.status_code == 200:
			return res.json()
		else:
			self.logger.e(f"status code: {res.status_code}")
			raise ErrorResponse(res.status_code)

	def download(self, g, n, v):
		download_infos = self.get_download_infos(g, n, v)
		if len(download_infos) > 0:
			download_info = download_infos[0]
		else:
			return False

		url = download_info["url"]
		filename = download_info["id"]

		headers = {"Cookie": self.session_cookie}
		if self.set_referer:
			headers["Referer"] = self.host

		self.logger.i(f"GET {url}")
		res = requests.get(url, headers=headers, allow_redirects=True)

		if res.status_code == 200:
			with open(filename, "wb") as f:
				f.write(res.content)
			return filename
		else:
			self.logger.e(f"status code: {res.status_code}")
			raise ErrorResponse(res.status_code)

