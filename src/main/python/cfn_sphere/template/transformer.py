from six import string_types

from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateTransformer(object):
    @classmethod
    def transform_template(cls, template):
        conditions = template.conditions
        resources = template.resources
        outputs = template.outputs

        conditions = cls.scan_dict_values(conditions, cls.transform_reference_string)
        conditions = cls.scan_dict_values(conditions, cls.transform_getattr_string)
        conditions = cls.scan_dict_keys(conditions, cls.transform_join_key)
        conditions = cls.scan_dict_keys(conditions, cls.transform_taupage_user_data_key)
        conditions = cls.scan_dict_keys(conditions, cls.transform_yaml_user_data_key)
        conditions = cls.scan_dict_values(conditions, cls.check_for_leftover_reference_values)
        conditions = cls.scan_dict_keys(conditions, cls.check_for_leftover_reference_keys)

        resources = cls.scan_dict_values(resources, cls.transform_reference_string)
        resources = cls.scan_dict_values(resources, cls.transform_getattr_string)
        resources = cls.scan_dict_keys(resources, cls.transform_join_key)
        resources = cls.scan_dict_keys(resources, cls.transform_taupage_user_data_key)
        resources = cls.scan_dict_keys(resources, cls.transform_yaml_user_data_key)
        resources = cls.scan_dict_values(resources, cls.check_for_leftover_reference_values)
        resources = cls.scan_dict_keys(resources, cls.check_for_leftover_reference_keys)

        outputs = cls.scan_dict_values(outputs, cls.transform_reference_string)
        outputs = cls.scan_dict_values(outputs, cls.transform_getattr_string)
        outputs = cls.scan_dict_keys(outputs, cls.transform_join_key)
        outputs = cls.scan_dict_keys(outputs, cls.transform_taupage_user_data_key)
        outputs = cls.scan_dict_keys(outputs, cls.transform_yaml_user_data_key)
        outputs = cls.scan_dict_values(outputs, cls.check_for_leftover_reference_values)
        outputs = cls.scan_dict_keys(outputs, cls.check_for_leftover_reference_keys)

        template.conditions = conditions
        template.resources = resources
        template.outputs = outputs

        return template

    @staticmethod
    def check_for_leftover_reference_values(value):
        if isinstance(value, list):
            for item in value:
                if item.startswith('|'):
                    raise TemplateErrorException("Unhandled reference value found: {0}".format(value))
        elif isinstance(value, string_types):
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

        if isinstance(key, string_types):

            if str(key).lower() == '@taupageuserdata@':

                if not isinstance(value, dict):
                    raise TemplateErrorException("Value of 'TaupageUserData' must be of type dict")

                lines = ['#taupage-ami-config']
                lines.extend(cls.transform_dict_to_yaml_lines_list(value))

                return "UserData", {
                    'Fn::Base64': {
                        'Fn::Join': ['\n', lines]
                    }
                }

        return key, value

    @classmethod
    def transform_yaml_user_data_key(cls, key, value):
        if not value:
            return key, value

        if isinstance(key, string_types):

            if str(key).lower() == '@yamluserdata@':

                if not isinstance(value, dict):
                    raise TemplateErrorException("Value of 'YamlUserData' must be of type dict")

                lines = cls.transform_dict_to_yaml_lines_list(value)

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

        if isinstance(key, string_types):
            if key.lower().startswith('|join|'):
                if not isinstance(value, list):
                    raise TemplateErrorException("Value of '|join|' must be of type list")

                join_string = key[6:]

                return 'Fn::Join', [join_string, value]

        return key, value

    @staticmethod
    def transform_kv_to_cfn_join(key, value):
        if isinstance(value, string_types) and ':' in key:
            key = "'{0}'".format(key)

        if isinstance(value, string_types) and ':' in value:
            value = "'{0}'".format(value)

        return {'Fn::Join': [': ', [key, value]]}

    @staticmethod
    def transform_reference_string(value):
        if not value:
            return value

        if isinstance(value, string_types):
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

        if isinstance(value, string_types):
            if value.lower().startswith('|getatt|'):
                elements = value.split('|', 3)

                if len(elements) != 4:
                    raise TemplateErrorException("Attribute reference must be like '|getatt|resource|attribute'")

                resource = elements[2]
                attribute = elements[3]

                return {'Fn::GetAtt': [resource, attribute]}

        return value

    @classmethod
    def transform_dict_to_yaml_lines_list(cls, userdata_dict, indentation_level=0):
        lines = []

        for key, value in sorted(userdata_dict.items()):

            # key indentation with two spaces
            if indentation_level > 0:
                indented_key = '  ' * indentation_level + str(key)
            else:
                indented_key = key

            if isinstance(key, string_types):

                # do not go any further and directly return cfn functions and their values
                if key.lower() in ['ref', 'fn::getatt', 'fn::join']:
                    return {key: value}
                else:

                    # recursion for dict values
                    if isinstance(value, dict):
                        result = cls.transform_dict_to_yaml_lines_list(value, indentation_level + 1)
                        if isinstance(result, dict):
                            lines.append(cls.transform_kv_to_cfn_join(indented_key, result))
                        elif isinstance(result, list):
                            lines.append(indented_key + ':')
                            lines.extend(result)
                        else:
                            raise TemplateErrorException("Failed to convert dict to list of lines")
                    elif isinstance(value, list):
                        lines.extend([indented_key + ':'] + ['- {0}'.format(item) for item in value])

                    else:
                        lines.append(cls.transform_kv_to_cfn_join(indented_key, value))
            else:
                lines.append(cls.transform_kv_to_cfn_join(indented_key, value))

        return lines

    @classmethod
    def scan_dict_keys(cls, original_dict, key_handler):
        result_dict = {}

        for key, value in original_dict.items():
            if isinstance(value, dict):
                new_dict_value = cls.scan_dict_keys(value, key_handler)
                new_key, new_value = key_handler(key, new_dict_value)
                result_dict[new_key] = new_value

            elif isinstance(value, list):
                new_list_value = []

                for item in value:
                    if isinstance(item, dict):
                        new_list_value.append(cls.scan_dict_keys(item, key_handler))
                    else:
                        new_list_value.append(item)

                new_key, new_value = key_handler(key, new_list_value)
                result_dict[new_key] = new_value

            else:
                new_key, new_value = key_handler(key, value)
                result_dict[new_key] = new_value

        return result_dict

    @classmethod
    def scan_dict_values(cls, original_dict, value_handler):
        result_dict = {}

        for key, value in original_dict.items():
            if isinstance(value, dict):
                result_dict[key] = cls.scan_dict_values(value, value_handler)

            elif isinstance(value, list):
                new_list_value = []
                for item in value:
                    if isinstance(item, dict):
                        new_list_value.append(cls.scan_dict_values(item, value_handler))
                    elif isinstance(item, string_types):
                        new_list_value.append(value_handler(item))
                    else:
                        new_list_value.append(item)

                result_dict[key] = new_list_value

            elif isinstance(value, string_types):
                result_dict[key] = value_handler(value)
            else:
                result_dict[key] = value

        return result_dict


if __name__ == "__main__":
    template = CloudFormationTemplateTransformer
