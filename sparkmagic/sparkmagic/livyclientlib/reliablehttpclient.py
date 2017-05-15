﻿# Copyright (c) 2015  aggftw@gmail.com
# Distributed under the terms of the Modified BSD License.
import json
from time import sleep
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
import requests
import subprocess

import sparkmagic.utils.configuration as conf
from sparkmagic.utils.sparklogger import SparkLog
from sparkmagic.utils.constants import MAGICS_LOGGER_NAME
import sparkmagic.utils.constants as constants
from sparkmagic.livyclientlib.exceptions import HttpClientException


class ReliableHttpClient(object):
    """Http client that is reliable in its requests. Uses requests library."""

    def __init__(self, endpoint, headers, retry_policy):
        self._endpoint = endpoint
        self._headers = headers
        self._retry_policy = retry_policy
        self.logger = SparkLog(u"ReliableHttpClient")

        self.verify_ssl = not conf.ignore_ssl_errors()
        if not self.verify_ssl:
            self.logger.debug(u"ATTENTION: Will ignore SSL errors. This might render you vulnerable to attacks.")
            requests.packages.urllib3.disable_warnings()

    def compose_url(self, relative_url):
        r_u = "/{}".format(relative_url.rstrip(u"/").lstrip(u"/"))
        return self._endpoint.url + r_u

    def get(self, relative_url, accepted_status_codes):
        """Sends a get request. Returns a response."""
        return self._send_request(relative_url, accepted_status_codes, requests.get)

    def post(self, relative_url, accepted_status_codes, data):
        """Sends a post request. Returns a response."""
        return self._send_request(relative_url, accepted_status_codes, requests.post, data)

    def delete(self, relative_url, accepted_status_codes):
        """Sends a delete request. Returns a response."""
        return self._send_request(relative_url, accepted_status_codes, requests.delete)

    def _send_request(self, relative_url, accepted_status_codes, function, data=None):
        return self._send_request_helper(self.compose_url(relative_url), accepted_status_codes, function, data, 0)

    def _send_request_helper(self, url, accepted_status_codes, function, data, retry_count):
        # self.logger.debug("Starting Url = {}, Auth Type = {}, Data = {}".format(url, self._endpoint.auth_type, json.dumps(data)))
        while True:
            try:
                if self._endpoint.auth_type == constants.NO_AUTH:
                    if data is None:
                        r = function(url, headers=self._headers, verify=self.verify_ssl)
                    else:
                        r = function(url, headers=self._headers, data=json.dumps(data), verify=self.verify_ssl)
                else:
                    if self._endpoint.auth_type == constants.AUTH_SSL:
                        auth = (self._endpoint.username, self._endpoint.password)
                    elif self._endpoint.auth_type == constants.AUTH_LDAP:
                        from requests.auth import HTTPBasicAuth
                        auth = HTTPBasicAuth(self._endpoint.username, self._endpoint.password)
                    elif self._endpoint.auth_type == constants.AUTH_KERBEROS:
                        from requests_kerberos import HTTPKerberosAuth, REQUIRED
                        principal = subprocess.check_output("klist | grep 'Principal:' | awk '{print $NF}'", shell=True).decode("utf-8").strip()
                        auth = HTTPKerberosAuth(principal=principal, mutual_authentication=REQUIRED, force_preemptive=True)
                    else:
                        raise ValueError("Unsupported authentication type {}".format(self._endpoint.auth_type))
                    
                    if data is None:
                        r = function(url, headers=self._headers, auth=auth, verify=self.verify_ssl, cookies = self._endpoint.cookies)
                    else:
                        r = function(url, headers=self._headers, auth=auth, data=json.dumps(data), verify=self.verify_ssl, cookies = self._endpoint.cookies)
            except requests.exceptions.RequestException as e:
                error = True
                r = None
                status = None
                text = None

                self.logger.error(u"Request to '{}' failed with '{}'".format(url, e))
            else:
                error = False
                status = r.status_code
                text = r.text

            if error or status not in accepted_status_codes:
                if self._retry_policy.should_retry(status, error, retry_count):
                    sleep(self._retry_policy.seconds_to_sleep(retry_count))
                    retry_count += 1
                    continue

                if error:
                    raise HttpClientException(u"Error sending http request and maximum retry encountered.")
                else:
                    raise HttpClientException(u"Invalid status code '{}' from {} with error payload: {}"
                                              .format(status, url, text))
            if r.cookies.get('hadoop.auth') and not self._endpoint.cookies:
                self._endpoint.cookies = {'hadoop.auth' : r.cookies.get('hadoop.auth')}
            return r
