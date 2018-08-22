package service.l3vpn

# Certain VPNs are allowed to use certain AS:es

# Service input
import input as service
import data.topology as topology

default allow = false


# Find the one matching the customer in the service
cust_topology = [ topology.allowedas[t] | topology.allowedas[t]["customer"] = service["name"]]

allowed_as = cust_topology[_]["as"]

allow {
    allowed_as[_] = to_number(service["as-number"])
}

# Simple command to test the rule:
# curl -v -X POST "http://localhost:8181/v1/data/service/l3vpn?pretty=true" -d '{"input":{"name":"volvo", "as-number":"65009"}}'
# Command to upload the rule:
# curl -v -X PUT --data-binary @demo/demo.rego localhost:8181/v1/policies/test
