import json
import boto3
import urllib3
import base64
import re
import os
import pymysql
from pymysql import Error
from botocore.response import StreamingBody
from urllib.parse import parse_qs

bedrock = boto3.client(service_name='bedrock-runtime')

http = urllib3.PoolManager()

html_code = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatBox</title>
  </head>
  <body>
    <form action="/" method="POST" style="float: left;">
      <label for="message">Enter your message:</label>
      <br>
      <textarea id="message" name="message" rows="30" cols="100">ReplaceMesgHere</textarea>
      <br>
      <input type="submit" value="Submit">
    </form>
    <div style="float:left;width:300px;height:300px;margin-left: 40px;">
      <h3>Results</h3>
      <p>ResHere</p>
      <div>
  </body>
</html>
'''
prompt = '''
Here is my MySQL tables:\n\n

```
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);
```
\n\n
```
CREATE TABLE fruits (
    id INT PRIMARY KEY,
    user_id INT,
    fruit_name VARCHAR(50) NOT NULL,
    quantity INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```
\n\n

'''
endprompt = "\n\nONLY OUTPUT SQL CODE ENCLOSED IN THREE BACKTICKS."


def call_bedrock(prompt):
    body = json.dumps({
        "prompt": prompt,
        "maxTokens": 3000,
        "temperature": 0.5,
        "topP": 1,
    })

    modelId = 'meta.llama2-70b-chat-v1'
    accept = 'application/json'
    contentType = 'application/json'

    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)

    if isinstance(response.get('body'), StreamingBody):
        response_content = response['body'].read().decode('utf-8')
    else:
        response_content = response.get('body')

    response_body = json.loads(response_content)

    return response_body.get('completions')[0].get('data').get('text')


def query_mysql_database(query):
    try:
        connection = pymysql.connect(
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            host=os.environ["db_host"],
            database=os.environ["db_name"],
            cursorclass=pymysql.cursors.DictCursor
        )

        if connection.open:
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

            return results

    except Error as e:
        print(f"Error: {e}")
        return None

    finally:
        if connection.open:
            connection.close()


def lambda_handler(event, context):
    msg = ""
    results = ""
    if 'body' in event:
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
            query_params = parse_qs(body)
            msg = call_bedrock(prompt + query_params['message'][0])
            sql = re.findall(r'```([\s\S]*?)```', msg)
            if len(sql) > 0:
                res = query_mysql_database(sql[0].replace('\n', ' '))
                if res:
                    results = json.dumps(res)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': html_code.replace('ReplaceMesgHere', msg).replace('ResHere', results)
    }

if __name__ == "__main__":
    event = {
        'body': 'message=What is the total number of fruits?',
        'isBase64Encoded': False
    }
    print(lambda_handler(event, None))


