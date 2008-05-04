def mixin(py_class, mixin_class, make_last=False):
	"""
	Mixes the mixin_class into the py_class. If make_last is False the mixin is
	inserted before the bases, otherwise after the bases
	
	py_class -- the python class
	mixin_class -- the mixin class
	make_last -- if False the mixin is inserted after the bases
	"""
	if make_last:
		py_class.__bases__ += (mixin_class, )
	else:
		py_class.__bases__ = (mixin_class, ) + py_class.__bases__
