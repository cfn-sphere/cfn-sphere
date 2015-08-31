from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateTransformer(object):
    @classmethod
    def transform_template(cls, template):
        template_dict = template.body_dict

        template_dict = cls.transform_dict_values(template_dict, cls.transform_reference_string)
        template_dict = cls.transform_dict_values(template_dict, cls.transform_getattr_string)
        template_dict = cls.transform_dict_keys(template_dict, {'@TaupageUserData@': cls.render_taupage_user_data})

        template.body_dict = template_dict
        return template

    @classmethod
    def render_taupage_user_data(cls, taupage_user_data_dict):
        if not isinstance(taupage_user_data_dict, dict):
            raise TemplateErrorException("Value of 'TaupageUserData' must be of type dict")

        lines = ['#taupage-ami-config']
        lines.extend(cls.transform_userdata_dict(taupage_user_data_dict))

        return "UserData", {
            'Fn::Base64': {
                'Fn::Join': ['\n', lines]
            }
        }

    @staticmethod
    def transform_kv_to_cfn_join(key, value):
        return {'Fn::Join': [': ', [key, value]]}

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
    def transform_userdata_dict(cls, userdata_dict, level=0):
        parameters = []

        for key, value in userdata_dict.items():
            # key indentation
            if level > 0:
                key = '  ' * level + str(key)

            # recursion for dict values
            if isinstance(value, dict):
                parameters.extend(cls.transform_userdata_dict(value, level + 1))
                parameters.append(key + ':')

            elif isinstance(value, str):
                if value.lower().startswith('|ref|'):
                    value = cls.transform_reference_string(value)
                elif value.lower().startswith('|getatt|'):
                    value = cls.transform_getattr_string(value)

                parameters.append(cls.transform_kv_to_cfn_join(key, value))

            else:
                parameters.append(cls.transform_kv_to_cfn_join(key, value))

        parameters.reverse()
        return parameters

    @classmethod
    def transform_dict_keys(cls, dictionary, key_handlers):
        for key in dictionary:
            value = dictionary[key]
            if isinstance(value, dict):
                cls.transform_dict_keys(value, key_handlers)

            key_handler = key_handlers.get(key, None)
            if key_handler:
                new_key, new_value = key_handler(value)
                dictionary[new_key] = new_value
                dictionary.pop(key)

        return dictionary

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
