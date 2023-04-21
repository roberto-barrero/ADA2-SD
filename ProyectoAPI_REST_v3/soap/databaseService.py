import sqlite3
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import hashlib

app = Flask(__name__)
database_location = '../instance/users.db'
# Connect to the database
conn = sqlite3.connect(database_location)
c = conn.cursor()

# Create the users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username text PRIMARY KEY, password text, email text, name text)''')

# Commit changes and close the connection
conn.commit()
conn.close()

# Initialize the Zeep client
wsdl = './database.wsdl'
cache = SqliteCache(path='./cache.sqlite3', timeout=3600)
transport = Transport(cache=cache)
client = Client(wsdl=wsdl, transport=transport)

# Define the namespace
namespace = {'ns0': "http://schemas.xmlsoap.org/soap/envelope/", 'ns1': 'http://localhost:5000/user-service'}


def createSOAPResponse(body):
    # Create the SOAP response
    soap_response = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:5000/user-service'})
    soap_body = ET.SubElement(soap_response, 'ns0:Body')
    soap_body.append(body)
    return soap_response

# Define the SOAP service endpoints
@app.route('/', methods=['GET', 'POST'])
def user_service():
    if request.method == 'POST':
        request_xml = request.data
        response = client.service.__call__(
            request.environ['PATH_INFO'][1:],
            ET.fromstring(request_xml)
        )
        return str(response), 200, {'Content-Type': 'application/xml'}
    else:
        return 'User Database Web Service'

# Define the create user endpoint
@app.route('/createUser', methods=['POST'])
def create_user():
    # Parse the username, password, and email from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username, password, and email elements
    username_element = soap_request_xml.find('.//ns1:username', namespace)
    password_element = soap_request_xml.find('.//ns1:password', namespace)
    email_element = soap_request_xml.find('.//ns1:email', namespace)
    name_element = soap_request_xml.find('.//ns1:name', namespace)

    # Extract the values of the username, password, and email elements from the SOAP request
    username = username_element.text
    password = hashlib.sha256(password_element.text.encode("utf-8")).hexdigest()
    email = email_element.text
    name = name_element.text

    # Insert the new user into the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, email, name) VALUES (?, ?, ?, ?)", (username, password, email, name))
    conn.commit()
    conn.close()

    response = ET.Element('ns1:createUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_user = ET.SubElement(response, 'ns1:user')
    response_username = ET.SubElement(response_user, 'ns1:username').text = username
    response_password = ET.SubElement(response_user, 'ns1:password').text = password
    response_email = ET.SubElement(response_user, 'ns1:email').text = email
    resopnse_name = ET.SubElement(response_user, 'ns1:name').text = name

    soap_response = createSOAPResponse(response)
    print(ET.tostring(soap_response))
    # Return a success message
    return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})

# Define the update user endpoint
@app.route('/updateUser', methods=['POST'])
def update_user():
    
    soap_request_xml = ET.fromstring(request.data)
    # Find the username, password, and email elements
    token_element = soap_request_xml.find('.//ns1:authToken', namespace)
    user_element = soap_request_xml.find('.//ns1:user', namespace)
    new_username_element = user_element.find('.//ns1:username', namespace)
    password_element = user_element.find('.//ns1:password', namespace)
    email_element = user_element.find('.//ns1:email', namespace)
    name_element = user_element.find('.//ns1:name', namespace)

    # Extract the values of the username, password, and email elements from the SOAP request
    authToken = token_element.text
    new_username = new_username_element.text
    new_password = hashlib.sha256(password_element.text.encode("utf-8")).hexdigest()
    new_email = email_element.text
    new_name = name_element.text
    
    # Update the user in the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute("UPDATE users SET password = ?, username = ?, email = ?, name = ? WHERE authToken = ?", (new_password, new_username, new_email, new_name, authToken))
    conn.commit()
    conn.close()

    # Create the SOAP response
    response = ET.Element('ns1:updateUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_user = ET.SubElement(response, 'ns1:user')
    response_username = ET.SubElement(response_user, 'ns1:username').text = new_username
    response_password = ET.SubElement(response_user, 'ns1:password').text = new_password
    response_email = ET.SubElement(response_user, 'ns1:email').text = new_email
    response_name = ET.SubElement(response_user, 'ns1:name').text = new_name

    soap_response = createSOAPResponse(response)
    
    # Return a success message
    return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})

# Define the delete user endpoint
@app.route('/deleteUser', methods=['POST'])
def delete_user():
    # Parse the username from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username element
    token_element = soap_request_xml.find('.//ns1:authToken', namespace)

    # Extract the values of the username from the SOAP request
    token = token_element.text
    
    # Delete the user from the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE authToken = ?", (token))
    username = c.fetchone()[0]
    c.execute("DELETE FROM users WHERE authToken = ?", (token))
    conn.commit()
    conn.close()

    # Create the SOAP response
    response = ET.Element('ns1:deleteUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_username = ET.SubElement(response, 'ns1:username').text = username

    soap_response = createSOAPResponse(response)
    
    # Return a success message
    return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})

# Define the get password endpoint
@app.route('/getPassword', methods=['POST'])
def get_password():
    # Parse the password from the request body

    print("Request data: " + str(request.data))
    soap_request_xml = ET.fromstring(request.data)

    # Find the password element
    username_element = soap_request_xml.find('.//ns1:username', namespace)

    # Extract the values of the password from the SOAP request
    username = username_element.text
    
    # Retrieve the password for the specified user from the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute(f"SELECT password FROM users WHERE username = '{username}'")
    result = c.fetchone()
    conn.close()
    
    # Check if the user was found in the database
    if result is None:
        # Return an error message if the user was not found
        return jsonify({'error': 'User not found'}), 404
    else:
        
        # Create the SOAP response
        response = ET.Element('ns1:getPasswordResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
        response_password = ET.SubElement(response, 'ns1:password').text = result[0]

        soap_response = createSOAPResponse(response)
        
        # Return the password
        return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})
  
# Define the get user endpoint
@app.route('/getUser', methods=['POST'])
def get_user():
    # Parse the username from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username element
    token_element = soap_request_xml.find('.//ns1:authToken', namespace)

    # Extract the values of the username from the SOAP request
    token = token_element.text
    
    # Retrieve the user from the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute(f"SELECT * FROM users WHERE authToken = '{token}'")  
    # c.execute("SELECT * FROM users WHERE username = ? AND token = ", (username,))
    result = c.fetchone()
    conn.close()
    
    # Check if the user was found in the database
    if result is None:
        # Return an error message if the user was not found
        return jsonify({'error': 'User not found'}), 404
    else:
        response = ET.Element('ns1:getUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
        response_user = ET.SubElement(response, 'ns1:user')
        response_username = ET.SubElement(response_user, 'ns1:username').text = result[0]
        response_password = ET.SubElement(response_user, 'ns1:password').text = result[1]
        response_email = ET.SubElement(response_user, 'ns1:email').text = result[2]
        response_name = ET.SubElement(response_user, 'ns1:name').text = result[3]
        soap_response = createSOAPResponse(response)
        # Return a success message
        return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})
    
# Define the set auth token endpoint
@app.route('/setAuthToken', methods=['POST'])
def set_auth_token():
    # Validate the request host is localhost
    # if request.remote_addr != 'http://localhost:5000/user-service':
    #     return jsonify({'error': 'Invalid request'}), 400
    
    # Print the client IP address
    print("Client IP address: " + request.remote_addr)

    # Parse the username and auth token from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username and auth token elements

    username_element = soap_request_xml.find('.//ns1:username', namespace)
    token_element = soap_request_xml.find('.//ns1:authToken', namespace)

    # Extract the values of the username and auth token from the SOAP request
    username = username_element.text
    token = token_element.text

    # Update the user in the database
    conn = sqlite3.connect(database_location)
    c = conn.cursor()
    c.execute("UPDATE users SET authToken = ? WHERE username = ?", (token, username))
    conn.commit()
    conn.close()

    # Create the SOAP response
    response = ET.Element('ns1:user', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_username = ET.SubElement(response, 'ns1:username').text = username
    response_token = ET.SubElement(response, 'ns1:authToken').text = token

    soap_response = createSOAPResponse(response)

    # Return a success message
    return Flask.response_class(response=ET.tostring(soap_response), status=200, mimetype='text/xml', headers={'Access-Control-Allow-Origin': '*'})


if __name__ == '__main__':
    app.run()