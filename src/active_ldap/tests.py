import pyspec
import pymock
import active_ldap
import ldap

test_data = [ ( 'dn1', {
	'attribute1': [ 'someval1' ],
	'attribute2': [ 'someval2' ],
}), ( 'dn2', {
	'attribute1': [ 'someval3' ],
	'attribute2': [ 'someval4' ],
})]


class TestModel(active_ldap.Base):
	object_classes = (
		'klass1',
		'klass2'
	)
	attributes = (
		'attribute1',
		'attribute2',
	)
	dn_attribute = 'attribute1'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE

class TestModel2(active_ldap.Base):
	object_classes = (
		'klass1',
	)
	attributes = (
		'attribute1',
		'attribute2',
	)
	dn_attribute = 'attribute1'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE

class TestModel3(active_ldap.Base):
	object_classes = (
		'klass4',
	)
	attributes = (
		'attribute1',
		'attribute5',
	)
	dn_attribute = 'attribute1'
	prefix = 'ou=user,o=schule'
	scope = ldap.SCOPE_SUBTREE
	test_model = active_ldap.ForeignKey(TestModel2)

class ConnectionStub(object):
	def __init__(self, search_s=None, add_s=None, modify_s=None,
			     delete_s=None):
		self.search_s = search_s
		self.add_s = add_s
		self.modify_s = modify_s
		self.delete_s = delete_s

class Creation(object):
	@pyspec.context(group=1)
	def a_model_with_all_attributes_without_lists(self):
		TestModel.connection = ConnectionStub()
		self.model = TestModel({
			'attribute1': 'someval1',
			'attribute2': 'someval2',
		})
	@pyspec.spec(group=1)
	def should_have_attribute1_assigend_correctly(self):
		pyspec.About(self.model.attribute1).should_equal('someval1')
	@pyspec.spec(group=1)
	def should_have_attribute2_assigend_correctly(self):
		pyspec.About(self.model.attribute2).should_equal('someval2')

	@pyspec.context(group=2)
	def a_model_only_one_attribute_without_lists(self):
		TestModel.connection = ConnectionStub()
		self.model = TestModel({
			'attribute1': 'someval1',
		})
	@pyspec.spec(group=2)
	def should_have_attribute1_assigend_correctly(self):
		pyspec.About(self.model.attribute1).should_equal('someval1')
	@pyspec.spec(group=2)
	def should_have_attribute2_assigend_correctly(self):
		pyspec.About(self.model.attribute2).should_equal('')

	@pyspec.context(group=3)
	def a_model_with_only_one_attribute_with_lists(self):
		TestModel.connection = ConnectionStub()
		self.model = TestModel({
			'attribute1': [ 'someval1' ],
		})
	@pyspec.spec(group=3)
	def should_have_attribute1_assigend_correctly(self):
		pyspec.About(self.model.attribute1).should_equal('someval1')
	@pyspec.spec(group=3)
	def should_have_attribute2_assigend_correctly(self):
		pyspec.About(self.model.attribute2).should_equal('')

class FindAll(object):
	@pyspec.context(group=1)
	def model_with_two_classes_and_no_results(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(objectClass=klass2))'
		), [])
		TestModel.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.replay()
		self.result = TestModel.find_all()
	
	@pyspec.spec(group=1)
	def should_return_an_empty_list(self):
		pyspec.About(self.result).should_equal([])
	@pyspec.spec(group=1)
	def should_make_the_correct_call(self):
		self.controller.verify()

	@pyspec.context(group=2)
	def model_with_one_class_and_some_results(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1))'
		), test_data)
		TestModel2.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.replay()
		self.result = TestModel2.find_all()

	@pyspec.spec(group=2)
	def should_return_2_models(self):
		pyspec.About(len(self.result)).should_equal(2)
	@pyspec.spec(group=2)
	def should_create_the_right_models(self):
		model1, model2 = self.result
		pyspec.About(model1.attribute1).should_equal('someval1')
		pyspec.About(model1.attribute2).should_equal('someval2')
		pyspec.About(model2.attribute1).should_equal('someval3')
		pyspec.About(model2.attribute2).should_equal('someval4')
	@pyspec.spec(group=2)
	def should_make_the_correct_call(self):
		self.controller.verify()

class Find(object):
	@pyspec.context(group=1)
	def model_with_two_classes_and_no_results(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(objectClass=klass2)(attribute2=someid))'
		), [])
		TestModel.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.replay()
		self.result = TestModel.find('(attribute2=someid)')
	@pyspec.spec(group=1)
	def should_return_an_empty_list(self):
		pyspec.About(self.result).should_equal([])
	@pyspec.spec(group=1)
	def should_make_the_right_call(self):
		self.controller.verify()

	@pyspec.context(group=2)
	def model_with_one_class_and_a_result(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(attribute2=someid))'
		), test_data)
		TestModel2.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.replay()
		self.result = TestModel2.find('(attribute2=someid)')
	@pyspec.spec(group=2)
	def should_return_a_list_of_size_2(self):
		pyspec.About(len(self.result)).should_equal(2)
	@pyspec.spec(group=2)
	def should_make_the_right_call(self):
		self.controller.verify()

class FindById(object):
	@pyspec.context(group=1)
	def model_with_two_classes_and_no_results(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(objectClass=klass2)(attribute1=someid))'
		), [])
		TestModel.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.replay()
		self.result = TestModel.find_by_id('someid')
	@pyspec.spec(group=1)
	def should_find_data_per_id(self):
		self.controller.verify()
	@pyspec.spec(group=1)
	def should_return_none(self):
		pyspec.About(self.result).should_equal(None)

	@pyspec.context(group=2)
	def model_with_one_class_and_one_result(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		TestModel2.connection = ConnectionStub(search_s=self.search_s_mock)
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(attribute1=someid))'
		), test_data)
		self.controller.replay()
		self.result = TestModel2.find_by_id('someid')
	@pyspec.spec(group=2)
	def should_find_data_per_id(self):
		self.controller.verify()
	@pyspec.spec(group=2)
	def should_return_the_first_element(self):
		pyspec.About(self.result.attribute1).should_equal('someval1')
		pyspec.About(self.result.attribute2).should_equal('someval2')

class Save(object):
	@pyspec.context(group=1)
	def a_model_which_dont_exists(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(objectClass=klass2)(attribute1=testattr1))'
		), [])
		self.add_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.add_s_mock(
			'attribute1=testattr1,ou=user,o=schule', [
			('attribute1', 'testattr1'),
			('attribute2', 'testattr2'),
			('objectClass', [ 'klass1', 'klass2' ]),
		]), None)
		TestModel.connection = ConnectionStub(
			search_s=self.search_s_mock,
			add_s=self.add_s_mock
		)
		self.model = TestModel({
			'attribute1': 'testattr1',
			'attribute2': 'testattr2',
		})
		self.controller.replay()
		self.result = self.model.save()
		
	@pyspec.spec(group=1)
	def should_create_the_object(self):
		self.controller.verify()

	@pyspec.context(group=2)
	def a_model_which_exists(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(objectClass=klass2)(attribute1=testattr1))'
		), test_data)
		self.modify_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.modify_s_mock(
			'attribute1=testattr1,ou=user,o=schule', [
			(ldap.MOD_REPLACE, 'attribute1', 'testattr1'),
			(ldap.MOD_REPLACE, 'attribute2', 'testattr2'),
			(ldap.MOD_REPLACE, 'objectClass', [ 'klass1', 'klass2' ]),
		]), None)
		TestModel.connection = ConnectionStub(
			search_s=self.search_s_mock,
			modify_s=self.modify_s_mock
		)
		self.model = TestModel({
			'attribute1': 'testattr1',
			'attribute2': 'testattr2',
		})
		self.controller.replay()
		self.result = self.model.save()
		
	@pyspec.spec(group=2)
	def should_update_the_object(self):
		self.controller.verify()

class Delete(object):
	@pyspec.context(group=1)
	def a_model(self):
		self.controller = pymock.Controller()
		self.delete_s_mock = self.controller.mock()
		self.controller.expectAndReturn(
			self.delete_s_mock('attribute1=val1,ou=user,o=schule'), None
		)
		TestModel.connection = ConnectionStub(delete_s=self.delete_s_mock)
		self.controller.replay()
		self.model = TestModel({
			'attribute1': 'val1',
			'attribute2': 'val2',
		})
		self.result = self.model.delete()

	@pyspec.spec(group=1)
	def should_delete_the_model(self):
		self.controller.verify()

	@pyspec.context(group=2)
	def a_delete_statement(self):
		self.controller = pymock.Controller()
		self.delete_s_mock = self.controller.mock()
		self.controller.expectAndReturn(
			self.delete_s_mock('attribute1=val1,ou=user,o=schule'), None
		)
		TestModel.connection = ConnectionStub(delete_s=self.delete_s_mock)
		self.controller.replay()
		self.result = TestModel.delete_by_id('val1')
	@pyspec.spec(group=2)
	def should_delete_the_model(self):
		self.controller.verify()

class HasMany(object):
	@pyspec.context(group=1)
	def a_has_many_relationship(self):
		self.controller = pymock.Controller()
		self.search_s_mock = self.controller.mock()
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass1)(attribute1=tester))'
		), test_data)
		self.controller.expectAndReturn(self.search_s_mock(
			'ou=user,o=schule',
			ldap.SCOPE_SUBTREE,
			'(&(objectClass=klass4)(attribute1=tester))'
		), test_data[-1:])
		stub = ConnectionStub(search_s=self.search_s_mock)
		TestModel2.connection = stub
		TestModel3.connection = stub
		self.controller.replay()
		self.model3 = TestModel3({
			'attribute1': 'tester',
			'attribute2': 'blub',
		})
		self.model2 = TestModel2({
			'attribute1': 'tester',
			'attribute2': 'hoho',
		})
		self.result1 = self.model3.test_model
		self.result2 = self.model2.testmodel3s
	@pyspec.spec(group=1)
	def should_be_correct(self):
		self.controller.verify()
	@pyspec.spec(group=1)
	def should_return_the_first_user(self):
		pyspec.About(self.result1.__class__).should_equal(TestModel2)
		pyspec.About(self.result1.attribute1).should_equal('someval1')
		pyspec.About(self.result1.attribute2).should_equal('someval2')
	@pyspec.spec(group=1)
	def should_return_the_second_users(self):
		pyspec.About(self.result2.__class__).should_equal(list)
		pyspec.About(self.result2[0].attribute1).should_equal('someval3')

if __name__ == '__main__':
	pyspec.run_test()
