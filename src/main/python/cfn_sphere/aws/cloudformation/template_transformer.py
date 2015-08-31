from cfn_sphere.exceptions import TemplateErrorException

class CloudFormationTemplateTransformer(object):

    @classmethod
    def transform_template(cls, template):
        template_dict = template.body_dict

        template_dict = cls.transform_dict_values(template_dict, cls.transform_reference_string)
        template_dict = cls.transform_dict_values(template_dict, cls.transform_getattr_string)
        return template_dict

    @staticmethod
    def transform_reference_string(value):
        if not value:
            return value

        if value.lower().startswith('|ref|'):
            referenced_value = value[5:]

            if not referenced_value:
                raise TemplateErrorException("Reference must be like |ref|resource")

            return {'Ref': referenced_value}
        else:
            return value

    @staticmethod
    def transform_getattr_string(value):
        if not value:
            return value

        if value.lower().startswith('|getatt|'):
            elements = value.split('|', 3)

            if len(elements) != 4:
                raise TemplateErrorException("Attribute reference must be like '|getatt|resource|attribute'")

            resource = elements[2]
            attribute = elements[3]

            return {'Fn::GetAtt': [resource, attribute]}
        else:
            return value

    @classmethod
    def transform_dict_values(cls, dictionary, value_handler):
        for key in dictionary:
            value = dictionary[key]

            if isinstance(value, dict):
                dictionary[key] = cls.transform_dict_values(value, value_handler)
            if isinstance(value, basestring):
                dictionary[key] = value_handler(value)
            else:
                dictionary[key] = value

        return dictionary
