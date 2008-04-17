import ldap

class CacheDecorator(object):
	"""
	This class caches the result of a function
	"""

	def __init__(self, *args, **kwds):
		self._result = None
	
	def _cached_fun(self, *args, **kwds):
		if self._result is not None:
			return self._result
		self._result = self._fun(*args, **kwds)
		return self._result
	
	def __call__(self, fun):
		self._fun = fun
		return self._cached_fun

class ForeignKey(object):
	"""
	This class represents a foreign key
	"""

	def __init__(self, other_class, attribute=None):
		if attribute is None:
			attribute = other_class.dn_attribute
		self.other_class = other_class
		self.attribute   = attribute

class LdapFetcher(type):
	"""
	This class autogenerates the ldap fields
	"""

	def __init__(cls, name, bases, dct):
		foreigns = filter(lambda key: isinstance(dct[key], ForeignKey), dct)
		for foreign_name in foreigns:
			cls._create_has_many(foreign_name, name, bases, dct)

	def _create_has_many(cls, foreign_name, name, bases, dct):
		foreign = dct[foreign_name]
		@CacheDecorator()
		def fetch_object(self):
			return foreign.other_class.find_by_id(
				getattr(self, foreign.attribute)
			)
		@CacheDecorator()
		def fetch_objects(self):
			return cls.find(
				"(%s=%s)" % (
					foreign.attribute, getattr(self,
					foreign.attribute)
			))
		setattr(cls, foreign_name, property(fget=fetch_object))
		setattr(
			foreign.other_class,
			name.lower() + 's',
			property(fget=fetch_objects)
		)

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
			if key not in self.attributes: continue
			if attrs[key].__class__ == list:
				setattr(self, key, attrs[key][0])
			else:
				setattr(self, key, attrs[key])
		
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
		return cls(results[0][1])

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
		return map(lambda (id, attrs): cls(attrs), results)
	
	@classmethod
	def find(cls, filter):
		"""Finds all which matches the given LDAP-filter"""
		results = cls.connection.search_s(
			cls.prefix,
			cls.scope,
			'(&%s%s)' % (cls._classes_string(), filter)
		)
		return map(lambda (id, attrs): cls(attrs), results)

	# ---- creation methods -----
	def save(self):
		""" Saves (creates or updates) the User """
		try:
			if self.find_by_id(getattr(self, self.dn_attribute)) != None:
				self.update()
			else:
				self.create()
		except Exception, e:
			print e
			return False
		return True
	
	def update(self):
		""" Updates the user in the directory """
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
				getattr(self, key).encode('utf-8')
			) )
		attrs.append( (
			ldap.MOD_REPLACE,
			'objectClass',
			list(self.object_classes)
		) )
		if hasattr(self, 'after_collect_attributes'):
			return self.after_collect_attributes(attrs)
		return attrs
		
class Device(Base):
	"""
	This class represents a Device
	"""
	object_classes = ( 
		'voipDevice',
	)
	attributes = (
		'voipDeviceID',
		'voipPhoneNumber',
		'voipDeviceMac',
		'voipDeviceTyp',
		'voipDeviceIP',
	)
	dn_attribute = 'voipDeviceID'
	prefix = 'ou=voip,o=schule'
	scope = ( ldap.SCOPE_SUBTREE )


class User(Base):
	"""
	This class represents a LdapUser
	"""
	object_classes = ( 
		'voipUser',
		'User',
		'organizationalPerson' 
	)
	attributes = (
		'sn',
		'telephoneNumber',
		'uid',
		'mail',
		'voipDeviceID',
		'givenName',
		'cn'
	)
	dn_attribute = 'uid'
	prefix = 'ou=user,o=schule'
	scope = ( ldap.SCOPE_SUBTREE )
	device = ForeignKey(Device, 'voipDeviceID')

	def after_collect_attributes(self, attrs):
		number = filter(lambda i: i[1] == 'telephoneNumber', attrs)[0][2]
		attrs.append((ldap.MOD_REPLACE, 'voipPhoneNumber', number))
		return attrs

if __name__ == '__main__':
	u = User({
		'sn': 'roflhaha1',
		'telephoneNumber': '123345',
		'uid': 'roflhaha12',
		'mail': 'rofl@haha.de',
		'voipDeviceID': 'DEVBL49_1',
		'givenName': 'roflhaha1',
		'cn': 'roflhaha1'
	})
	LDAP_CONFIG = {
		'uri': 			 'ldap://192.168.49.50',
		'bind_dn': 		 'cn=admin,o=schule',
		'bind_password': 'netwix',
		'cert_path': 	 'certs/groupwise.cert',
	}
	Base.establish_connection(LDAP_CONFIG)
	dev = User.find_all()[0].device
	print dev.users
	print dev.users
	print dev.users
	print User.find_all()[0].device.users
	print User.find_all()[0].device.users
	print len(Device.find_all()[5].users)
