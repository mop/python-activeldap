"""
= Introduction =
ActiveLdap is an simple ObjectRelationalMapper for LDAP for python, which 
is inspired from the ruby ActiveLdap library.

To use it you must derive from the active_ldap.Base-class and specify several
instance-variables on this class. Then you must connect to your ldap-server via
the establish_connection-method.

== Basic Usage ==
To specify a User-class you must do the following:
	from active_ldap import Base
	import ldap
	class User(Base):
		attributes = (
			'uid',
			'sn',
			'telephoneNumber',
			'mail',
			'givenName',
			#...
		)
		dn_attribute = 'uid'
		scope = ldap.SCOPE_SUBTREE
		prefix = 'ou=users,o=yourtree'
		object_classes = ('inetOrgPerson',)

	Base.establish_connection({
		'uri': 'ldap://someip',
		#...
	})
	
	User.find_all()		# returns all users
	u = User.find_by_id('some_user') # finds the user with the ID 'some_user'
	u.telephoneNumber = '44444'
	u.save()			# updates the user

	u = User({
		'uid': 'someid',
		'cn': 'somecn',
		'telephoneNumber': '8888',
		'mail': 'somebody@example.com',
		'givenName': 'test',
	})
	u.save()			# Creates the user 

	u.delete()			# Deletes the user

	User.find('(telephoneNumber=3333)')	# Returns all users with the 
										# phone number 3333
	
== Relationships ==
ActiveLdap allows you to define 2 kinds of relationships: has-many and
many-to-many. This works like this:
	
	from active_ldap import Base
	import ldap

	class Switch(Base):
		object_classes = ('Switch', )
		attributes = (
			'SwitchID',
			'ipHostNumber',
			# ...
		)
		dn_attribute = 'SwitchID'
		prefix = 'ou=voip,o=schule'
		scope = ldap.SCOPE_SUBTREE

	class Device(Base):
		object_classes = (
			'voipPhone',
		)

		attributes = (
			'voipPhoneID',
			'voipPhoneMac',
			'voipPhoneNumber',
			'SwitchID',
			# ...
		)
		dn_attribute = 'voipPhoneID'
		prefix = 'ou=voip,o=tree'
		scope = ldap.SCOPE_SUBTREE

		switch = ForeignKey(
			Switch,
			my_attr='SwitchID',			# Device.SwitchID
			other_attr='SwitchID'		# Switch.SwitchID
		)

	class User(Base):
		#...
		devices = ManyToManyField(
			Device,
			my_attr='voipPhoneID',		# User.voipPhoneID
			other_attr='voipPhoneID'	# Device.voipPhoneID
		)

	Base.establish_connection({
		# ...
	})

	user = User.find_by_id('some_user')
	user.devices		# Returns all devices of the user (as array).
	device = Device.find_by_id('some device')
	device.users 		# Returns all users of the device (as array).
	sw = device.switch	# Returns the Switch of the device.
	sw.devices			# Returns all devices on the switch (as array).

In a ManyToMany-Relationship the 'my_attr'-attribute on the class is used as an
array to store all foreign IDs.
In a one-to-many-Relationship no attribute is used as an array, which means 
each Device.SwitchID-attribute contains only a single SwitchID.

"""

