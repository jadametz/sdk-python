"""
Edmunds.com API Python wrapper
Edmunds API Documentation: http://developer.edmunds.com/

author: Michael Bock <mbock@edmunds.com>
version: 0.1.1
"""

import requests
import json
import hashlib
import os.path
import tempfile
from types import StringType, BooleanType

TEMP_DIR = tempfile.gettempdir()


def make_cache_file_name(endpoint, kwargs_items):
	"""
	Creates a hashed file name for use in local caching during development

	:param endpoint: endpoint passed to Edmunds.make_call()
	:param kwargs_items: list of kwargs passed to Edmunds.make_call()
	:return: md5 hashed filename
	"""
	file_name = endpoint
	kwargs_string = ''
	for key, value in kwargs_items:
		kwargs_string += '_%s_%s' % (key, value)
		file_name += kwargs_string
	m = hashlib.md5()
	m.update(file_name)
	file_name = m.hexdigest()

	return file_name


class Edmunds:
	"""
	The Edmunds API wrapper class
	"""

	BASE_URL = 'https://api.edmunds.com'
	BASE_MEDIA_URL = 'http://media.ed.edmunds-media.com'

	def __init__(self, key, debug=False, cache=False):
		"""
		Constructor for Edmunds class

		:param key: Edmunds API key
		:param debug: True or False. If True, prints error messages
		:param cache: True or False. If True, activates local response caching for development
		:type key: str
		"""

		if not isinstance(debug, BooleanType):
			raise Exception('debug is not a BooleanType; class not instantiated')
		self._debug = debug

		if not isinstance(key, StringType):
			raise Exception('key not a StringType; class not instantiated')
		self._parameters = {'api_key': key, 'fmt': 'json'}

		if not isinstance(cache, BooleanType):
			raise Exception('cache is not a BooleanType; class not instantiated')
		self._cache = cache


	def make_call(self, endpoint, **kwargs):
		"""
		example calls:
		>>> make_call('/v1/api/vehiclephoto/service/findphotosbystyleid', comparator='simple', styleId='3883')
		>>> make_call('/api/vehicle/v2/lexus/rx350/2011/styles')

		Info about **kwargs: http://stackoverflow.com/questions/1769403/understanding-kwargs-in-python

		:param endpoint: Edmunds API endpoint, e.g. '/v1/api/vehiclephoto/service/findphotosbystyleid' or '/api/vehicle/v2/lexus/rx350/2011/styles'
		:type endpoint: str
		:param kwargs: List of extra parameters to be put into URL query string, e.g. view='full' or comparator='simple', styleId='3883'
		:type kwargs: List of key=value pairs, where the value is a str
		:returns: API response
		:rtype: JSON object
		"""
		# assemble url and queries
		payload = dict(self._parameters.items() + kwargs.items())
		url = self.BASE_URL + endpoint

		# make request
		try:
			if self._cache:
				# Check for the existence of a previously cached response
				file_name = make_cache_file_name(endpoint, kwargs.items())
				if os.path.isfile('%s/%s' % (TEMP_DIR, file_name)):
					try:
						json_file = open('%s/%s' % (TEMP_DIR, file_name))
					except:
						print 'Previously cached file could not be opened'
						pass
					try:
						json_from_file = json.load(json_file)
					except ValueError:
						print 'ValueError: Cached JSON could not be parsed'
						print 'Retrieving new response'
						r = requests.get(url, params=payload)
					else:
						json_file.close()
						return json_from_file
				# Otherwise make request
				else:
					r = requests.get(url, params=payload)
			else:
				r = requests.get(url, params=payload)
		# ConnectionError would result if an improper url is assembled
		except requests.ConnectionError:
			if self._debug:
				print 'ConnectionError: URL was probably incorrect'
			return None
		except requests.Timeout:
			if self._debug:
				print 'Timeout Error'
			return None

		# extract JSON
		try:
			response_json = r.json()

			# Cached response was not found, create file in TEMP_DIR before returning JSON
			if self._cache:
				with open('%s/%s' % (TEMP_DIR, file_name), 'w') as outfile:
					json.dump(response_json, outfile)

		# ValueError would result if JSON cannot be parsed
		except ValueError:
			if self._debug:
				print 'ValueError: JSON could not be parsed'
				print 'Response:'
				print r.text
			return None

		return response_json
