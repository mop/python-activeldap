"""
This module includes all necessary classes for the usage of the signals-package
"""
class Sender(object):
	"""
	This class represents a sender which is able to send events to registered
	callbacks.
	"""
	
	def get_callbacks(self):
		"""
		Returns the callbacks. If the attribute is not existing it will be
		initialized.
		"""
		if not hasattr(self, '_callbacks'):
			self._callbacks = {}
		return self._callbacks

	def set_callbacks(self, callbacks):
		"""
		Sets the callbacks
		"""
		self._callbacks = callbacks

	callbacks = property(get_callbacks, set_callbacks)

	def get_catchall_callbacks(self):
		"""
		Returns a list of callbacks which should be called everytime a new
		event occured.
		"""
		if not hasattr(self, '_catchall_callbacks'):
			self._catchall_callbacks = []
		return self._catchall_callbacks
	
	def set_catchall_callbacks(self, callbacks):
		"""
		Sets the list of callbacks which should be called everytime a new event
		occured.
		"""
		self._catchall_callbacks = callbacks

	catchall_callbacks = property(
		get_catchall_callbacks, set_catchall_callbacks
	)
		
	
	def register(self, event, callback):
		"""
		Registers a callback for a given event.
		
		event -- the event for which the callback should be registered
		callback -- the callback itself, which should be called if the event
		occured.
		"""
		if event == '__all__':
			self.catchall_callbacks.append(callback)
			return
		self.callbacks.setdefault(event, []).append(callback)
		
	def notify(self, event, *messages):
		"""
		Notifies all callbacks, which are registered for the given event and
		sends them the given message.
		
		event -- the event which occured
		message -- the message which should be send
		"""
		for callback in self.catchall_callbacks:
			callback(event, *messages)
		if event not in self.callbacks:
			return
		for callback in self.callbacks[event]:
			callback(event, *messages)

	def unregister(self, event, callback):
		"""
		Unregisters the callback for the given event
		
		event -- the event for which the callback should be unregistered
		callback -- the callback which should be removed
		"""
		if event == '__all__':
			self.catchall_callbacks.remove(callback)
			return
		if event not in self.callbacks:
			return
		self.callbacks[event].remove(callback)
	
class SenderDelegator(object):
	"""
	This class tries to call methods on subclasses if they have the same name
	as the occured events.
	"""
	
	def __init__(self, sender):
		"""
		Intializes the delegate mixin
		
		sender -- the sender-object which will emit the events
		"""
		sender.register('__all__', self._event_received)
	
	def _event_received(self, event, *messages):
		"""
		This method is called if a event was received. It tries to find methods
		with the same name as the event on the item which sent the message and
		calls them. The first element in the messages-array _must_ therefore be
		the object whose methods should be called.
		
		event -- the received event.
		messages -- the received messages.
		"""
		obj = messages[0]
		if hasattr(obj, event):
			getattr(obj, event)(*messages[1:])

def send_event(func):
	"""
	This decorator emits an event before the encapsulated function is called
	and after the encapsulated function is called. The event has the name
	before_<function_name> and after_<function_name>. The encapsulated function
	_must_ be a instance-method, or maybe a class-method, otherwise the
	automatic dispatch-mechanism with the Sendable metaclass will probably 
	fail.
	"""
	def new_fun(self, *args, **kwds):
		before_name = 'before_%s' % func.__name__
		after_name  = 'after_%s' % func.__name__

		self.events.notify(before_name, self)
		result = func(self, *args, **kwds)
		self.events.notify(after_name, self)

		return result
	return new_fun

class Sendable(type):
	"""
	This metaclass adds a events-attribute to the class and creates a
	_delegator attribute. With the events-attribute events can be created and
	callbacks registered on the class. The SenderDelegator is responsible for
	invoking methods in subclasses which have the same name as the received
	events.
	The notified events _must_ have as first message-parameter the 
	object which sends the events. 
		e.g.:
		# in base
		def save(self):
			self.events.notify('before_save', self, 'arg1', 'arg2')

		# in child:
		def before_save(self):
			print 'before save!'
	"""
	
	def __init__(cls, name, bases, dct):
		super(Sendable, cls).__init__(name, bases, dct)
		cls.events = Sender()
		cls._delegator = SenderDelegator(cls.events)
