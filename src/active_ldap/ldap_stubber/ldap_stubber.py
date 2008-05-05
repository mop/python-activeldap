import ldap
import re

# Parses ()-expressions
def parse_expression(string):
	stack = 0
	lists = []
	start = -1
	for i, elem in enumerate(string):
		if elem == '(' and stack == 0:
			start = i
		if elem == ')' and stack == 1:
			lists.append(string[start:i+1])
		if elem == '(':
			stack = stack + 1
		if elem == ')':
			stack = stack - 1
	return lists


class LdapElement(object):
	"""
	This class represents an element within the directory
	"""

	parenthesis = re.compile(r'\(([\||\&])?(.*)\)')
	nodes = re.compile(r'(\(.*?\))')

	def __init__(self, dn, attrs):
		"""
		Constructor.

		dn -- the distinguished name for the element
		attrs -- a list of tuples which contains the attribute and the value
		"""
		self.dn = dn
		self.attributes = []
		for attr, value in attrs:
			self._append_attribute(attr)
			if not isinstance(value, list):
				value = [ value ]
			setattr(self, attr, value)

	def __repr__(self):
		return '<LdapStubber %s>' % self.dn

	def modify(self, attrs):
		"""
		Modifies the element
		
		attrs -- a list of tuples with the attributes which should be modified
		"""
		for op, attr, val in attrs:
			self._append_attribute(attr)
			if not isinstance(val, list):
				val = [ val ]
			self.operation_mappings[op](self, attr, val)

	def modrdn(self, rdn):
		"""
		Modifies the DN of the attribute
		
		rdn -- the new relative distinguisher
		"""
		attr, val = rdn.split('=')
		if hasattr(self, attr):
			setattr(self, attr, [ val ])
		self.dn = re.sub(r'.*?,', "%s," % rdn, self.dn, 1)

	def matches(self, filter):
		"""
		Returns true if the element matches the given filter
		
		filter -- a LDAP-Filter expression
		"""
		ops = [ '&', '|' ]
		match = self.parenthesis.match(filter).groups()
		op = '&'
		if match[0]:
			op = match[0]
		match = match[1:]
		rv = self._init_for_op(op)
		for i in match:
			rv = self._combine(op, rv, self._handle_element(op, i))
		return rv

	def has_prefix(self, prefix, scope=ldap.SCOPE_SUBTREE):
		"""
		Returns true if the element has the given prefix
		
		prefix -- the ldap-prefix of the object
		scope -- the scope of the search operation
		"""
		if scope == ldap.SCOPE_SUBTREE:
			return self.dn.endswith(prefix)
		return re.sub(r'.*?,', '', self.dn, 1) == prefix

	def to_result(self):
		"""
		Converts the object back to a ldap-result
		"""
		return ( self.dn, self._result_dict() )
	
	###########################################################################
	# Helper methods
	###########################################################################
	def _result_dict(self):
		"""
		Returns all attributes as a dictionary.
		"""
		dict = {}
		for attr in self.attributes:
			dict[attr] = getattr(self, attr)
		return dict

	def _combine(self, op, val1, val2):
		"""
		Combines the given values with the given operator.

		op -- either & or |
		val1 -- the first boolean value
		val2 -- the second boolean value
		"""
		if op == '&':
			return val1 and val2
		if op == '|':
			return val1 or val2

	def _init_for_op(self, op):
		"""
		Returns the initial combination-value for the given operator

		op -- the operator 
		"""
		if op == '&': 
			return True
		return False

	def _handle_nodes(self, op, match):
		"""
		Handles elements like '(attr1=b)(attr2=c)'. It splits those elements up
		and calls for each filter-element recursively the matches-method.

		op -- the operator
		match -- the filter expression
		"""
		nodes = parse_expression(match)
		rv = self._init_for_op(op)
		for node in nodes:
			rv = self._combine(op, rv, self.matches(node))
		return rv
	
	def _handle_attribute(self, op, match):
		"""
		Handles regular filter expressions like attr1=value.

		op -- the operator
		match -- the filter expression
		"""
		try:
			attr, val = match.split('=')
			return val in getattr(self, attr)
		except:
			return False
	
	def _handle_element(self, op, match):
		"""
		Handles an filter-expression element like (attr1=value1)(attr2=value2)
		or attr1=value1.
		It returns either true or false if the elements are matching or not.

		op -- is the operator which should be used for combining the elements
		match -- is the filter sub-expression
		"""
		# an element like (attr1=b)(attr2=c) is given. Thus we are splitting
		# those elements up and calling matches recursively
		if '(' in match:
			return self._handle_nodes(op, match)
		# normal handling of elements
		return self._handle_attribute(op, match)
	
	def _add(self, attr, val):
		"""
		Adds a new value to the list
		
		attr -- the attribute which should be modified
		val -- the value which should be added
		"""
		if not hasattr(self, attr):
			setattr(self, attr, [])

		list = getattr(self, attr)
		list += val
		setattr(self, attr, list)
	
	def _replace(self, attr, val):
		"""
		Replaces the entire values of the given attribute with the new values
		
		attr -- The attribute
		"""
		if not isinstance(val, list):
			val = [ val ]
		setattr(self, attr, val)

	def _append_attribute(self, attr):
		"""
		Appends the given attribute to the internal list of attributes. If the
		attribute already exists within the list it won't be added.
		
		attr -- the name of the new attribute which should be added
		"""
		if attr not in self.attributes:
			self.attributes.append(attr)
		
	operation_mappings = {
		ldap.MOD_REPLACE: _replace,
		ldap.MOD_ADD: _add,
	}
			
		
				
class LdapStubber(object):
	"""
	This class is a helper for stubbing the ldap-object
	"""

	def __init__(self):
		self.elements = []

	def add_s(self, dn, attrs):
		"""
		Adds a new element to the Directory
		
		dn -- The DN for the element which should be added
		attrs -- The attributes which should be added
		"""
		self.elements.append(LdapElement(dn, attrs))
	
	def modify_s(self, dn, attrs):
		"""
		Modifies an ldap object
		
		dn -- the DN of the object
		attrs -- The new attributes
		"""
		element = self._find_element(dn)
		element.modify(attrs)
	
	def delete_s(self, dn):
		"""
		Deletes the element with the given dn from the directory
		
		dn -- the distinguished name of the element which should be deleted
		"""
		self.elements.remove(self._find_element(dn))

	def modrdn_s(self, dn, rdn, flag):
		"""
		Modifies the DN of the element.
		
		dn -- the full distinguished name of the element
		rdn -- the new RDN of the element
		flag -- True if the old element should be destroyed
		"""
		if flag == False:
			raise RuntimeError("Operation not supported")
		element = self._find_element(dn)
		element.modrdn(rdn)
	
	def search_s(self, prefix, scope, expr):
		result = filter(lambda i: i.has_prefix(prefix, scope), self.elements)
		result = filter(lambda i: i.matches(expr), result)
		return map(lambda i: i.to_result(), result)
	###########################################################################
	# Helper methods
	###########################################################################
	def _find_element(self, dn):
		"""
		Finds the element with the given DN and returns it. If no element was
		found or more than one element was found an Exception is risen.
		
		dn -- the DN of the element
		"""
		results = filter(lambda i: i.dn == dn, self.elements)
		if len(results) != 1:
			raise RuntimeError("No such element with the dn: %s" % dn)
		return results[0]
