from flask_restful import Resource, reqparse
from aws_updater.stack import StackUpdater


class Stack(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('region', type=str, help='Hostname of the instance', required=True)
        self.parser.add_argument('template', type=str, help='Fully qualified name', required=False)
        self.parser.add_argument('parameters', type=str, help='Fully qualified name', required=False)
        self.parser.add_argument('timeout', type=int, help='Timeout in seconds', required=True)

    def put(self, stack_id):
        args = self.parser.parse_args(strict=True)

        try:
            updater = StackUpdater(stack_id, args['region'], timeout_in_seconds=args['timeout'])
            updater.update_stack(args['parameters'], template_filename=args['template'])
            updater.update_asgs()
        except Exception as e:
            return "Stack update failed with error: {0}".format(e), 500

        return '', 201