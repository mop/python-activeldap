import ldap
import re
import sys

class RelationField(object):
	def __init__(self, other_class, my_attr=None, other_attr=None):
		if other_attr is None:
			other_attr = other_class.dn_attribute
		if my_attr is None:
			my_attr = other_attr
		self.other_class = other_class
		self.my_attr     = my_attr
		self.other_attr  = other_attr
	
	def create_relation(self, foreign_name, cls, name, bases, dict):
		"""
		Creates the relationship
		
		foreign_name -- the name of the attribute in the dictionary
		cls -- the class which called the object
		name -- the name of the class
		bases -- the bases of the class
		dict -- the dictionary of the class
		"""
		raise NotImplementedError("Not Implemented")
		
class ForeignKey(RelationField):
	"""
	This class represents a foreign key
	"""

	def __init__(self, *attrs, **kwds):
		super(ForeignKey, self).__init__(*attrs, **kwds)

	def create_relation(self, foreign_name, cls, name, bases, dct):
		foreign = self
		singular_name = "_%s" % foreign_name
		plural_name = "_%ss" % name.lower()
		def fetch_object(self):
			""" 
			this method fetches the single other FSK-Object and caches in an
			instance variable.
			"""
			if singular_name not in self.has_many_list:
				self.has_many_list.append(singular_name)
			if not hasattr(self, singular_name) or \
				getattr(self, singular_name) is None:

				id = getattr(self, foreign.my_attr)
				elements = None
				try:
					elements = foreign.other_class.find('(%s=%s)' % (
						foreign.other_attr, id
					))[0]
				except:
					pass
				setattr(self, singular_name, elements)
			return getattr(self, singular_name)
		def fetch_objects(self):
			""" 
			this method fetches multiple other FSK-Objects and caches them 
			in an instance variable.
			"""
			if plural_name not in self.has_many_list:
				self.has_many_list.append(plural_name)
			if not hasattr(self, plural_name) or \
				getattr(self, plural_name) is None:

				setattr(self, plural_name, cls.find(
					"(%s=%s)" % (
						foreign.my_attr, 
						getattr(self, foreign.other_attr)
				)))
			return getattr(self, plural_name)
		setattr(cls, foreign_name, property(fget=fetch_object))
		setattr(
			foreign.other_class,
			name.lower() + 's',
			property(fget=fetch_objects)
		)

class ManyToManyField(RelationField):
	"""
	This class represents a many-to-many relationship
	"""

	def __init__(self, *attrs, **kwds):
		super(ManyToManyField, self).__init__(*attrs, **kwds)
	def create_relation(self, foreign_name, cls, name, bases, dct):
		"""
		Creates a many-to-many realtionship for the given class
		
		If. we have e.g. a User-class, which defined a relation to a 
		DeviceClass via the ManyToManyField my_name would be devices and
		other_name would be users. fetch_my_objects would return all users for
		the current device and would be set on the device-class.
		"""
		my_name = "_%s" % foreign_name
		other_name = "_%ss" % name.lower()
		foreign = self
		def fetch_my_objects(self):
			"""
			This method fetches all objects of the class which has defined the
			ManyToManyField
			"""
			if other_name not in self.has_many_list:
				self.has_many_list.append(other_name)
			if not hasattr(self, other_name) or \
				getattr(self, other_name) is None:
				
				setattr(self, other_name, cls.find(
					"(%s=%s)" % (
						foreign.my_attr,			# e.g. deviceID
						getattr(self, foreign.other_attr) # e.g. val of phoneID
				)))
			return getattr(self, other_name)
		def fetch_other_objects(self):
			"""
			This method fetches all objects of the class which has _not_ 
			defined the ManyToManyField.
			"""
			# if e.g. 'devices' is not in list -> create it
			if my_name not in self.has_many_list:
				self.has_many_list.append(my_name)
			# cache miss
			if not hasattr(self, my_name) or \
				getattr(self, my_name) is None:
				
				# Fetch the list of IDs
				ids = getattr(self, foreign.my_attr)
				if not isinstance(ids, list):
					ids = [ ids ]
					
				# construct the filter expression...
				# e.g. (phoneID=phone1)(phoneID=phone2)...
				ids = ''.join([ 
					"(%s=%s)" % (foreign.other_attr, i) for i in ids 
				])
				
				setattr(self, my_name, foreign.other_class.find(
					"(|%s)" % ids
				))
			return getattr(self, my_name)
		# on the User class set the fetch_other_objects...
		setattr(cls, foreign_name, property(fget=fetch_other_objects))
		# on the Device class set the fetch_my_objects...
		setattr(
			foreign.other_class,	         # eg. Device
			name.lower() + 's',		         # eg. users
			property(fget=fetch_my_objects)  # eg. property
		)


class NullConnection(object):
	def search_s(self, *args, **kw): return []
	def add_s(self, *args, **kw): return []
	def modify_s(self, *args, **kw): return []
	def delete_s(self, *args, **kw): return []
	def modrdn_s(self, *args, **kw): return []

class LdapFetcher(type):
	"""
	This class autogenerates the ldap fields
	"""

	def __init__(cls, name, bases, dct):
		if not hasattr(cls, 'connection'):
			cls.connection = NullConnection()

		cls._create_has_many_list(name, bases, dct)
		foreigns = filter(lambda key: isinstance(dct[key], RelationField), dct)
		for foreign_name in foreigns:
			dct[foreign_name].create_relation(
				foreign_name,
				cls,
				name,
				bases,
				dct
			)
			#cls._create_has_many(foreign_name, name, bases, dct)
		if hasattr(cls, 'attributes') and isinstance(cls.attributes, dict):
			cls._create_property_links()

		super(LdapFetcher, cls).__init__(name, bases, dct)
	
	def _create_property_links(cls):
		"""
		Creates the property links for the given class
		"""
		for key in cls.attributes:
			cls._create_property(key, cls.attributes[key])
	
	def _create_property(cls, key, link):
		"""
		Creates the property link for the given key and link.
		
		key -- The name of the original ldap attribute.
		link -- The link-name of the property which should be created.
		
		"""
		def set_it(self, val):
			setattr(self, key, val)
		def get_it(self):
			return getattr(self, key)
		setattr(cls, link, property(get_it, set_it))
	
	def _create_has_many_list(cls, name, bases, dct):
		def get_has_many_list(self):
			if not hasattr(self, '_has_many_list'):
				self._has_many_list = []
			return self._has_many_list
		def set_has_many_list(self, list):
			self._has_many_list = list
		setattr(
			cls, 
			'has_many_list', 
			property(get_has_many_list, set_has_many_list)
		)

		def reload_cache(self):
			""" reloads the cached has_many-attributes """
			for i in self.has_many_list:
				setattr(self, i, None)
		setattr(cls, 'reload_cache', reload_cache)

class Base(object):
	"""
	This class represents the base of ActiveLdap
	"""
	__metaclass__ = LdapFetcher

	def __init__(self, attrs={}, dn=None):
		"""
		Initializes the object with the global connection...
		"""
		if dn:
			self.dn = dn
		for key in self.attributes:
			setattr(self, key, '')
		for key in attrs.keys():
			val = self._get_val_from_dict(key, attrs)
			self._set_key(key, val)
	
	def _get_val_from_dict(self, key, dict):
		"""
		Returns the value of the key in the given dictionary

		key -- is the key of the dictionary
		dict -- is the dictionary whose value should be returned
		"""
		if dict[key].__class__ == list and len(dict[key]) == 1:
			return dict[key][0]
		else:
			return dict[key]

	def _is_key_in_attributes(self, key):
		"""
		Returns true if the given key is in the attributes list or dictionary.
		
		key -- the name of the attribute.
		"""
		rv = key in self.attributes
		if rv:
			return rv
		if isinstance(self.attributes, dict):
			return key in self.attributes.values()
		return rv

	def _set_key(self, key, val):
		"""
		Assigns the given value to the given key
		
		key -- The attribute name which should be set
		val -- The value of the attribute
		"""
		if not self._is_key_in_attributes(key):
			return
		setattr(self, key, val)
		
	@classmethod
	def establish_connection(cls, config):
		"""
		Establishes the connection to ldap
		"""
		cls.config = config
		try:
			cls.connection = ldap.initialize(cls.config['uri'])
			if cls.config['uri'].startswith('ldaps'):
				cls._init_certs()
				cls.connection.start_tls_s()
			cls.connection.simple_bind_s(
				cls.config['bind_dn'],
				cls.config['bind_password']
			)
			return cls.connection
		except:
			del cls.connection
	
	def _init_certs(cls):
		""" 
		Initializes the certs 
		"""
		if cls.config['cert_path'] == None:
			return
		cert = os.path.abspath(cls.config['cert_path'])
		ldap.set_option(ldap.OPT_X_TLS_CERTFILE, cls.config['cert_path'])

	@classmethod
	def find_by_id(cls, id):
		"""Finds the item by id"""
		filter = "(&%s(%s=%s))" % (
			cls._classes_string(),
			cls.dn_attribute,
			id
		)
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			filter
		)
		if len(results) == 0: return None
		return cls(results[0][1], results[0][0])

	@classmethod
	def find_all(cls):
		"""
		Finds all items
		"""
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			'(&%s)' % cls._classes_string()
		)
		return map(lambda (id, attrs): cls(attrs, id), results)
	
	@classmethod
	def find(cls, filter):
		"""Finds all which matches the given LDAP-filter"""
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			'(&%s%s)' % (cls._classes_string(), filter)
		)
		return map(lambda (id, attrs): cls(attrs, id), results)

	# ---- creation methods -----
	def save(self):
		""" Saves (creates or updates) the User """
		try:
			if hasattr(self, 'dn') or \
			   self.find_by_id(getattr(self, self.dn_attribute)) != None:

				self.update()
			else:
				self.create()
		except Exception, e:
			print e
			return False
		return True
	
	def update(self):
		""" Updates the user in the directory """
		# Modify the DN via modrdn!
		if hasattr(self, 'dn'):
			new_attr = getattr(self, self.dn_attribute)
			self.connection.modrdn_s(self.dn, '%s=%s' % (
				self.dn_attribute, new_attr
			), True)
			# Set the DN-Attribute to the new value!
			self.dn = re.sub(r'^%s=.*?,' % self.dn_attribute, '%s=%s,' % (
				self.dn_attribute, new_attr
			), self.dn)
		self.connection.modify_s(self._collect_dn(), self._collect_attrs())

	def create(self):
		""" Creates the user in the directory """
		attrs = self._collect_attrs()
		attrs = [ ( i[1], i[2] ) for i in attrs ]
		self.connection.add_s(self._collect_dn(), attrs)

	def delete(self):
		"""
		Deletes the object from the directory
		"""
		try:
			dn = self._collect_dn()
			self.connection.delete_s(dn)
			return True
		except:
			return False
	
	@classmethod
	def delete_by_id(cls, id):
		""" Deletes an entry by it's ID """
		try:
			cls.connection.delete_s(cls._construct_dn(id))
			return True
		except:
			return False
		
		

	# ------ helper methods ------
	@classmethod
	def _classes_string(cls):
		"""Returns the object_classes as string"""
		return ''.join([ '(objectClass=%s)' % i for i in cls.object_classes ])
	
	def _collect_dn(self):
		"""Returns the DN for the object"""
		if hasattr(self, 'dn'):
			return self.dn
		return self._construct_dn(getattr(self, self.dn_attribute))

	@classmethod
	def _construct_dn(cls, attr):
		"""
		Constructs the actual DN
		"""
		return "%s=%s,%s" % (
			cls.dn_attribute,
			attr,
			cls.prefix
		)

	def _encode_val(self, val):
		"""
		Encodes the given value for LDAP
		
		val -- the value which should be encoded
		"""
		if isinstance(val, unicode):
			return val.encode('utf-8')
		if isinstance(val, bool):
			trans_table = { True: 'TRUE', False: 'FALSE' }
			return trans_table[val]
		if isinstance(val, list):
			return [ self._encode_val(i) for i in val ]
		return val
	
	def _encoded_attr(self, key):
		"""
		Encodes the given attribute in utf-8
		
		key -- the key (the name) of the attribute which should be encoded
		"""
		attr = getattr(self, key)
		return self._encode_val(attr)

	def _collect_attrs(self):
		"""
		Returns the attributes in the form:
		[ (ldap.MOD_REPLACE, key1, val1), (ldap.MOD_REPLACE, key2, val2), ... ]
		"""
		attrs = []
		for key in self.attributes:
			attrs.append( (
				ldap.MOD_REPLACE,
				key,
				self._encoded_attr(key)
			) )
		attrs.append( (
			ldap.MOD_REPLACE,
			'objectClass',
			list(self.object_classes)
		) )
		if hasattr(self, 'after_collect_attributes'):
			return self.after_collect_attributes(attrs)
		return attrs
		
if __name__ == '__main__':
#	u = User({
#		'sn': 'roflhaha1',
#		'telephoneNumber': '123345',
#		'uid': 'roflhaha12',
#		'mail': 'rofl@haha.de',
#		'voipDeviceID': 'DEVBL49_1',
#		'givenName': 'roflhaha1',
#		'cn': 'roflhaha1'
#	})
#	LDAP_CONFIG = {
#		'uri': 			 'ldap://192.168.49.50',
#		'bind_dn': 		 'cn=admin,o=schule',
#		'bind_password': 'netwix',
#		'cert_path': 	 'certs/groupwise.cert',
#	}
#	Base.establish_connection(LDAP_CONFIG)
#	dev = User.find_all()[0].device
#	print dev.users
#	print dev.users
#	print dev.users
#	print User.find_all()[0].device.users
#	print User.find_all()[0].device.users
#	print len(Device.find_all()[5].users)
	pass
