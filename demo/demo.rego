package service.l3vpn

# Certain VPNs are allowed to use certain AS:es

# Service input
import input as service
import data.topology as topology

default allow = false

# curl -v -X POST "http://localhost:8181/v1/data/service/l3vpn?pretty=true" -d '{"input":{"method":"GET", "path":["finance","salary","alice"], "user":"alice"}}'

# Find the one matching the customer in the service
cust_topology = [ topology.allowedas[t] | topology.allowedas[t]["customer"] = "volvo"]

allowed_as = cust_topology[_]["as"]

allow {
    allowed_as[_] = to_number(service["as-number"])
}

# curl -v -X POST "http://localhost:8181/v1/data/service/l3vpn?pretty=true" -d '{"input":{"name":"volvo", "as":"65009"}}'
