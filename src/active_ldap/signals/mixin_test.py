from signals import Sender, send_event, SenderDelegator, Sendable
from mixin import mixin

class Base(object):
	"""
	This class represents a base
	"""
	__metaclass__ = Sendable

	def __init__(self, ):
		"""
		Constructor.
		"""
		print 'base'

class Child(Base):
	"""
	This class represents a child
	"""

	def __init__(self, ):
		"""
		Constructor.
		"""
		print 'child'
		super(Child, self).__init__()
	
	@send_event
	def something(self, arg1, arg2):
		"""
		something
		"""
		print 'in-something'

	def after_something(self):
		print 'after-custom-something!!'

	def before_something(self):
		print 'before-custom-something!!'

c = Child()
print c.events
c2 = Child()
print c2.events
c2.something('a', 'b')
c2.something('a', 'b')
