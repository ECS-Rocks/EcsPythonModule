# EcsPythonModule
The ECS module for Python AWS Lambda functions.

The purpose of this module is to simplify the code used by ECS Technology Solutions. If other
people or companies find it useful as well, that's entirely incidental.

This module is meant to be used as an AWS Lambda Layer. You must have `config.json` in the same
directory as `lambda_handler.py` to use the ECS module. Sample `config.json`:

```
{
    "region-name": "us-east-1",
    "endpoint-url": "https://dynamodb.us-east-1.amazonaws.com",
    "admin-email": "developer@example.com"
}
```

No part of this document should be interpreted to suggest or imply any kind of warranty or
guarantee of service. See the LICENSE for more details.
