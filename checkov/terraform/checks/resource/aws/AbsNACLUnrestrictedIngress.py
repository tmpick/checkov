from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.util.type_forcers import force_list
from checkov.common.util.type_forcers import force_int


class AbsNACLUnrestrictedIngress(BaseResourceCheck):
    def __init__(self, check_id, port):
        name = "Ensure no NACL allow ingress from 0.0.0.0:0 to port %d" % port
        supported_resources = ['aws_network_acl', 'aws_network_acl_rule']
        categories = [CheckCategories.NETWORKING]
        super().__init__(name=name, id=check_id, categories=categories, supported_resources=supported_resources)
        self.port = port

    def scan_resource_conf(self, conf):
        """

            Return PASS if:
            - The NACL doesnt allows restricted ingress access to the port
            - The resource is an aws_network_acl of type 'ingress' that does not violate the check.

            Return FAIL if:
            - The the NACL allows unrestricted access to the port

            Return UNKNOWN if:
            - the resource is an NACL of type 'egress', OR

        :param conf: aws_network_acl configuration
        :return: <CheckResult>
        """

        if conf.get("ingress"):
            ingress = conf.get("ingress")
            for rule in ingress:
                rule_lst = rule
                if not isinstance(rule_lst, list):
                    rule_lst = [rule_lst]
                for sub_rule in rule_lst:
                    if not self.check_rule(sub_rule):
                        return CheckResult.FAILED
            return CheckResult.PASSED
        # maybe its an network_acl_rule
        if conf.get("network_acl_id"):
            if not conf.get("egress") or not conf.get("egress")[0]:
                if not self.check_rule(conf):
                    return CheckResult.FAILED
            return CheckResult.PASSED

        return CheckResult.UNKNOWN

    def check_rule(self, rule):
        from_port = rule.get('from_port')
        to_port = rule.get('to_port')
        if rule.get('cidr_block'):
            if rule.get('cidr_block') == ["0.0.0.0/0"]:
                if rule.get('action') == ["allow"] or rule.get('rule_action') == ["allow"]:
                    protocol = rule.get('protocol')
                    if protocol and str(protocol[0]) == "-1":
                        return False
                    if from_port and to_port and int(from_port[0]) <= self.port <= int(to_port[0]):
                        return False
        if rule.get('ipv6_cidr_block'):
            if rule.get('ipv6_cidr_block') == ["::/0"]:
                if rule.get('action') == ["allow"] or rule.get('rule_action') == ["allow"]:
                    protocol = rule.get('protocol')
                    if protocol and str(protocol[0]) == "-1":
                        return False
                    if from_port and to_port and int(from_port[0]) <= self.port <= int(to_port[0]):
                        return False
        return True
