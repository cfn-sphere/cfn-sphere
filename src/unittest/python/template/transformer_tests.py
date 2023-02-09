import json

try:
    from unittest import TestCase
    from mock import Mock
except ImportError:
    from unittest import TestCase
    from mock import Mock

import mock

from cfn_sphere.exceptions import TemplateErrorException
from cfn_sphere.template import CloudFormationTemplate
from cfn_sphere.template.transformer import CloudFormationTemplateTransformer

DESCRIPTION_1000_CHARS = "V1nrIETxGEoaMZhfzYr3BTfjzIIguxW3aF0o24ggkyydnsYGQPe96uH8IjtnhAWziEYrharWhxP" \
                         "fEnlAd7kFG7x4yFz4cN3w79U1m5KsQOqTYicEIk1x87arcvIz0soxYdZ4fDsz1uq05cUzkz0mvX" \
                         "7oe2Zf4tUkBlc0FuPWoyITXbfEfTJVvjvDQiry2DQO7Hfv0vrNOzwLUY6nAz52rjJKBmB4lI7OE" \
                         "vn08ZWBTBBIzRTfAfdcpOfWnW7ekpmGfJZ13SRi8rvAPlP3PlOuKTJ08Lj0nwTj6jEA5JDsUrVF" \
                         "GHOEqnQ5M6bDv14irpt0VX5zRIf6Zf16jHBJTzNkNExld9PEnVey3IqNK10Ukg368fTIDdfAkgR" \
                         "3rFB4ZSNZqxG2WRDnyZ4X39hM4oO1g8GxeB3RVkOGOMmzrRZ7mbQiYuoVPTXD7HU3p686vCEO94" \
                         "DkSF9shH3B5twfCEGXrGfIa3APOXJ9E4OtA3BrBNblkxd8zingQhj8azqV6NJlbZoVkWUZBkJvb" \
                         "L4ECFYrlUifXw7gbQZIqm5eybUYSBtF4iFN3oncKAlE1s6pzLbMJ0pNJ0chMDHyaWyYYFlYZ3OV" \
                         "9O5h2QtEOvBgQciupLdRraoBMkF1uNFcB1w9VtylQbCKaOlKpIGdjYH2cL1TJGWOZPtm3dhmB2J" \
                         "Zf6zppaOVn9xeDM5haP6eSj9Lh9uzbKpCvjCIiuJGJtEZaHWb8iMm3ei7h7roZKA8oze3P07J7g" \
                         "e5IBZleyTQOyWDLzghgG5On3cgy6BAtnqwcz2hUetkczM5D0bPv2evnTNcxW3cfvo5LOL9pGIGU" \
                         "ZXRXzcjqiZ3SFVR6GoxbkS5T2ifRXfP8eq3m7OmNjZLlwAL821RExw23EuErVYmdy3D9qfqKqqq" \
                         "lfwvl8BOiGvvCHDW57QQnLefIecQSemhGZL8wqsfnNIY4TCIyZg7meXxJTi2iOOZYIoXrh42neK" \
                         "1fQNebEkWKskElr6QICH5TSIg"


class CloudFormationTemplateTransformerTests(TestCase):
    def test_extend_stack_description_extends_description(self):
        result = CloudFormationTemplateTransformer.extend_stack_description("my-description",
                                                                            "my-additional-description")
        self.assertEqual("my-description | my-additional-description", result)

    def test_extend_stack_description_limits_length(self):
        additional_description = "my-additional-description"

        expected_result = DESCRIPTION_1000_CHARS[:996] + " | " + additional_description
        result = CloudFormationTemplateTransformer.extend_stack_description(DESCRIPTION_1000_CHARS,
                                                                            additional_description)
        self.assertEqual(expected_result, result)
        self.assertEqual(1024, len(result))

    def test_extend_stack_description_does_not_cut_description(self):
        description = DESCRIPTION_1000_CHARS[:996]
        additional_description = "my-additional-description"

        expected_result = description + " | " + additional_description
        result = CloudFormationTemplateTransformer.extend_stack_description(description,
                                                                            additional_description)
        self.assertEqual(expected_result, result)
        self.assertEqual(1024, len(result))

    def test_scan_executes_key_handler_for_all_matching_keys(self):
        dictionary = {"|key|": "value"}
        handler = Mock()
        handler.return_value = "new-key", "new-value"

        result = CloudFormationTemplateTransformer.scan(dictionary, [handler], [])
        expected_calls = [mock.call("|key|", "value")]

        self.assertEqual(expected_calls, handler.mock_calls)
        self.assertEqual(result, {"new-key": "new-value"})

    def test_scan_executes_value_handler_for_all_matching_prefixes(self):
        dictionary = {"a": "foo123", "b": {"c": "foo234"}}
        handler = Mock()
        handler.return_value = "foo"

        result = CloudFormationTemplateTransformer.scan(dictionary, [], [handler])
        expected_calls = [mock.call("foo123"), mock.call("foo234")]

        self.assertEqual(sorted(expected_calls), sorted(handler.mock_calls))
        self.assertEqual(result, {"a": "foo", "b": {"c": "foo"}})

    def test_transform_dict_to_yaml_lines_list_with_simple_kv(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({"my-key": "my-value"})
        self.assertEqual(["my-key: 'my-value'"], result)

    def test_transform_dict_to_yaml_lines_list_indents_sub_dicts(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({"my-key": {"my-sub-key": "v"}})
        self.assertEqual(["my-key:", "  my-sub-key: 'v'"], result)

    def test_transform_dict_to_yaml_lines_list_accepts_integer_values(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({"my-key": 3})
        self.assertEqual(["my-key: 3"], result)

    # def test_transform_dict_to_yaml_lines_list_accepts_list_values(self):
    #     result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({"my-key": ["a", "b"]})
    #     self.assertEqual(["my-key:", "  - a", "  - b"], result)

    def test_transform_join_key_creates_valid_cfn_join(self):
        result = CloudFormationTemplateTransformer.transform_join_key("|join|-", ["a", "b"])
        self.assertEqual(("Fn::Join", ["-", ["a", "b"]]), result)

    def test_transform_join_key_accepts_empty_join_string(self):
        result = CloudFormationTemplateTransformer.transform_join_key("|join|", ["a", "b"])
        self.assertEqual(("Fn::Join", ["", ["a", "b"]]), result)

    def test_transform_join_key_creates_valid_cfn_join_with_multiple_strings(self):
        result = CloudFormationTemplateTransformer.transform_join_key("|join|-", ["a", "b", "c", "d", "e"])
        self.assertEqual(("Fn::Join", ["-", ["a", "b", "c", "d", "e"]]), result)

    def test_transform_include_key_creates_valid_include(self):
        result = CloudFormationTemplateTransformer.transform_include_key("|include|", "s3://myBucket/myTemplate.json")
        self.assertEqual(("Fn::Transform", {"Name": "AWS::Include", "Location": "s3://myBucket/myTemplate.json"}),
                         result)

    def test_transform_reference_string_creates_valid_cfn_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string("|ref|my-value")
        self.assertEqual({"Ref": "my-value"}, result)

    def test_transform_reference_string_ignores_value_without_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string("my-value")
        self.assertEqual("my-value", result)

    def test_transform_reference_string_raises_exception_on_empty_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_reference_string("|ref|")

    def test_transform_reference_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_reference_string(None)
        self.assertEqual(None, result)

    def test_transform_reference_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_reference_string("")
        self.assertEqual("", result)

    def test_transform_getattr_string_creates_valid_cfn_getattr(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string("|getatt|resource|attribute")
        self.assertEqual({"Fn::GetAtt": ["resource", "attribute"]}, result)

    def test_transform_getattr_string_raises_exception_on_missing_resource(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_getattr_string("|getatt|attribute")

    def test_transform_getattr_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string(None)
        self.assertEqual(None, result)

    def test_transform_getattr_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string("")
        self.assertEqual("", result)

    def test_transform_taupage_user_data_key(self):
        input = {
            "notify_cfn": {
                "resource": "asg",
                "stack": {"Ref": "AWS::StackName"}
            },
            "cloudwatch_logs": {
                "/var/log/application.log": {"Ref": "applicationLog"},
                "/var/log/syslog": {"Ref": "syslog"}
            },
            "environment": {
                "DYNAMODB_INDEX_NAME": {"Ref": "dynamodbIndexName"},
                "JAVA_OPTS": "-Xmx3g",
                "METRICS_NAMESPACE": {"Ref": "AWS::StackName"},
                "ELASTICSEARCH_URL": {"Ref": "elasticsearchUrl"},
                "IMPORT_QUEUE_URL": {"Ref": "importQueue"}
            },
            "application_id": {"Ref": "AWS::StackName"},
            "health_check_port": 8080,
            "health_check_timeout_seconds": 9000,
            "ports": {
                "8080": 9000
            },
            "health_check_path": "/status",
            "root": True,
            "ecr": {
                "region": {"Ref": "AWS::Region"}
            },
            "runtime": "Docker",
            "healthcheck": {
                "type": "elb",
                "loadbalancer_name": {"Ref": "elb"}
            },
            "application_version": {"Ref": "dockerImageVersion"},
            "source": {
                "Fn::Join": [
                    ":", [
                        "my-docker-repo/my-app-image",
                        {"Ref": "dockerImageVersion"}
                    ]]
            }
        }

        expected = {
            "Fn::Base64": {
                "Fn::Join": [
                    "\n",
                    [
                        "#taupage-ami-config",
                        "application_id:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "  ",
                                    {
                                        "Ref": "AWS::StackName"
                                    }
                                ]
                            ]
                        },
                        "application_version:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "  ",
                                    {
                                        "Ref": "dockerImageVersion"
                                    }
                                ]
                            ]
                        },
                        "cloudwatch_logs:",
                        "  /var/log/application.log:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "applicationLog"
                                    }
                                ]
                            ]
                        },
                        "  /var/log/syslog:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "syslog"
                                    }
                                ]
                            ]
                        },
                        "ecr:",
                        "  region:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "AWS::Region"
                                    }
                                ]
                            ]
                        },
                        "environment:",
                        "  DYNAMODB_INDEX_NAME:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "dynamodbIndexName"
                                    }
                                ]
                            ]
                        },
                        "  ELASTICSEARCH_URL:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "elasticsearchUrl"
                                    }
                                ]
                            ]
                        },
                        "  IMPORT_QUEUE_URL:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "importQueue"
                                    }
                                ]
                            ]
                        },
                        "  JAVA_OPTS: '-Xmx3g'",
                        "  METRICS_NAMESPACE:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "AWS::StackName"
                                    }
                                ]
                            ]
                        },
                        "health_check_path: '/status'",
                        "health_check_port: 8080",
                        "health_check_timeout_seconds: 9000",
                        "healthcheck:",
                        "  loadbalancer_name:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "elb"
                                    }
                                ]
                            ]
                        },
                        "  type: 'elb'",
                        "notify_cfn:",
                        "  resource: 'asg'",
                        "  stack:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "    ",
                                    {
                                        "Ref": "AWS::StackName"
                                    }
                                ]
                            ]
                        },
                        "ports:",
                        "  8080: 9000",
                        "root: True",
                        "runtime: 'Docker'",
                        "source:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "  ",
                                    {
                                        "Fn::Join": [
                                            ":",
                                            [
                                                "my-docker-repo/my-app-image",
                                                {
                                                    "Ref": "dockerImageVersion"
                                                }
                                            ]
                                        ]
                                    }
                                ]
                            ]
                        }
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_taupage_user_data_key("@taupageUserData@", input)
        self.assertEqual("UserData", key)
        self.assertEqual(expected, value)

    def test_transform_yaml_user_data_key(self):
        input = {'docker-compose': {
            'services': {
                'db': {
                    'environment': {'MYSQL_DATABASE': 'wordpress',
                                    'MYSQL_PASSWORD': 'wordpress',
                                    'MYSQL_ROOT_PASSWORD': 'wordpress',
                                    'MYSQL_USER': 'wordpress'},
                    'image': 'mysql:5.7',
                    'restart': 'always',
                    'volumes': ['db_data:/var/lib/mysql']},
                'wordpress': {
                    'depends_on': ['db'],
                    'environment': {'WORDPRESS_DB_HOST': 'db:3306',
                                    'WORDPRESS_DB_PASSWORD': 'wordpress'},
                    'image': {'fn::join': [':',
                                           ['wordpress',
                                            {'ref': 'wp_version'}]]},
                    'ports': ['8000:80'],
                    'restart': 'always'}},
            'version': '2',
            'volumes': 'db_data'},
            'healthchecks': [
                {'http': {'port': 8000}},
                {'AwsElb': {'loadbalancer_name': {'Ref': 'my-alb'}}}],
            'pre_start': [
                {'AwsEcrLogin': {'account_id': 123456789123,
                                 'region': 'eu-west-1'}}],
            'signals': [
                {'AwsCfn': {'logical_resource_id': {'fn::getatt': ['my-asg', 'arn']},
                            'region': 'eu-west-1',
                            'stack_name': 'my-stack'}}]}

        expected = {
            "Fn::Base64": {
                "Fn::Join": [
                    "\n",
                    [
                        "docker-compose:",
                        "  services:",
                        "    db:",
                        "      environment:",
                        "        MYSQL_DATABASE: 'wordpress'",
                        "        MYSQL_PASSWORD: 'wordpress'",
                        "        MYSQL_ROOT_PASSWORD: 'wordpress'",
                        "        MYSQL_USER: 'wordpress'",
                        "      image: 'mysql:5.7'",
                        "      restart: 'always'",
                        "      volumes:",
                        "        - 'db_data:/var/lib/mysql'",
                        "    wordpress:",
                        "      depends_on:",
                        "        - 'db'",
                        "      environment:",
                        "        WORDPRESS_DB_HOST: 'db:3306'",
                        "        WORDPRESS_DB_PASSWORD: 'wordpress'",
                        "      image:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "        ",
                                    {
                                        "fn::join": [
                                            ":",
                                            [
                                                "wordpress",
                                                {
                                                    "ref": "wp_version"
                                                }
                                            ]
                                        ]
                                    }
                                ]
                            ]
                        },
                        "      ports:",
                        "        - '8000:80'",
                        "      restart: 'always'",
                        "  version: '2'",
                        "  volumes: 'db_data'",
                        "healthchecks:",
                        "  - http:",
                        "    port: 8000",
                        "  - AwsElb:",
                        "    loadbalancer_name:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "      ",
                                    {
                                        "Ref": "my-alb"
                                    }
                                ]
                            ]
                        },
                        "pre_start:",
                        "  - AwsEcrLogin:",
                        "    account_id: 123456789123",
                        "    region: 'eu-west-1'",
                        "signals:",
                        "  - AwsCfn:",
                        "    logical_resource_id:",
                        {
                            "Fn::Join": [
                                "",
                                [
                                    "      ",
                                    {
                                        "fn::getatt": ["my-asg", "arn"]
                                    }
                                ]
                            ]
                        },
                        "    region: 'eu-west-1'",
                        "    stack_name: 'my-stack'"
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_yaml_user_data_key("@YamlUserData@", input)
        self.assertEqual("UserData", key)
        self.assertEqual(expected, value)

    def test_transform_dict_to_yaml_lines(self):
        input = {
            "docker-compose": {
                "version": "2",
                "services": {
                    "grafana": {
                        "environment": {
                            "GF_SECURITY_ADMIN_PASSWORD": {"Ref": "grafanaAdminPassword"}
                        },
                        "ports": [
                            "3000:3000"
                        ],
                        "restart": "always"
                    }
                }
            }
        }

        expected = [
            "docker-compose:",
            "  services:",
            "    grafana:",
            "      environment:",
            "        GF_SECURITY_ADMIN_PASSWORD:",
            {
                "Fn::Join": [
                    "",
                    [
                        "          ",
                        {
                            "Ref": "grafanaAdminPassword"
                        }
                    ]
                ]
            },
            "      ports:",
            "        - '3000:3000'",
            "      restart: 'always'",
            "  version: '2'"
        ]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_preserves_int_values(self):
        input = {"a": 2}
        expected = ["a: 2"]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_preserves_double_values(self):
        input = {"a": 2.3}
        expected = ["a: 2.3"]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_preserves_string_numbers(self):
        input = {"a": "2"}
        expected = ["a: '2'"]

    def test_transform_dict_to_yaml_lines_preserves_boolean_values(self):
        input = {"a": True}
        expected = ["a: True"]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_dict(self):
        input = {
            "a": {
                "baa": {"key": "value"}
            },
            "b": [{"c": "d"}, "e", 2, [1, 2, {"Ref": "Foo"}]]
        }

        expected = [
            "a:",
            "  baa:",
            "    key: 'value'",
            "b:",
            "  - c: 'd'",
            "  - 'e'",
            "  - 2",
            "  -",
            "    - 1",
            "    - 2",
            {
                "Fn::Join": [
                    "",
                    [
                        "    - ",
                        {
                            "Ref": "Foo"
                        }
                    ]
                ]
            }
        ]

        result = CloudFormationTemplateTransformer._transform_dict(input)
        self.assertEqual(expected, result)

    def test_transform_dict_with_ref_in_nested_list(self):
        input = {
            "key": ["a", "b", ["a", {"Ref": "Foo"}]]
        }

        expected = [
            "key:",
            "  - 'a'",
            "  - 'b'",
            "  -",
            "    - 'a'",
            {
                "Fn::Join": [
                    "",
                    [
                        "    - ",
                        {
                            "Ref": "Foo"
                        }
                    ]
                ]
            }
        ]

        result = CloudFormationTemplateTransformer._transform_dict(input)
        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_list_accepts_multiple_sub_dicts(self):
        input = {
            "foo": {
                "baa": {"key": "value"}
            }
        }
        expected = ["foo:", "  baa:", "    key: 'value'"]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_list_accepts_int_key_value(self):
        input = {"ports": {8080: 9000}}

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        expected = [
            "ports:",
            {"Fn::Join": [": ", ["  8080", 9000]]}
        ]

        self.assertEqual(expected, result)

    def test_transform_dict_to_yaml_lines_list_accepts_joins(self):
        input = {
            "source": {"Fn::Join": [":", ["my-registry/my-app", {"Ref": "appVersion"}]]}
        }

        expected = [
            "source:",
            {
                "Fn::Join": [
                    "",
                    [
                        "  ",
                        {
                            "Fn::Join": [
                                ":",
                                [
                                    "my-registry/my-app",
                                    {
                                        "Ref": "appVersion"
                                    }
                                ]
                            ]
                        }
                    ]
                ]
            }
        ]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)


def test_transform_dict_to_yaml_lines_list_returns_stable_order(self):
    input = {"d": "d", "a": "a", "e": "e", "b": {"f": "f", "c": "c", "a": "a"}, "#": "3"}

    expected = [{"Fn::Join": [": ", ["#", "3"]]},
                {"Fn::Join": [": ", ["a", "a"]]},
                "b:",
                {"Fn::Join": [": ", ["  a", "a"]]},
                {"Fn::Join": [": ", ["  c", "c"]]},
                {"Fn::Join": [": ", ["  f", "f"]]},
                {"Fn::Join": [": ", ["d", "d"]]},
                {"Fn::Join": [": ", ["e", "e"]]}]

    result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
    self.assertEqual(expected, result)


def test_transform_kv_to_cfn_join_accepts_int_key_value(self):
    result = CloudFormationTemplateTransformer.transform_kv_to_cfn_join(8080, 9000)
    expected = {"Fn::Join": [": ", [8080, 9000]]}

    self.assertEqual(expected, result)


def test_transform_kv_to_cfn_join_quotes_strings_with_colons(self):
    result = CloudFormationTemplateTransformer.transform_kv_to_cfn_join('f:b', 'foo:baa')
    expected = {'Fn::Join': [': ', ["'f:b'", "'foo:baa'"]]}

    self.assertEqual(expected, result)


def test_transform_template_properly_renders_dict(self):
    template_dict = {
        "Resources": {
            "myResource": {
                "key1": "|ref|value",
                "key2": "|getatt|resource|attribute",
                "@TaupageUserData@":
                    {
                        "key1": "value",
                        "key2": {"ref": "value"},
                        "key3": {"|join|.": ["|Ref|a", "b", "c"]},
                        "key4": "|ref|value"
                    }
            }
        }
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))

    expected = {
        "myResource": {
            "key1": {
                "Ref": "value"
            },
            "key2": {
                "Fn::GetAtt": [
                    "resource",
                    "attribute"
                ]
            },
            "UserData": {
                "Fn::Base64": {
                    "Fn::Join": [
                        "\n",
                        [
                            "#taupage-ami-config",
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key1",
                                        "value"
                                    ]
                                ]
                            },
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key2",
                                        {
                                            "ref": "value"
                                        }
                                    ]
                                ]
                            },
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key3",
                                        {
                                            "Fn::Join": [
                                                ".",
                                                [
                                                    {"Ref": "a"},
                                                    "b",
                                                    "c"
                                                ]
                                            ]
                                        }
                                    ]
                                ]
                            },
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key4",
                                        {
                                            "Ref": "value"
                                        }
                                    ]
                                ]
                            },
                        ]
                    ]
                }
            }
        }
    }

    self.assertEqual(expected, result.resources)


def test_transform_template_transforms_references_in_conditions_section(self):
    template_dict = {
        "Conditions": {"key1": ["|ref|foo", "a", "b"], "key2": "|Ref|baa"}
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))
    expected = {"key1": [{"Ref": "foo"}, "a", "b"], "key2": {"Ref": "baa"}}

    self.assertEqual(expected, result.conditions)


def test_transform_template_transforms_list_values(self):
    template_dict = {
        "Resources": {"key1": ["|ref|foo", "a", "b"]}
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))
    expected = {"key1": [{"Ref": "foo"}, "a", "b"]}

    self.assertEqual(expected, result.resources)


def test_transform_template_transforms_dict_list_items(self):
    template_dict = {
        "Resources": {"key1": {"key2": [{"key3": "value3", "foo": {"|Join|": ["a", "b"]}}]}}
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))
    expected = {"key1": {"key2": [{"foo": {"Fn::Join": ["", ["a", "b"]]}, "key3": "value3"}]}}

    self.assertEqual(expected, result.resources)


def test_transform_template_transforms_join_with_embedded_ref(self):
    template_dict = {
        "Resources": {"key1": {"|join|.": ["|ref|foo", "b"]}}
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))
    expected = {"key1": {"Fn::Join": [".", [{"Ref": "foo"}, "b"]]}}

    self.assertEqual(expected, result.resources)


def test_transform_template_raises_exception_on_unknown_reference_value(self):
    template_dict = {
        "Resources": {"key1": "|foo|foo"}
    }

    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))


def test_transform_template_raises_exception_on_unknown_reference_key(self):
    template_dict = {
        "Resources": {"|key|": "foo"}
    }

    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))


def test_transform_template_raises_exception_on_unknown_at_reference_key(self):
    template_dict = {
        "Resources": {"@foo@": "foo"}
    }

    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))


def test_transform_template_raises_exception_on_embedded_reference(self):
    template_dict = {
        "Resources": {"key1": {"foo": ["|foo|foo", "b"]}}
    }

    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))


def test_transform_template_properly_handles_reference_in_list_of_lists(self):
    template_dict = {
        "Resources":
            {
                "myResource": {
                    "Properties": {
                        "PolicyDocument": {
                            "Statement": [{
                                "Resource": {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "a",
                                            "|Ref|b",
                                            "c"
                                        ]
                                    ]
                                }
                            }]
                        }
                    }
                }
            }
    }

    result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, "foo"))
    expected = {"myResource": {"Properties": {
        "PolicyDocument": {"Statement": [{"Resource": {"Fn::Join": ["", ["a", {"Ref": "b"}, "c"]]}}]}}}}

    self.assertEqual(expected, result.resources)


def test_check_for_leftover_reference_values_raises_exception_on_existing_reference(self):
    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.check_for_leftover_reference_values("|Ref|foo")


def test_check_for_leftover_reference_values_passes_on_double_pipe_values(self):
    self.assertEqual(("|| exit 1"),
                     CloudFormationTemplateTransformer.check_for_leftover_reference_values("|| exit 1"))


def test_check_for_leftover_reference_values_passes_on_double_pipe_with_spaces_values(self):
    self.assertEqual(("| xargs | grep"),
                     CloudFormationTemplateTransformer.check_for_leftover_reference_values("| xargs | grep"))


def test_check_for_leftover_reference_values_properly_returns_values_without_reference(self):
    self.assertEqual("foo", CloudFormationTemplateTransformer.check_for_leftover_reference_values("foo"))


def test_check_for_leftover_reference_values_properly_returns_empty_values(self):
    self.assertEqual("", CloudFormationTemplateTransformer.check_for_leftover_reference_values(""))


def test_check_for_leftover_reference_keys_raises_exception_on_existing_at_reference(self):
    with self.assertRaises(TemplateErrorException):
        CloudFormationTemplateTransformer.check_for_leftover_reference_keys("@Foo@", "foo")


def test_check_for_leftover_reference_keys_properly_returns_values_without_reference(self):
    self.assertEqual(("key", "value"),
                     CloudFormationTemplateTransformer.check_for_leftover_reference_keys("key", "value"))


def test_check_for_leftover_reference_keys_properly_returns_empty_values(self):
    self.assertEqual(("", ""), CloudFormationTemplateTransformer.check_for_leftover_reference_keys("", ""))


def test_is_reference_key_returns_true_on_existing_pipe_reference(self):
    self.assertTrue(CloudFormationTemplateTransformer.is_reference_key("|foo|"))


def test_is_reference_key_returns_true_on_references_with_leading_spaces(self):
    self.assertTrue(CloudFormationTemplateTransformer.is_reference_key("  |join|"))


def test_is_reference_key_returns_false_for_empty_string(self):
    self.assertFalse(CloudFormationTemplateTransformer.is_reference_key(""))


def test_is_reference_key_returns_false_for_simple_string(self):
    self.assertFalse(CloudFormationTemplateTransformer.is_reference_key("foo"))
