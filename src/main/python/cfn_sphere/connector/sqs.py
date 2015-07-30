from boto import sqs
import logging


class SqsQueue(object):

    def __init__(self, region="eu-west-1"):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        logging.getLogger('boto').setLevel(logging.ERROR)

        self.conn = sqs.connect_to_region(region)
        self.queue = self._get_queue_instance("is24-cfn-custom-resources")

    def _get_queue_instance(self, name):
        return self.conn.get_queue(name)

    def get_attributes(self):
        return self.conn.get_queue_attributes(self.queue)

    def get_messages(self):
        return self.conn.receive_message(self.queue, wait_time_seconds=20, number_messages=10)

    def delete_message(self, message):
        return self.conn.delete_message(self.queue, message)

    def delete_messages(self, messages):
        return self.conn.delete_message_batch(self.queue, messages)

if __name__ == "__main__":
    sqs = SqsQueue()
    messages = sqs.get_messages()
    print vars(messages[0])
    print type(messages[0])