
def load(filename, defaultConstructor):
	import main
	import os
	import pickle
	from TaskSystem import DoInMainthreadDecoratorNowait

	filename = main.RootDir + "/index.db"
	if os.path.exists(filename):
		obj = pickle.load(open(filename))
	else:
		obj = defaultConstructor()

	# Set obj.save() function.
	@DoInMainthreadDecoratorNowait
	def save():
		pickle.dump(obj, open(filename, "w"))
	obj.save = save

	return obj
