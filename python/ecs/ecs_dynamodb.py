import json
import boto3
from boto3.dynamodb.conditions import Key, Attr


class DynamoDB:

    def __init__(self, table_name: str, primary_key_name: str):
        self._primary_key = primary_key_name
        self._table_name = table_name
        try:
            config_file = open("config.json")
            self._config_options = json.loads(config_file.read())
        except FileNotFoundError:
            raise FileNotFoundError((
                "Unable to find config.json. "
                "You need config.json in your pwd to use the ecs.DynamoDB class."
            ))
        self._boto_dynamodb_client = boto3.resource(
            "dynamodb",
            region_name=self._config_options["region-name"],
            endpoint_url=self._config_options["endpoint-url"]
        )
        self.table = self._boto_dynamodb_client.Table(self._table_name)


    def __getitem__(self, value):
        data = self.table.get_item(Key={self._primary_key: value})
        return data["Item"]


    def __setitem__(self, key, item: dict):
        new_entry = {
            self._primary_key: key,
            **item
        }

        r = self.table.put_item(Item=new_entry)

        return r


    def __len__(self):
        table_data = self.table.scan()
        try:
            return len(table_data["Items"])
        except KeyError:
            return 0


    # This method will get _ALL_ the data in a table, even over the 1MB limit. If you don't really
    # need 1MB of data, use `DynamoDB.table.scan()` instead of `DynamoDB.get_all_items()`.
    def get_all_items(self, **kwargs):
        response = self.table.scan(**kwargs)
        if kwargs.get("Select") == "COUNT":
            return response.get("Count")
        data = response.get("Items")
        while "LastEvaluatedKey" in response:
            response = kwargs.get("table").scan(ExclusiveStartKey=response["LastEvaluatedKey"], **kwargs)
            data.extend(response["Items"])
        return data


    def get_items_by_key_val_pair(self, key: str, value):
        data = self.table.query(
            KeyConditionExpression=Key(key).eq(value)
        )
        return data["Items"]
