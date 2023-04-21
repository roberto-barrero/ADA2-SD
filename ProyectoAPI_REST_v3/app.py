from flask import Flask, jsonify, abort, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from resources import resources_bp, registrar_rutas
# Importar librerías para crear la solicitud SOAP
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}

app.secret_key = 'mysecretkey'

# Registramos las rutas de los recursos en la aplicación Flask
registrar_rutas(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(128))

# Send SOAP request to the database service for the username based on the auth token
def get_username():
    auth_token = session.get('auth_token')
    print(auth_token)
    username = ''
    # Redirecciona a la página de login si no hay un token de autenticación
    if auth_token is None:
        return False
    else:
        # Crear la solicitud SOAP al servicio de base de datos
        soap_request = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:5000/user-service'})
        soap_body = ET.SubElement(soap_request, 'ns0:Body')
        body = ET.Element('ns1:getUserRequest')
        auth_token_element = ET.SubElement(body, 'ns1:authToken').text = auth_token
        soap_body.append(body)

        # Enviar la solicitud SOAP al servicio de base de datos
        response = requests.post('http://localhost:5000/getUser', data=ET.tostring(soap_request), headers={'Content-Type': 'text/xml'})

        # Procesar la respuesta SOAP del servicio de base de datos
        soap_response_xml = ET.fromstring(response.text)

        user_element = soap_response_xml.find('.//ns1:getUserResponse', {"ns1": "http://localhost:5000/user-service"})
        username_element = user_element.find('.//ns1:username', {"ns1": "http://localhost:5000/user-service"})
        username = username_element.text
    return username

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Login page (GET and POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Crear la solicitud SOAP al servicio de base de datos
        soap_request = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:8000/authentication'})
        soap_body = ET.SubElement(soap_request, 'ns0:Body')
        body = ET.Element('ns1:LoginRequest')
        username = ET.SubElement(body, 'ns1:username').text = username
        password = ET.SubElement(body, 'ns1:password').text = password
        soap_body.append(body)

        # Print the SOAP request to the database service
        print(str(ET.tostring(soap_request)))

        # Enviar la solicitud SOAP al servicio de base de datos
        response = requests.post('http://localhost:8000/authentication', data=ET.tostring(soap_request), headers={'Content-Type': 'text/xml'})

        # Print the SOAP response from the database service
        print(response.text)

        # Procesar la respuesta SOAP del servicio de base de datos
        if response.status_code != 200:
            flash('Invalid username or password')
            return redirect(url_for('login'))
        else:
            soap_response_xml = ET.fromstring(response.text)

            password_element = soap_response_xml.find('.//ns1:LoginResponse', {"ns1": "http://localhost:8000/authentication"})
            auth_token_element = password_element.find('.//ns1:authToken', {"ns1": "http://localhost:8000/authentication"})
            auth_token = auth_token_element.text

            # Guardar el token de autenticación en la sesión
            session['auth_token'] = auth_token

        if username != '' and password != '':
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html')

# Register page (GET and POST)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']

        # Crear la solicitud SOAP al servicio de base de datos
        soap_request = ET.Element('ns0:Envelope', {'xmlns:ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'xmlns:ns1': 'http://localhost:5000/user-service'})
        soap_body = ET.SubElement(soap_request, 'ns0:Body')
        body = ET.Element('ns1:createUserRequest')
        user = ET.SubElement(body, 'ns1:user')
        username = ET.SubElement(user, 'ns1:username').text = username
        password = ET.SubElement(user, 'ns1:password').text = password
        name = ET.SubElement(user, 'ns1:name').text = name
        email = ET.SubElement(user, 'ns1:email').text = email
        soap_body.append(body)

        # Print the SOAP request to the database service
        print(str(ET.tostring(soap_request)))

        # Enviar la solicitud SOAP al servicio de base de datos
        response = requests.post('http://localhost:5000/createUser', data=ET.tostring(soap_request), headers={'Content-Type': 'text/xml'})

        # Print the SOAP response from the database service
        print("Response", response.text)

        # Procesar la respuesta SOAP del servicio de base de datos
        if response.status_code != 200:
            flash('Invalid username or password')
            return redirect(url_for('register'))
        else:
            soap_response_xml = ET.fromstring(response.text)

            password_element = soap_response_xml.find('.//ns1:createUserResponse', {"ns1": "http://localhost:5000/user-service"})
            user_element = password_element.find('.//ns1:user', {"ns1": "http://localhost:5000/user-service"})
            username = user_element.find('.//ns1:username', {"ns1": "http://localhost:5000/user-service"}).text

        if username != '':
            return redirect(url_for('login'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('index.html')

# Devuelve todas las tareas
@app.route('/tasks', methods=['GET'])
def get_tasks():
    
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    
    # Obtain the tasks from the database where the username column value is the same as the one in the session
    print(username)
    tasks = Task.query.filter(Task.username == username).all()

    result = []
    for task in tasks:
        task_data = {}
        task_data['id'] = task.id
        task_data['title'] = task.title
        task_data['description'] = task.description
        task_data['completed'] = task.completed
        result.append(task_data)
    #return jsonify(result)
    return render_template('tasks.html', tasks=tasks)

# Búsqueda por título
@app.route('/tasks/search')
def search_task():
    username = get_username()
    if not username:
        return redirect(url_for('login'))

    search_input = request.args.get('search_input')

    # Una busqueda por titulo y username
    tasks = Task.query.filter(Task.title.like(f'%{search_input}%'), Task.username == username).all()
    # tasks = Task.query.filter(Task.title.like(f'%{search_input}%')).all()
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'completed': task.completed
        })
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/completed', methods=['GET'])
def get_completed_tasks():
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    
    tasks = Task.query.filter(Task.completed.is_(True), Task.username == username).all()
    results = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed
        } for task in tasks
    ]
    return jsonify(results)

@app.route('/tasks/<int:task_id>')
def get_task(task_id):
    
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    
    task = Task.query.get(task_id)
    if task and task.username == username:
        return jsonify({'id': task.id, 'title': task.title, 'description': task.description, 'completed': task.completed})
    else:
        return jsonify({'error': 'Task not found'})

@app.route('/tasks/new_task')
def add_task_html():
    return render_template('addTask.html')

@app.route('/tasks/add_task', methods=['POST'])
def create_task():
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    
    data = request.get_json()
    new_task = Task(title=data['title'], description=data['description'], completed=data['completed'], username=username)
    db.session.add(new_task)
    db.session.commit()
    return {'id': new_task.id, 'title': new_task.title, 'description': new_task.description, 'completed': new_task.completed}

@app.route('/tasks/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    
    task = Task.query.get(task_id) if Task.query.get(task_id).username == username else abort(404)
    data = request.get_json()
    task.title = data['title']
    task.description = data['description']
    task.completed = data['completed']
    db.session.commit()
    return {'message': 'Task updated successfully'}
        
@app.route('/tasks/delete/<int:id>', methods=['POST'])
def delete_task(id):
    username = get_username()
    if not username:
        return redirect(url_for('login'))
    task = Task.query.get(id) if Task.query.get(id).username == username else abort(404)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('get_tasks'))

if __name__ == '__main__':
    app.run(debug=True, port=9000)

