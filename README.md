# automatic_rest_testing
Automatic RESTful API Testing / Whitebox Testing / Load Testing tool

## Requirements

1. pip utility

    1. `$ sudo easy_install pip # in Mac`
    1. Or you can install pip from the website (https://pip.pypa.io/en/latest/installing/)
1. pip package
    1. `$ sudo pip install -r requirements.txt`

## Usage

### Automatic Rest Testing

`python ./auto_rest_test.py -c <CONFIG FILE> -t <TEST CASE FILE> [-d:If you want to get the detailed result]`

### Load Testing

`python ./load_test.py -c <CONFIG FILE> -t <TEST CASE FILE> [-d:If you want to get the detailed result]`

## Configuration file

```
[OAuth]
Version: 1.0
Host: oauth.server.com
Port: 443
URL: /sessions
Concept: MessagingServerName
UserName: USERNAME
Password: PASSWORD
consumer_key: <CONSUMER_KEY>
consumer_secret: <CONSUMER_SECRET>
```

## Automatic Test cases

1. "TestCases" key, "name" key, "url" key, and "data" key are required.

```
{
  "TestCases": [
    {
      "name": "Test Case 1",
      "description": "Test case 1 when var1 is present and var2 is present",
      "url": "http://localhost:8000/test/case/endpoint",
      "data": {
        "var1" : 1234,
        "var2": {
          "subvar1": "test"
        }
      }
    },
    {
      "name": "Test Case 2",
      "description": "Test case 2 when var1 is present and var2 is null",
      "url": "http://localhost:8000/test/case/endpoint",
      "data": {
        "var1" : 1234
      }
    },
    ...
    {
      "name": "Test Case n",
      "description": "Test case n when...",
      "url": "http://localhost:8000/test/case/endpoint",
      "data": {
        ...
        }
      }
    }
  ]
}
```

## Load Test scenarios

1. "TestIteration" key is required.

```
{
  "TestIteration": 10,
}
```

2. "TestData" object is used to assign variables in the scenario. Each object in the array is assigned to a separate process and run simultaneously.

```
{
  ...
  "TestData": [
    {
      "encounter_id": 1,
      "pump_device_id": <DATA1 in Process1>
    },
    {
      "encounter_id": 1,
      "pump_device_id": <DATA2 in Process2>
    },
    {
      "encounter_id": 1,
      "pump_device_id": <DATA2 in Process2>
    }
  ],
  ...
}

```

2. "Scenario" object: "name" key, "url" key, and "data" key are required. "method, ""delayToNext", "variables" optional

```
{
  "Scenario": [
    {
      "name": "Scenario 1",
      "description": "Test case 1 when var1 is present and var2 is present",
      "url": "http://localhost:8000/test/case/endpoint",
      "method": "POST",
      "data": {
        "var1" : 1234,
        "var2": {
          "subvar1": "test"
        }
      },
      "delayToNext": <DELAY_TO_NEXT in SECONDS>,
    },
    {
      "name": "Scenario 2",
      "description": "Test case 2 when var1 is present and var2 is null",
      "url": "http://localhost:8000/test/case/endpoint",
      "method": "GET"
    },
    ...
    {
      "name": "Scenario n",
      "description": "Test case n when...",
      "url": "http://localhost:8000/test/case/endpoint",
      "METHOD" : "DELETE",
      "data": {
        ...
        }
      }
    }
  ]
}
```

3. "variable" object in Scenario: assigns the result into the test_data so that it can be used in the next scenario

```
{
  "Scenario": [
    ...
    "variables": {
      "association_id": {
        "type": "dict",
        "key": "devices",
        "child": {
          "type": "list",
          "index": 0,
          "child": {
            "type": "str",
            "key": "id"
          }
        }
      }
    }
  ]
}
```

In the example, we get "id" value in the first object in "devices" array in the result, assign it to "association_id" in TestData and we can use it to next Scenario by using {{ association_id }}.
