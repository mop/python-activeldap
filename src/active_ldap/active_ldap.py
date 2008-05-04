"""
This module includes the Base class from which the other classes must be
derived.
"""
import ldap
import re
import os
from signals.signals import Sendable, send_event

class RelationField(object):
	"""
	This is a base-class for relationships.
	It takes the other_class and two attributes (the local one, and the one on
	the foreign class) as parameter.

	other_class -- The other class of the relationship.
	my_attr -- the name of the local attribute.
	other_attr -- The name of the attribute on the other class.
	"""
	def __init__(self, other_class, my_attr=None, other_attr=None):
		if other_attr is None:
			other_attr = other_class.dn_attribute
		if my_attr is None:
			my_attr = other_attr
		self.other_class = other_class
		# Unfortunately we can't populate this attribute since the called-class
		# should not exist on the timepoint of creating this class :(
		self.my_class	 = None
		self.my_attr     = my_attr
		self.other_attr  = other_attr
	
	def create_relation(self, foreign_name, cls):
		"""
		Creates the relationship
		
		foreign_name -- the name of the attribute in the dictionary
		cls -- the class which called the object
		name -- the name of the class
		bases -- the bases of the class
		dct -- the dictionary of the class
		"""
		raise NotImplementedError("Not Implemented")

def referenced_object_deleted(self, obj):
	"""
	This method is called from the referenced class if an instance of it
	was deleted
	
	obj -- the object which will be deleted
	"""
	name = "%ss" % self.my_class.__name__.lower()
	deleted_id = getattr(obj, self.other_attr)
	items = getattr(obj, name)
	for item in items:
		attr = getattr(item, self.my_attr)
		if not isinstance(attr, list):
			attr = [ attr ]
		# remove the id
		attr.remove(deleted_id)
		setattr(item, self.my_attr, attr)
		item.save()
		
class ForeignKey(RelationField):
	"""
	This class is used to specify a has-many relationship.
	"""

	def _create_fetch_single_object(self, foreign_name):
		"""
		Returns a function for fetching the single objects on the my_class (the
		class with the foreign-key).

		foreign_name -- is the name of the ForeignKey instance in the
		dictionary of the class which defined it.
		"""
		foreign = self
		singular_name = "_%s" % foreign_name
		def fetch_object(self):
			""" 
			this method fetches the single other FSK-Object and caches in an
			instance variable.
			"""
			if singular_name not in self.has_many_list:
				self.has_many_list.append(singular_name)
			if not hasattr(self, singular_name) or \
				getattr(self, singular_name) is None:

				my_id = getattr(self, foreign.my_attr)
				elements = None
				try:
					elements = foreign.other_class.find('(%s=%s)' % (
						foreign.other_attr, my_id
					))[0]
				except ldap.LDAPError:
					elements = None
				setattr(self, singular_name, elements)
			return getattr(self, singular_name)
		return fetch_object

	def _create_fetch_multiple_objects(self):
		"""
		Creates the multiple-fetch-property on the referenced class.
		"""
		cls = self.my_class
		plural_name = "_%ss" % cls.__name__.lower()
		foreign = self
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
		return fetch_objects

	def create_relation(self, foreign_name, cls):
		"""
		Creates the has-many relationship.
		"""
		self.other_class.events.register(
			'before_delete', 
			lambda event, instance: referenced_object_deleted(self, instance)
		)
		self.my_class = cls

		setattr(cls, foreign_name,
				property(self._create_fetch_single_object(foreign_name))
		)
		setattr(
			self.other_class,
			cls.__name__.lower() + 's',
			property(self._create_fetch_multiple_objects())
		)

class ManyToManyField(RelationField):
	"""
	This class represents a many-to-many relationship.
	"""

	def _create_fetch_my_objects(self):
		"""
		Returns a function for fetching all objects of the class which has
		defined the ManyToManyField
		"""
		cls = self.my_class
		other_name = "_%ss" % cls.__name__.lower()
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
		return fetch_my_objects

	def _create_fetch_other_objects(self, foreign_name):
		"""
		Returns a function for fetching all objects of the class which has
		_not_ defined the ManyToManyField.
		"""
		my_name = "_%s" % foreign_name
		foreign = self
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
		return fetch_other_objects


	def create_relation(self, foreign_name, cls):
		"""
		Creates a many-to-many realtionship for the given class
		
		If. we have e.g. a User-class, which defined a relation to a 
		DeviceClass via the ManyToManyField my_name would be devices and
		other_name would be users. fetch_my_objects would return all users for
		the current device and would be set on the device-class.
		"""
		self.other_class.events.register(
			'before_delete', 
			lambda event, instance: referenced_object_deleted(self, instance)
		)
		self.my_class = cls

		# on the User class set the fetch_other_objects...
		setattr(
			cls,
			foreign_name,
			property(self._create_fetch_other_objects(foreign_name))
		)
		# on the Device class set the fetch_my_objects...
		setattr(
			self.other_class,	         			    # eg. Device
			self.my_class.__name__.lower() + 's',       # eg. users
			property(self._create_fetch_my_objects())	# eg. property
		)


class NullConnection(object):
	"""
	If no connection is specified this connection object is actually used in
	order to not block in unit-tests, etc.
	"""
	def search_s(self, *args, **kwds): 
		"""
		Searches the directory
		"""
		return []
	def add_s(self, *args, **kwds): 
		"""
		Adds an element to the directory
		"""
		return []
	def modify_s(self, *args, **kwds): 
		"""
		Modifies an element in the directory
		"""
		return []
	def delete_s(self, *args, **kwds): 
		"""
		Deletes an entry in the directory
		"""
		return []
	def modrdn_s(self, *args, **kwds): 
		"""
		Modifies the DN of an entry in the directory
		"""
		return []

class LdapFetcher(Sendable):
	"""
	This class autogenerates the ldap fields. It dynamically searches for
	Relation-instances on the class and creates the appropriate relationship.
	Moreover this class is responsible for creation the mapped attributes on 
	the class when specified.
	"""

	def __init__(cls, name, bases, dct):
		"""
		Dynamically searches for Relation-instances on the class and creates 
		the appropriate relationship. Moreover it generates the properties for
		the links.
		"""
		# First of all we have to enable signals on the appropriate class
		super(LdapFetcher, cls).__init__(name, bases, dct)

		if not hasattr(cls, 'connection'):
			cls.connection = NullConnection()

		cls._create_has_many_list()
		foreigns = filter(lambda key: isinstance(dct[key], RelationField), dct)
		for foreign_name in foreigns:
			dct[foreign_name].create_relation(
				foreign_name,
				cls,
			)
		if hasattr(cls, 'attributes') and isinstance(cls.attributes, dict):
			cls._create_property_links()
	
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
			"""
			Creates the set-property for the given key
			"""
			setattr(self, key, val)
		def get_it(self):
			"""
			Creates the get-property for the given key
			"""
			return getattr(self, key)
		setattr(cls, link, property(get_it, set_it))
	
	def _create_has_many_list(cls):
		"""
		Creates the has_many_list property, which contains all names of cached
		properties.
		"""
		def get_has_many_list(self):
			"""
			Returns the _has_many_list-attribute. If it doesn't exists it will
			be created.
			"""
			if not hasattr(self, '_has_many_list'):
				self._has_many_list = []
			return self._has_many_list
		def set_has_many_list(self, vals):
			"""
			Sets the _has_many_list-attribute.
			"""
			self._has_many_list = vals
		setattr(
			cls, 
			'has_many_list', 
			property(get_has_many_list, set_has_many_list)
		)

		def reload_cache(self):
			""" reloads the cached has_many and habtm-attributes """
			for i in self.has_many_list:
				setattr(self, i, None)
		setattr(cls, 'reload_cache', reload_cache)

class Base(object):
	"""
	This class represents the base of ActiveLdap. Concrete classes must derive
	from this class and specify the following things:
		* attributes: Might be a list or a dictionary of attributes which 
					  should be fetched from the directory
		* dn_attribute: The dn_attribute which should be used by the class
		* scope: the scope of the search-operaions. e.g. ldap.SCOPE_SUBTREE
		* object_classes: the ldap-objectClasses of the class.
	"""
	__metaclass__ = LdapFetcher

	object_classes = ('inetOrgUser', )
	"""
	Specifies the object-classes of the record type. This attribute should be
	overwritten by child-classes.
	"""

	attributes = {
		'uid': 'id',
		'givenName': 'name',
		'telephoneNumber': 'number',
	}
	"""
	This dictionary specifies which attributes should be fetched from ldap. 
	The values of the dictionary are names of properties which are created as
	links of the real values. This was made in order to abstract from the
	ldap-schema.
	This should be overwritten.
	"""

	dn_attribute = 'uid'
	"""
	Specifies the DN-Attribute of the class.
	This should be overwritten.
	"""

	scope = ldap.SCOPE_SUBTREE
	"""
	Specifies the scope in which the entries should be searched. This can be
	overwritten by child-classes.
	"""

	prefix = 'ou=user,o=tree'
	"""
	Specifies the prefix of the class.
	This should be overwritten by child-classes.
	"""

	def __init__(self, attrs=None, my_dn=None):
		"""
		Initializes the object with the global connection...
		"""
		attrs = attrs or {}
		if my_dn:
			self.dn = my_dn
		for key in self.attributes:
			setattr(self, key, '')
		for key in attrs.keys():
			val = self._get_val_from_dict(key, attrs)
			self._set_key(key, val)
	
	def _get_val_from_dict(self, key, dct):
		"""
		Returns the value of the key in the given dictionary

		key -- is the key of the dictionary
		dct -- is the dictionary whose value should be returned
		"""
		if dct[key].__class__ == list and len(dct[key]) == 1:
			return dct[key][0]
		else:
			return dct[key]

	def _is_key_in_attributes(self, key):
		"""
		Returns true if the given key is in the attributes list or dictionary.
		
		key -- the name of the attribute.
		"""
		result = key in self.attributes
		if result:
			return result
		if isinstance(self.attributes, dict):
			return key in self.attributes.values()
		return result

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
		Establishes the connection to ldap.
		
		config -- is a dictionary which might contain the following attributes:
			* uri: the URI to the server
			* bind_dn: the bind-dn for the admin-user
			* bind_password: the passwort for the bind-user
			* cert_path: the certificate for the server
			* timeout: the amout of time which should be waited before raising
					   an timeout-exception
		"""
		cls.config = config
		try:
			if 'timeout' in cls.config:
				ldap.set_option(
					ldap.OPT_NETWORK_TIMEOUT,
					cls.config['timeout']
				)
			cls.connection = ldap.initialize(cls.config['uri'])

			if cls.config['uri'].startswith('ldaps'):
				cls._init_certs()
				cls.connection.start_tls_s()
			cls.connection.simple_bind_s(
				cls.config['bind_dn'],
				cls.config['bind_password']
			)
			return cls.connection
		except ldap.LDAPError, ldap.TIMEOUT:
			del cls.connection
	
	@classmethod
	def _init_certs(cls):
		""" 
		Initializes the certs 
		"""
		if cls.config['cert_path'] == None:
			return
		cert = os.path.abspath(cls.config['cert_path'])
		ldap.set_option(ldap.OPT_X_TLS_CERTFILE, cert)

	@classmethod
	def find_by_id(cls, elem_id):
		"""Finds the item by id"""
		filter_expression = "(&%s(%s=%s))" % (
			cls._classes_string(),
			cls.dn_attribute,
			elem_id
		)
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			filter_expression
		)
		if len(results) == 0:
			return None
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
	def find(cls, filter_expression):
		"""Finds all which matches the given LDAP-filter"""
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			'(&%s%s)' % (cls._classes_string(), filter_expression)
		)
		return map(lambda (id, attrs): cls(attrs, id), results)

	# ---- creation methods -----
	@send_event
	def save(self):
		""" Saves (creates or updates) the item """
		try:
			if hasattr(self, 'dn') or \
			   self.find_by_id(getattr(self, self.dn_attribute)) != None:

				self.update()
			else:
				self.create()
		except ldap.LDAPError, error:
			print error
			return False
		return True
	
	@send_event
	def update(self):
		""" Updates the item in the directory """
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

	@send_event
	def create(self):
		""" Creates the item in the directory """
		attrs = self._collect_attrs()
		attrs = [ ( i[1], i[2] ) for i in attrs ]
		self.connection.add_s(self._collect_dn(), attrs)

	@send_event
	def delete(self):
		"""
		Deletes the item from the directory
		"""
		try:
			my_dn = self._collect_dn()
			self.connection.delete_s(my_dn)
			return True
		except ldap.LDAPError:
			return False
	
	@classmethod
	def delete_by_id(cls, my_dn):
		""" Deletes an entry by it's ID """
		try:
			cls.connection.delete_s(cls._construct_dn(my_dn))
			return True
		except ldap.LDAPError:
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
		return self.after_collect_attributes(attrs)

	def after_collect_attributes(self, attrs):
		"""
		Overwrite this method in order to manipulate the attributes after
		sending it to the ldap-library.
		
		attrs -- a list of attribute tuples
		"""
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
