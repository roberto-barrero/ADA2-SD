from flask import Blueprint, jsonify, request, render_template

# Lista de recursos
from allResources import recursos

# Creamos un objeto Blueprint para tus rutas
resources_bp = Blueprint('resources', __name__)

# Obtener todos los recursos
@resources_bp.route('/recursos', methods=['GET'])
def obtener_recursos():
    return render_template('resources.html', resources=recursos)

# Buscar un recurso por ID
@resources_bp.route('/recursos/<int:id>', methods=['GET'])
def buscar_recurso(id):
    recurso = [recurso for recurso in recursos if recurso['id'] == id]
    if len(recurso) == 0:
        return jsonify({'mensaje': 'Recurso no encontrado'}), 404
    return jsonify(recurso[0])

# Agregar un nuevo recurso
@resources_bp.route('/recursos', methods=['POST'])
def agregar_recurso():
    nuevo_recurso = {
        'id': recursos[-1]['id'] + 1,
        'titulo': request.json['titulo'],
        'tipo': request.json['tipo'],
        'descripcion': request.json['descripcion'],
        'url': request.json['url']
    }
    recursos.append(nuevo_recurso)
    return jsonify(nuevo_recurso), 201

# Editar un recurso existente
@resources_bp.route('/recursos/<int:id>', methods=['PUT'])
def editar_recurso(id):
    recurso = [recurso for recurso in recursos if recurso['id'] == id]
    if len(recurso) == 0:
        return jsonify({'mensaje': 'Recurso no encontrado'}), 404
    recurso = recurso[0]
    recurso['titulo'] = request.json.get('titulo', recurso['titulo'])
    recurso['tipo'] = request.json.get('tipo', recurso['tipo'])
    recurso['descripcion'] = request.json.get('descripcion', recurso['descripcion'])
    recurso['url'] = request.json.get('url', recurso['url'])
    return jsonify(recurso)

# Borrar un recurso existente
@resources_bp.route('/recursos/<int:id>', methods=['DELETE'])
def borrar_recurso(id):
    recurso = [recurso for recurso in recursos if recurso['id'] == id]
    if len(recurso) == 0:
        return jsonify({'mensaje': 'Recurso no encontrado'}), 404
    recursos.remove(recurso[0])
    return jsonify({'mensaje': 'Recurso eliminado correctamente'})

# Se crea una función para registrar las rutas
def registrar_rutas(app):
    app.register_blueprint(resources_bp)

# Se devuelve el objeto Blueprint al final del archivo
    return app