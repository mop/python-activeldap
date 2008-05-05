from active_ldap import Base, ForeignKey, ManyToManyField
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
	attributes = {
		'userID': 'user_id',
		'deviceID': 'device_id',
		'name': 'user_name',
		'mail': 'user_mail',
	}
	dn_attribute = 'userID'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE
	device = ForeignKey(TestPhone, my_attr='deviceID', other_attr='phoneID')

class TestMultipleUser(Base):
	"""
	This class represents an user which has multiple phones
	"""
	object_classes = (
		'user',
		'person',
	)
	attributes = {
		'userID': 'user_id',
		'deviceID': 'device_id',
		'name': 'user_name',
		'mail': 'user_mail',
	}
	dn_attribute = 'userID'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE
	devices = ManyToManyField(
		TestPhone,
		my_attr='deviceID',
		other_attr='phoneID'
	)

class SignalTester(Base):
	"""
	This class tests the signal handling for ActiveLdap
	"""
	object_classes = (
		'user', 
		'person'
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

	def __init__(self, *args, **kwds):
		self.reset_signal_flags()
		super(SignalTester, self).__init__(*args, **kwds)

	def reset_signal_flags(self):
		self.ev_before_save = self.ev_after_save = False
		self.ev_before_create = self.ev_after_create = False
		self.ev_before_update = self.ev_after_update = False
		self.ev_after_delete = self.ev_before_delete = False

	def after_save(self):
		self.ev_after_save = True
	
	def before_save(self):
		self.ev_before_save = True

	def after_create(self):
		self.ev_after_create = True

	def before_create(self):
		self.ev_before_create = True

	def after_update(self):
		self.ev_after_update = True

	def before_update(self):
		self.ev_before_update = True

	def after_delete(self):
		self.ev_after_delete = True

	def before_delete(self):
		self.ev_before_delete = True


def new_user(attrs={}):
	default = { 
		'userID': 'user1',
		'name' : 'the_user',
		'mail' : 'user@example.com',
		'deviceID' : 'phone1',
	}
	default.update(attrs)
	return TestUser(default)

def new_multiple_user(attrs={}):
	default = { 
		'userID': 'user1',
		'name' : 'the_user',
		'mail' : 'user@example.com',
		'deviceID' : 'phone1',
	}
	default.update(attrs)
	return TestMultipleUser(default)

def new_phone(attrs={}):
	default = { 
		'phoneID': 'phone1',
		'name' :   'the_phone',
	}
	default.update(attrs)
	return TestPhone(default)

def setup_many_to_many_relations(tester):
	Base.connection = LdapStubber()
	tester.user1 = new_multiple_user()
	tester.user1.save()
	tester.user2 = new_multiple_user({
		'userID': 'user2',
		'deviceID': [
			'phone1', 'phone2'
		],
	})
	tester.user2.save()
	tester.phone1 = new_phone()
	tester.phone1.save()
	tester.phone2 = new_phone({'phoneID': 'phone2'})
	tester.phone2.save()

def setup_has_many_relations(tester):
	Base.connection = LdapStubber()
	tester.user  = new_user()
	tester.phone = new_phone()
	tester.phone.save()
	tester.user.save()

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

class PropertyLinksAccess(unittest.TestCase):
	def setUp(self):
		self.user = new_user()

	def test_should_create_the_correct_links(self):
		self.assertEqual(self.user.user_id, 'user1')
		self.assertEqual(self.user.device_id, 'phone1')
		self.assertEqual(self.user.user_name, 'the_user')

class PropertyLinksUpdateContructor(unittest.TestCase):
	def setUp(self):
		self.user = TestUser({
			'user_id':   'user2',
			'device_id': 'phone1',
		})

	def test_should_update_the_normal_links(self):
		self.assertEqual(self.user.userID, 'user2')
		self.assertEqual(self.user.deviceID, 'phone1')

class PropertyLinksUpdateAssignment(unittest.TestCase):
	def setUp(self):
		self.user = new_user()
		self.user.user_id = 'some id'
		self.user.device_id = 'some id2'

	def test_should_update_the_user(self):
		self.assertEqual(self.user.userID, 'some id')

	def test_should_update_the_device(self):
		self.assertEqual(self.user.deviceID, 'some id2')

class ManyToManyRelationWithTwoUserAndTwoPhones(unittest.TestCase):
	def setUp(self):
		setup_many_to_many_relations(self)
	
	def test_should_return_one_device_for_user1(self):
		self.assertEqual(len(self.user1.devices), 1)
		self.assertEqual(self.user1.devices[0].phoneID, 'phone1')

	def test_should_return_two_devices_for_user2(self):
		self.assertEqual(len(self.user2.devices), 2)

	def test_should_return_two_users_for_device1(self):
		self.assertEqual(len(self.phone1.testmultipleusers), 2)

	def test_should_return_one_user_for_device2(self):
		self.assertEqual(len(self.phone2.testmultipleusers), 1)
		self.assertEqual(self.phone2.testmultipleusers[0].userID, 'user2')

class AClassWithSignals(unittest.TestCase):
	def setUp(self):
		self.user = SignalTester({
			'userID': 'id',
			'deviceID': 'dev_id',
			'name': 'user_name',
			'mail': 'mail',
		})
	
	def test_should_notify_on_save(self):
		self.user.save()
		self.assertTrue(self.user.ev_before_save)
		self.assertTrue(self.user.ev_after_save)

	def test_should_notify_on_update(self):
		self.user.update()
		self.assertTrue(self.user.ev_before_update)
		self.assertTrue(self.user.ev_after_update)

	def test_should_notify_on_create(self):
		self.user.create()
		self.assertTrue(self.user.ev_before_create)
		self.assertTrue(self.user.ev_after_create)

	def test_should_notify_on_delete(self):
		self.user.delete()
		self.assertTrue(self.user.ev_before_delete)
		self.assertTrue(self.user.ev_after_delete)

class AHasManyClassWithReferencesWhenDeletingTheReference(unittest.TestCase):
	def setUp(self):
		setup_has_many_relations(self)
		self.phone.delete()

	def test_should_delete_the_phone_id_on_the_user_object(self):
		user = TestUser.find_by_id('user1')
		self.assertEqual(user.deviceID, [])

class AManyToManyFieldWithReferencesWhenDeleting(unittest.TestCase):
	def setUp(self):
		setup_many_to_many_relations(self)

		self.phone1.delete()
	
	def test_user1_should_have_zero_phones(self):
		user = TestMultipleUser.find_by_id('user1')
		self.assertEqual(user.devices, [])
	
	def test_user2_should_have_only_one_phone(self):
		user = TestMultipleUser.find_by_id('user2')
		self.assertEqual(len(user.devices), 1)
		self.assertEqual(user.devices[0].phoneID, 'phone2')

class AHasManyClassWithReferencesWhenModifyingTheDn(unittest.TestCase):
	def setUp(self):
		setup_has_many_relations(self)
		self.phone1 = TestPhone.find_by_id('phone1')
		self.phone1.phoneID = 'phone_new_id'
		self.phone1.save()
	
	def test_should_update_the_deviceID_on_the_user(self):
		user = TestUser.find_by_id('user1')
		self.assertEqual(user.deviceID, 'phone_new_id')

class AManyToManyClassWithReferencesWhenModifyingTheDn(unittest.TestCase):
	def setUp(self):
		setup_many_to_many_relations(self)
		self.phone1 = TestPhone.find_by_id('phone1')
		self.phone1.phoneID = 'phone_new_id'
		self.phone1.save()

	def test_should_update_the_deviceID_on_user1(self):
		user = TestMultipleUser.find_by_id('user1')
		self.assertEqual(user.deviceID, 'phone_new_id')

	def test_should_update_the_deviceID_on_user2(self):
		user = TestMultipleUser.find_by_id('user2')
		self.assertEqual(user.deviceID, [ 'phone_new_id', 'phone2' ])

if __name__ == '__main__':
	unittest.main()
