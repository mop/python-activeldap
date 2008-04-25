import unittest

import sys
import os
dir = os.path.abspath(os.path.dirname(__file__)) + '/..'
sys.path.insert(0, dir)

from ldap_stubber import LdapStubber
from test_ldap_element import convert_dict
import ldap

def new_ldap_stubber():
	return LdapStubber()

def new_element(dict={}, add_form=True):
	default = {
		'cn': 	 'item',
		'attr1': 'val1',
		'attr2': 'val2',
	}
	default.update(dict)
	items = convert_dict(default)
	if add_form:
		return items
	return [ ( ldap.MOD_REPLACE, i[0], i[1] ) for i in items ]
	

class AddingElements(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.stubber.add_s('ou=schule,o=lestwo', new_element())
	
	def test_should_have_a_collection_of_size1(self):
		self.assertEqual(len(self.stubber.elements), 1)
	def test_should_have_attr1(self):
		self.assertEqual(self.stubber.elements[0].attr1, [ 'val1' ])
	def test_should_have_a_dn(self):
		self.assertEqual(self.stubber.elements[0].dn, 'ou=schule,o=lestwo')

class ModifyingAnExistingElement(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.stubber.add_s(self.dn, new_element())
		self.stubber.modify_s(self.dn, new_element(add_form=False, dict={
			'attr3': 'newval',
			'attr1': [ 'val5', 'val4' ]
		}))
		self.element = self.stubber.elements[0]

	def test_should_add_the_new_attribute(self):
		self.assertEqual(self.element.attr3, [ 'newval' ])
	def test_should_alter_the_attr1(self):
		self.assertEqual(self.element.attr1, [ 'val5', 'val4' ])

class ModifyingAnNonExistingElement(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.cmd = lambda: self.stubber.modify_s(self.dn,
			new_element(add_form=False, dict={
				'attr3': 'newval',
				'attr1': [ 'val5', 'val4' ]
			})
		)

	def test_should_raise_error(self):
		self.assertRaises(RuntimeError, self.cmd)

class DeletingAnExistingElement(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.stubber.add_s(self.dn, new_element())
		self.stubber.delete_s(self.dn)
	def test_should_delete_the_element(self):
		self.assertEqual(len(self.stubber.elements), 0)

class DeletingAnNonExistingElement(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.cmd = lambda: self.stubber.delete_s(self.dn)
	def test_should_raise_error(self):
		self.assertRaises(RuntimeError, self.cmd)
	
class ModifyingTheDN(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.newdn = 'ou=newschule'
		self.stubber.add_s(self.dn, new_element())
		self.stubber.modrdn_s(self.dn, self.newdn, True)
	def test_should_change_the_dn(self):
		self.assertEqual(self.stubber.elements[0].dn, 'ou=newschule,o=lestwo')

class SearchingExistingElements(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.dn2 = 'ou=newschule,o=lestwo'
		self.stubber.add_s(self.dn, new_element())
		self.stubber.add_s(self.dn2, new_element(
			dict={ 'attr1': 'val2' })
		)
		self.results = self.stubber.search_s(
			'o=lestwo',
			ldap.SCOPE_SUBTREE,
			'(attr1=val1)'
		)

	def test_should_return_the_correct_result(self):
		self.assertEqual(self.results, [
			('ou=schule,o=lestwo', {
				'cn':    [ 'item' ],
				'attr1': [ 'val1' ],
				'attr2': [ 'val2' ],
			})
		])
	
class SearchingNonExistingElements(unittest.TestCase):
	def setUp(self):
		self.stubber = new_ldap_stubber()
		self.dn = 'ou=schule,o=lestwo'
		self.dn2 = 'ou=newschule,o=lestwo'
		self.stubber.add_s(self.dn, new_element())
		self.stubber.add_s(self.dn2, new_element(
			dict={ 'attr1': 'val2' })
		)
		self.results = self.stubber.search_s(
			'o=lestwo',
			ldap.SCOPE_SUBTREE,
			'(attr5=val1)'
		)

	def test_should_return_the_correct_result(self):
		self.assertEqual(self.results, [ ])
	
		

if __name__ == '__main__':
	unittest.main()
