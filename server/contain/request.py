

class Request:

    def __init__(self, target):
        self.target = target

    def __getattr__(self, name):
        return getattr(self.target, name)

    def is_post(self):
        return self.target.method == 'POST'

    def is_get(self):
        return self.target.method == 'GET'
