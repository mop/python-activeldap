from active_ldap import Base, ForeignKey
from ldap_stubber.ldap_stubber import LdapStubber
import unittest
import ldap

Base.connection = LdapStubber()

class TestPhone(Base):
	object_classes = (
		'klass3',
	)
	attributes = (
		'phoneID',
		'name',
	)
	dn_attribute = 'phoneID'
	prefix = 'ou=devices,o=schule'
	scope = ldap.SCOPE_SUBTREE

class TestUser(Base):
	object_classes = (
		'user',
		'person',
	)
	attributes = (
		'userID',
		'deviceID',
		'name',
		'mail',
	)
	dn_attribute = 'userID'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE
	device = ForeignKey(TestPhone, my_attr='deviceID', other_attr='phoneID')


def new_user(attrs={}):
	default = { 
		'userID': 'user1',
		'name' : 'the_user',
		'mail' : 'user@example.com',
		'deviceID' : 'phone1',
	}
	default.update(attrs)
	return TestUser(default)

def new_phone(attrs={}):
	default = { 
		'phoneID': 'phone1',
		'name' : 'the_phone',
	}
	default.update(attrs)
	return TestPhone(default)

class Relationship(unittest.TestCase):
	def setUp(self):
		Base.connection = LdapStubber()
		self.user = new_user()
		self.user.save()
		self.phone = new_phone()
		self.phone.save()
		self.user2 = new_user({ 'userID': 'user2' })
		self.user2.save()

	def test_should_have_two_users(self):
		self.assertEqual(len(self.phone.testusers), 2)
	
	def test_should_have_one_device(self):
		self.assertEqual(self.user.device.phoneID, self.phone.phoneID)

	def test_should_have_one_device2(self):
		self.assertEqual(self.user2.device.phoneID, self.phone.phoneID)
		
if __name__ == '__main__':
	unittest.main()
