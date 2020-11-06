import json
import decimal
import boto3
from boto3.dynamodb.conditions import Key


def dynamodb_item_to_json(item: dict, indent: int = None) -> str:
    """Function to serialize items retrieved from DynamoDB as JSON strings.

    Amazon's DynamoDB API for Python returns numbers as decimal.Decimal
    instances instead of ints or floats. This makes it so that you can't
    just call json.dumps on an item retrieved from DynamoDB. If you want to
    serialize a DynamoDB item to JSON, you can just use this function.

    :param item: the DynamoDB item to serialize
    :param indent: (optional) number of spaces with which to indent the JSON
    :return: the item as a JSON string
    """
    result = {}
    for key in item.keys():
        if type(item[key]) is decimal.Decimal:
            result[key] = float(item[key])
        else:
            result[key] = item[key]

    return json.dumps(result, indent=indent)


class DynamoDB:
    """This class basically allows you to treat a DynamoDB table as a dict.

    ----

    Amazon's API for using DynamoDB in Python is needlessly complex for most of our use cases.
    This class uses operator overloading to make querying and updating a DynamoDB table as easy
    as using a dict.

    ----

    Additionally, the Table object is accesible through a @property, so you can still
    use all of Amazon's API methods. For example, if you have an instance of ecs.DynamoDB
    named "foo", and you want to call delete_item on its table, you can do it like so:

        foo.table.delete_item(Key={"primary-key-name": "key-of-item-to-delete"})

    ----

    This class's ctor requires you to have a config.json in your Lambda function's directory to specify the Amazon
    region name and DynamoDB endpoint URL.

    """

    def __init__(self, table_name: str, primary_key_name: str):
        """Ctor for the ecs.DynamoDB class.

        ----

        :param table_name: the name of the DynamoDB table to be represented by this object
        :param primary_key_name: the name of the table's primary key
        """
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
        self._table = self._boto_dynamodb_client.Table(self._table_name)

        # To ensure that creating new DynamoDB objects isn't too expensive,
        # the length of a table is lazily evaulated. Read the implementation
        # of the method ecs.DynamoDB.__len__ to see how this works.
        self._len = None

    def __getitem__(self, value):
        """Operator to query the table represented by this object.

        ----

        This operator will return the item from the table for which the value
        of the item's primary key is the value passed to the operator. For example,
        if a table's primary key is "deviceid", then table["123456"] will return the
        item which has the value "123456" for its deviceid.

        :param value: value of the desired item's primary key
        :return: the item whose primary key is the requisite value
        """
        data = self._table.get_item(Key={self._primary_key: value})
        return data["Item"]

    def __setitem__(self, value, item: dict):
        """Operator to create or update an item in this object's table.

        ----

        This operator will create an item in the table which has the passed
        value for its primary key. The rest of the item's attributes are specified
        by the assigned dict.

        ----

        Suppose you have a table whose primary key is "deviceid". If you do this:
            table["123456"] = {
                "foo": 1337,
                "bar": "Hello"
            }

        then the table will have a new item with "123456" as its deviceid, plus the columns
        "foo" and "bar" with the values 1337 and "hello" respectively.

        ----

        :param value: value for the primary key of the item to add
        :param item: attributes and their values of the item to add
        """
        new_entry = {
            self._primary_key: value,
            **item
        }

        r = self._table.put_item(Item=new_entry)

        # This operation may have changed the number of entries in the table,
        # so we set the _len attribute to None. _len won't be reevaluated until
        # the next time __len__ gets called.
        self._len = None

        return r

    @property
    def table(self):
        """Property for accessing the Table object.

        ----

        Any time you want to access the Table object, you might be doing something
        that changes the number of items in the DynamoDB table, so the _len attribute
        will be reset to None so it will have to be reevaluated the next time __len__
        gets called.

        """
        self._len = None
        return self._table

    @property
    def primary_key_name(self):
        """Property for getting the name of the table's primary key name.

        ----

        We want the primary key name to be read-only because there's never a
        good reason to change it, since DynamoDB tables can't have their primary
        key's name changed.

        """
        return self._primary_key

    def __len__(self):
        # The number of entries in the table is lazily evaluated. Any of this class's
        # methods that might change the number of entries in the table will result in
        # the _len attribute being set to None.
        if self._len is None:
            table_data = self.get_all_items()
            self._len = len(table_data)
        return self._len

    # This method will get _ALL_ the data in a table, even over the 1MB limit. If you don't really
    # need 1MB of data, use `DynamoDB.table.scan()` instead of `DynamoDB.get_all_items()`.
    def get_all_items(self, **kwargs):
        """Method to get _all_ items from a table, even over the 1MB limit on scan() operations.

        ----

        The Table.scan() operation only returns at most a megabyte of items from a table at a time.
        This method returns _all_ items from a table, regardless of how much data that is. It will
        call the scan() operation over and over with the LastEvaluatedKey until it has retrieved
        the table's full contents.

        ----

        :param kwargs: any arguments you want to pass to the scan() operation
        :return: all items in the table
        """
        response = self._table.scan(**kwargs)
        if kwargs.get("Select") == "COUNT":
            return response.get("Count")
        data = response.get("Items")
        while "LastEvaluatedKey" in response:
            response = kwargs.get("table").scan(ExclusiveStartKey=response["LastEvaluatedKey"], **kwargs)
            data.extend(response["Items"])
        return data

    def get_items_by_key_val_pair(self, key: str, value):
        """Method to get items which have a specified value for one of their keys.

        ----

        If a table has a "customerid" column, for example, and you want to get all
        items from the table which have the value 1337 for their customerid, you can
        simply do this:
            table.get_items_by_key_val_pair("customerid", 1337)

        ----

        :param key: key by which to query items
        :param value: desired value for the specified key in the returned items
        :return: items for which item[key] == value
        """
        data = self._table.query(
            KeyConditionExpression=Key(key).eq(value)
        )
        return data["Items"]
