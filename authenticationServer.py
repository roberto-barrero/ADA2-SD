from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.exceptions import Fault
from flask import Flask, request, jsonify
import uuid
import xml.etree.ElementTree as ET
import requests

# Define the namespace
namespace = {'ns0': "http://schemas.xmlsoap.org/soap/envelope/", 'ns1': 'http://localhost:8000/authentication'}
database_namespace = {'ns0': "http://schemas.xmlsoap.org/soap/envelope/", 'ns1': 'http://localhost:5000/user-service'}


def createSOAPResponse(body):
    # Create the SOAP response
    soap_response = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:8000/authentication'})
    soap_body = ET.SubElement(soap_response, 'ns0:Body')
    soap_body.append(body)
    return soap_response


def login(username, password):
    
    # Create SOAP request to the database service
    soap_request = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:5000/user-service'})
    soap_body = ET.SubElement(soap_request, 'ns0:Body')
    body = ET.Element('ns1:getPasswordRequest')
    name = ET.SubElement(body, 'ns1:username').text = username
    soap_body.append(body)

    # Send the SOAP request to the database service
    response = requests.post('http://localhost:5000/getPassword', data=ET.tostring(soap_request), headers={'Content-Type': 'application/xml'})
    
    print("Database response: " + str(response.text))

    # Parse the SOAP response from the database service
    soap_response_xml = ET.fromstring(response.text)

    print("Response: " + str(ET.tostring(soap_response_xml)))
    password_element = soap_response_xml.find('.//ns1:getPasswordResponse', database_namespace)
    password_value = password_element.find('.//ns1:password', database_namespace)
    actual_password = password_value.text

    print("Actual password: " + actual_password)


    if password == actual_password:
        
       # Create the SOAP response
        response = ET.Element('ns1:LoginResponse', {'xmlns:ns1': 'http://localhost:8000/authentication'})
        response_token = ET.SubElement(response, 'ns1:authToken').text = str(uuid.uuid4())

        soap_response = createSOAPResponse(response)
        return ET.tostring(soap_response)
    else:
        raise Fault(code='INVALID_LOGIN', message='Invalid username or password')

app = Flask(__name__)

@app.route('/authentication', methods=['POST'])
def authentication():
    client = Client(wsdl='authentication.wsdl')
    # Define the login operation
    client.service.login = login

    # Parse the username from the request body
    soap_request_xml = ET.fromstring(request.data)

    # Find the username element
    username_element = soap_request_xml.find('.//ns1:username', namespace)
    password_element = soap_request_xml.find('.//ns1:password', namespace)

    # Extract the values of the username from the SOAP request
    username = username_element.text
    password = password_element.text

    print("Username: " + username, "Password: " + password)
    try:
        auth_token = client.service.login(username, password)
        return auth_token, 200
    except Fault as e:
        return str(e), 401

if __name__ == '__main__':
    app.run(port=8000)