import unittest

import sys
import os
dir = os.path.abspath(os.path.dirname(__file__)) + '/..'
sys.path.insert(0, dir)

from ldap_stubber import LdapElement
import ldap

def convert_dict(dict):
	"""
	Converts the dict to ldap attributes
	"""
	list = []
	for key in dict:
		list.append( (key, dict[key]) )
	return list
	

def new_ldap_element(dn='cn=item,ou=schule,o=lestwo', attrs={}):
	default = {
		'cn': 'item',
		'attr1': 'val1',
		'attr2': 'val2'
	}
	default.update(attrs)
	return LdapElement(dn, convert_dict(default))

class LdapElementCreationWithoutLists(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
	def test_should_create_attr1_with_list(self):
		self.assertEqual(self.element.attr1, [ 'val1' ])
	def test_should_create_attr2_with_list(self):
		self.assertEqual(self.element.attr2, [ 'val2' ])
	def test_should_create_the_dn(self):
		self.assertEqual(self.element.dn, 'cn=item,ou=schule,o=lestwo')

class LdapElementCreationWithLists(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element(attrs={ 'attr1': ['val1', 'val2'] })
	def test_should_create_attr1_with_list(self):
		self.assertEqual(self.element.attr1, [ 'val1', 'val2' ])

class LdapElementModification(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
		self.element.modify([ 
			( ldap.MOD_REPLACE, 'attr3', [ 'val1', 'val2' ] ),
			( ldap.MOD_REPLACE, 'attr1', [ 'val5', 'val6' ] ),
			( ldap.MOD_ADD, 'attr2', [ 'val7' ] ),
		])
	def test_should_create_attr3(self):
		self.assertEqual(self.element.attr3, [ 'val1', 'val2' ])
	def test_should_replace_attr1(self):
		self.assertEqual(self.element.attr1, [ 'val5', 'val6' ])
	def test_should_add_elements_to_attr2(self):
		self.assertEqual(self.element.attr2, [ 'val2', 'val7' ])

class LdapElementRename(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
		self.element.modrdn('cn=newcn')
	def test_should_update_the_dn(self):
		self.assertEqual(self.element.dn, 'cn=newcn,ou=schule,o=lestwo')
	def test_should_update_the_attribute(self):
		self.assertEqual(self.element.cn, [ 'newcn' ])

class LdapElementPrefixCheck(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
		self.schule_lestwo_subtree = self.element.has_prefix(
			'ou=schule,o=lestwo'
		)
		self.wrong_subtree = self.element.has_prefix('wrong=base')
		self.lestwo_subtree = self.element.has_prefix('o=lestwo')
		self.schule_lestwo_base = self.element.has_prefix(
			'ou=schule,o=lestwo', ldap.SCOPE_BASE
		)
		self.lestwo_base = self.element.has_prefix(
			'o=lestwo', ldap.SCOPE_BASE
		)

	def test_should_return_true_on_right_subtree(self):
		self.assertEqual(self.schule_lestwo_subtree, True)
		self.assertEqual(self.lestwo_subtree, True)
	def test_should_return_false_on_wrong_subtree(self):
		self.assertEqual(self.wrong_subtree, False)
	def test_should_return_true_on_right_base(self):
		self.assertEqual(self.schule_lestwo_base, True)
	def test_should_return_false_on_wrong_base(self):
		self.assertEqual(self.lestwo_base, False)

class ConversionToResult(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
		self.result = self.element.to_result()
	
	def test_should_convert_correctly(self):
		self.assertEqual(self.result, ( 'cn=item,ou=schule,o=lestwo', {
			'attr1': [ 'val1' ],
			'cn':    [ 'item' ],
			'attr2': [ 'val2' ] 
		}))

class AndFilter(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
	def test_should_match_when_searching_for_the_attr1(self):
		self.assertTrue(self.element.matches('(attr1=val1)'))
	def test_should_not_match_when_searching_for_the_attr1(self):
		self.assertFalse(self.element.matches('(attr1=val2)'))
	def test_should_not_match_when_searching_for_attr1_and_2(self):
		self.assertFalse(self.element.matches('(&(attr1=val2)(attr2=val9))'))
	def test_should_match_when_both_attributes_are_matching(self):
		self.assertTrue(self.element.matches('(&(attr1=val1)(attr2=val2))'))

class OrFilter(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
	def test_should_not_match_if_no_attr_matches(self):
		self.assertFalse(self.element.matches('(|(attr1=zomg)(attr2=haha))'))
	def test_should_match_if_one_attr_matches(self):
		self.assertTrue(self.element.matches('(|(attr1=val1)(attr2=haha))'))

class FilterCombination(unittest.TestCase):
	def setUp(self):
		self.element = new_ldap_element()
	def test_should_match_with_and_and_or(self):
		self.assertTrue(self.element.matches(
			'(&(cn=item)(|(attr1=val1)(attr2=haha)))'
		))

if __name__ == '__main__':
	unittest.main()
