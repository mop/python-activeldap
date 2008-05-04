import unittest
from signals import Sender

class AnNewSender(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.called = False

	def callback(self, event, arg):
		self.called = True

	def test_should_add_a_callback_on_register(self):
		self.sender.register('some_event', self.callback)
		self.assertEqual(len(self.sender.callbacks), 1)

	def test_should_have_zero_callbacks(self):
		self.assertEqual(len(self.sender.callbacks), 0)

	def test_should_not_call_anything_on_notify(self):
		self.sender.notify('some_event', 'msg')
		self.assertFalse(self.called)

	def test_should_not_raise_error_on_unregister(self):
		self.sender.unregister('some_event', self.callback)

class ASenderWithOneCallback(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.called = False
		self.sender.register('event', self.callback)
	
	def callback(self, event, arg):
		self.called = True

	def test_should_notify_if_the_registered_signal_was_called(self):
		self.sender.notify('event', 'message')
		self.assertTrue(self.called)

	def test_should_not_notify_if_another_signal_was_called(self):
		self.sender.notify('other_event', 'message')
		self.assertFalse(self.called)

	def test_should_remove_the_callback_on_unregister(self):
		self.sender.unregister('event', self.callback)
		self.sender.notify('event', 'message')
		self.assertFalse(self.called)

class ASenderWithTwoCallbacksForTheSameSignal(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.called = False
		self.called2 = self.called1 = False
		self.sender.register('event', self.callback1)
		self.sender.register('event', self.callback2)

	def callback1(self, event, arg):
		self.called1 = True

	def callback2(self, event, arg):
		self.called2 = True

	def test_should_notify_both_if_the_registered_signal_was_called(self):
		self.sender.notify('event', 'msg')
		self.assertTrue(self.called1)
		self.assertTrue(self.called2)

class ARegisteredCallbackOnASenderWhichReceivesAEvent(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.sender.register('event', self.callback)
		self.sender.notify('event', 'message')
	
	def callback(self, event, arg):
		self.event = event
		self.arg   = arg

	def test_should_receive_the_correct_event(self):
		self.assertEqual(self.event, 'event')
	
	def test_should_receive_the_correct_arguments(self):
		self.assertEqual(self.arg, 'message')

class ARegisteredCallbackWithMultipleArgsReceivesAEvent(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.sender.register('event', self.callback)
		self.sender.notify('event', 'message1', 'message2')
	
	def callback(self, event, arg1, arg2):
		self.event = event
		self.arg1  = arg1
		self.arg2  = arg2

	def test_should_receive_the_correct_event(self):
		self.assertEqual(self.event, 'event')
	
	def test_should_receive_message1(self):
		self.assertEqual(self.arg1, 'message1')
	
	def test_should_receive_message2(self):
		self.assertEqual(self.arg2, 'message2')

class ACallBackWhichRegisteredToThe__all__event(unittest.TestCase):
	def setUp(self):
		self.sender = Sender()
		self.sender.register('__all__', self.callback)
		self.called = False

	def callback(self, event, *messages):
		self.called = True
		
	def test_should_be_notified_on_a_test_event(self):
		self.sender.notify('test', 'msg')
		self.assertTrue(self.called)

	def test_should_be_notified_on_a_event_event(self):
		self.sender.notify('event', 'msg1', 'msg2')
		self.assertTrue(self.called)

if __name__ == '__main__':
	unittest.main()
