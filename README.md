# OPA Example for Cisco NSO

This is a quick example of how to integrate Cisco NSO with the [Open Policy Agent](https://www.openpolicyagent.org/). This allows you
to express policies in OPA and both supply base documents from NSO and use rules expressed in Rego for decisions within NSO, in particular the example shows how to use this to validate service intent against rules.

The service code in this example is taken from `$NCS_DIR/examples.ncs/getting-started/developing-with-ncs/17-mpls-vpn-python/packages/` and the modifications should be clear in the code.

This has been tested with ncs 4.6.1 and OPA 0.8.2.

## Setup

1. Get OPA

This gets a static binary

```bash
    curl -L -o opa https://github.com/open-policy-agent/opa/releases/download/v0.8.2/opa_darwin_amd64
    chmod a+x opa
```

2. Setup NSO and build the packages

```bash
    ncs-setup --dest .
    make
```


## Simple Demo

1. Run OPA in a terminal
```bash
    ./opa run --server --log-level=debug
```

2. Start NSO
```bash
    make start
```

3. Show the transfer of topology information into opa. Since opa was started after NSO it has to be triggered manually. Run `request packages reload` in the NSO cli. You can then verify that the topology we uploaded into opa looks right:
```bash
    curl localhost:8181/v1/data/topology?pretty=true
```

4. Look at the file `demo/demo.rego`, it contains a very simple rule that hardcodes
```bash
    curl -v -X PUT --data-binary @demo/demo.rego localhost:8181/v1/policies/test
```

5. Load an example vpn into the nso cli and try commiting it
```
    load merge vpn0.cli
    commit dry-run
```
   You will notice that the `as-number` used does not match the allowed number shown if you do `show topology allowedas volvo`

   Try changing the `as-number` to one of the allowed ones
```
 set vpn l3vpn volvo as-number 65000
 commit dry-run
```
   It will now proceed as usual.


## Code

There are two main components, a simple subscriber in `packages/opa/python/opa/sub.py` that transfers all toplogy into opa as a base-document under `data/topology`.

The other is the service l3vpn, it has been modified in two ways:

 1. A list called allowedas is added to the topology structure, to serve as a way to record which customers are allowed to us which as-numbers.
 2. In `service.py` we added a simple pre-modificaiton callback that calls a new function `opa_check` which verifies that the result for the `allow` rule in the `data/service/l3vpn` module evaluates to `true`, otherwise it throws an exception.

 In addition to these there are some helper functions to marshal data into JSON format.
