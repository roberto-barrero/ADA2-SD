import sqlite3
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from flask import Flask, request, jsonify
from lxml import etree
import xml.etree.ElementTree as ET

app = Flask(__name__)

# Connect to the database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create the users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username text PRIMARY KEY, password text, email text, name text)''')

# Commit changes and close the connection
conn.commit()
conn.close()

# Initialize the Zeep client
wsdl = 'database.wsdl'
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
            etree.fromstring(request_xml)
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

    # Extract the values of the username, password, and email elements from the SOAP request
    username = username_element.text
    password = password_element.text
    email = email_element.text

    # Insert the new user into the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
    conn.commit()
    conn.close()

    response = ET.Element('ns1:createUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_user = ET.SubElement(response, 'ns1:user')
    response_username = ET.SubElement(response_user, 'ns1:username').text = username
    response_password = ET.SubElement(response_user, 'ns1:password').text = password
    response_email = ET.SubElement(response_user, 'ns1:email').text = email

    soap_response = createSOAPResponse(response)
    print(ET.tostring(soap_response))
    # Return a success message
    return ET.tostring(soap_response)

# Define the update user endpoint
@app.route('/updateUser', methods=['POST'])
def update_user():
    
    soap_request_xml = ET.fromstring(request.data)
    # Find the username, password, and email elements
    username_element = soap_request_xml.find('.//ns1:username', namespace)
    user_element = soap_request_xml.find('.//ns1:user', namespace)
    new_username_element = user_element.find('.//ns1:username', namespace)
    password_element = user_element.find('.//ns1:password', namespace)
    email_element = user_element.find('.//ns1:email', namespace)

    # Extract the values of the username, password, and email elements from the SOAP request
    username = username_element.text
    new_username = new_username_element.text
    new_password = password_element.text
    new_email = email_element.text
    
    # Update the user in the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password = ?, username = ?, email = ? WHERE username = ?", (new_password, new_username, new_email, username))
    conn.commit()
    conn.close()

    # Create the SOAP response
    response = ET.Element('ns1:updateUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_user = ET.SubElement(response, 'ns1:user')
    response_username = ET.SubElement(response_user, 'ns1:username').text = new_username
    response_password = ET.SubElement(response_user, 'ns1:password').text = new_password
    response_email = ET.SubElement(response_user, 'ns1:email').text = new_email

    soap_response = createSOAPResponse(response)
    
    # Return a success message
    return ET.tostring(soap_response)

# Define the delete user endpoint
@app.route('/deleteUser', methods=['POST'])
def delete_user():
    # Parse the username from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username element
    username_element = soap_request_xml.find('.//ns1:username', namespace)

    # Extract the values of the username from the SOAP request
    username = username_element.text
    
    # Delete the user from the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    # Create the SOAP response
    response = ET.Element('ns1:deleteUserResponse', {'xmlns:ns1': 'http://localhost:5000/user-service'})
    response_username = ET.SubElement(response, 'ns1:username').text = username

    soap_response = createSOAPResponse(response)
    
    # Return a success message
    return ET.tostring(soap_response)

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
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
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
        return ET.tostring(soap_response)
  
# Define the get user endpoint
@app.route('/getUser', methods=['POST'])
def get_user():
    # Parse the username from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username element
    username_element = soap_request_xml.find('.//ns1:username', namespace)

    # Extract the values of the username from the SOAP request
    username = username_element.text
    
    # Retrieve the user from the database
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
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
        soap_response = createSOAPResponse(response)
        print(ET.tostring(soap_response))
        # Return a success message
        return ET.tostring(soap_response)

if __name__ == '__main__':
    app.run()