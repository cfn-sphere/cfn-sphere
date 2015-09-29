from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateTransformer(object):
    @classmethod
    def transform_template(cls, template):
        template_dict = template.body_dict

        template_dict = cls.transform_dict_values(template_dict, cls.transform_reference_string)
        template_dict = cls.transform_dict_values(template_dict, cls.transform_getattr_string)
        template_dict = cls.transform_dict_keys(template_dict, cls.transform_join_key)
        template_dict = cls.transform_dict_keys(template_dict, cls.transform_taupage_user_data_key)

        template_dict = cls.transform_dict_values(template_dict, cls.check_for_leftover_reference_values)
        template_dict = cls.transform_dict_keys(template_dict, cls.check_for_leftover_reference_keys)

        template.body_dict = template_dict
        return template

    @staticmethod
    def check_for_leftover_reference_values(value):
        if isinstance(value, list):
            for item in value:
                if item.startswith('|'):
                    raise TemplateErrorException("Unhandled reference value found: {0}".format(value))
        elif isinstance(value, basestring):
            if value.startswith('|'):
                raise TemplateErrorException("Unhandled reference value found: {0}".format(value))

        return value

    @staticmethod
    def check_for_leftover_reference_keys(key, value):
        if key.startswith('|'):
            raise TemplateErrorException("Unhandled reference key found: {0}".format(key))
        if key.startswith('@') and key.endswith('@'):
            raise TemplateErrorException("Unhandled reference key found: {0}".format(key))

        return key, value

    @classmethod
    def transform_taupage_user_data_key(cls, key, value):
        if not value:
            return key, value

        if isinstance(key, basestring):

            if str(key).lower() == '@taupageuserdata@':

                if not isinstance(value, dict):
                    raise TemplateErrorException("Value of 'TaupageUserData' must be of type dict")

                lines = ['#taupage-ami-config']
                lines.extend(cls.transform_userdata_dict_to_lines_list(value))

                return "UserData", {
                    'Fn::Base64': {
                        'Fn::Join': ['\n', lines]
                    }
                }

        return key, value

    @classmethod
    def transform_join_key(cls, key, value):
        if not value:
            return key, value

        if isinstance(key, basestring):
            if key.lower().startswith('|join|'):
                if not isinstance(value, list):
                    raise TemplateErrorException("Value of '|join|' must be of type list")

                join_string = key[6:]

                return 'Fn::Join', [join_string, value]

        return key, value

    @staticmethod
    def transform_kv_to_cfn_join(key, value):
        if isinstance(value, basestring) and ':' in key:
            key = "'{0}'".format(key)

        if isinstance(value, basestring) and ':' in value:
            value = "'{0}'".format(value)

        return {'Fn::Join': [': ', [key, value]]}

    @staticmethod
    def transform_reference_string(value):
        if not value:
            return value

        if isinstance(value, basestring):
            if value.lower().startswith('|ref|'):
                referenced_value = value[5:]

                if not referenced_value:
                    raise TemplateErrorException("Reference must be like |ref|resource")

                return {'Ref': referenced_value}

        return value

    @staticmethod
    def transform_getattr_string(value):
        if not value:
            return value

        if isinstance(value, basestring):
            if value.lower().startswith('|getatt|'):
                elements = value.split('|', 3)

                if len(elements) != 4:
                    raise TemplateErrorException("Attribute reference must be like '|getatt|resource|attribute'")

                resource = elements[2]
                attribute = elements[3]

                return {'Fn::GetAtt': [resource, attribute]}

        return value

    @classmethod
    def transform_userdata_dict_to_lines_list(cls, userdata_dict, indentation_level=0):
        lines = []

        for key, value in userdata_dict.items():

            # key indentation with two spaces
            if indentation_level > 0:
                indented_key = '  ' * indentation_level + str(key)
            else:
                indented_key = key

            if isinstance(key, basestring):

                # do not go any further and directly return cfn functions and their values
                if key.lower() == 'ref' or key.lower() == 'fn::getatt' or key.lower() == 'fn::join':
                    return {key: value}
                else:

                    # recursion for dict values
                    if isinstance(value, dict):

                        result = cls.transform_userdata_dict_to_lines_list(value, indentation_level + 1)

                        if isinstance(result, dict):
                            lines.append(cls.transform_kv_to_cfn_join(indented_key, result))
                        elif isinstance(result, list):
                            result.reverse()
                            lines.extend(result)
                            lines.append(indented_key + ':')
                        else:
                            raise TemplateErrorException("Failed to convert user-data dict to list of lines")

                    else:
                        lines.append(cls.transform_kv_to_cfn_join(indented_key, value))
            else:
                lines.append(cls.transform_kv_to_cfn_join(indented_key, value))

        lines.reverse()
        return lines

    @classmethod
    def transform_dict_keys(cls, dictionary, key_handler):
        for key in dictionary:
            value = dictionary[key]

            if isinstance(value, dict):
                dictionary[key] = cls.transform_dict_keys(value, key_handler)

            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        cls.transform_dict_keys(item, key_handler)

            new_key, new_value = key_handler(key, value)

            if new_key != key or new_value != value:
                dictionary[new_key] = new_value

            if new_key != key:
                dictionary.pop(key)

        return dictionary

    @classmethod
    def transform_dict_values(cls, dictionary, value_handler):
        for key in dictionary:
            value = dictionary[key]

            if isinstance(value, dict):
                dictionary[key] = cls.transform_dict_values(value, value_handler)

            elif isinstance(value, list):
                value_list = []
                for item in value:
                    if isinstance(item, dict):
                        value_list.append(cls.transform_dict_values(item, value_handler))
                    elif isinstance(item, basestring):
                        value_list.append(value_handler(item))
                    else:
                        value_list.append(item)

                dictionary[key] = value_list

            elif isinstance(value, basestring):
                dictionary[key] = value_handler(value)
            else:
                dictionary[key] = value

        return dictionary


if __name__ == "__main__":
    template = CloudFormationTemplateTransformer
