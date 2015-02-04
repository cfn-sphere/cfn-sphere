__author__ = 'mhoyer'

from cfn_sphere.stack_config import StackConfig


class StackHandler(object):

    def __init__(self):
        self.stacks = StackConfig("resources/stacks.yml").get()

    def sync(self):
        for name, data in self.stacks.iteritems():
            print name
            print data


if __name__ == "__main__":
    stack_handler = StackHandler()
    stack_handler.sync()