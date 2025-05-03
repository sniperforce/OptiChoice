"""
Main entry point for the MCDM system.

This module initializes all system components and provides
a REST API for the frontend to interact with the backend
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from infrastructure.persistence.file_project_repository import FileProjectRepository
from presentation.controllers.main_controller import MainController
from utils.exceptions import ServiceError

app = Flask(__name__, static_folder='frontend/build')

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

repository = FileProjectRepository()
controller = MainController(repository)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# Routes for the REST API
@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        projects = controller.get_all_projects()
        return jsonify(projects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/projects', methods=['POST'])
def create_project():
    try:
        data = request.json
        project = controller.new_project(
            name=data.get('name', 'New Project'),
            description=data.get('description', ''),
            decision_maker=data.get('decision_maker', '')
        )
        
        controller.save_project()
        
        return jsonify({'id': project.id, 'name': project.name}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Gets the information of a specific project."""
    try:
        project = controller.load_project(project_id)
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'decision_maker': project.decision_maker,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'n_alternatives': len(project.alternatives),
            'n_criteria': len(project.criteria),
            'n_results': len(project.results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/save', methods=['POST'])
def save_project_explicitly(project_id):
    """Explicitly save a project after all components have been added"""
    try:
        project = controller.load_project(project_id)
        
        if project is None:
            return jsonify({'error': f"Project {project_id} not found"}), 404
            
        controller.save_project()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/alternatives', methods=['POST'])
def add_alternative(project_id):
    try:
        project = controller.load_project(project_id)
        
        if project is None:
            return jsonify({'error': f"Project {project_id} not found"}), 404
        
        data = request.json
        
        alternative = controller.add_alternative(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description', ''),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'id': alternative.id,
            'name': alternative.name,
            'description': alternative.description
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/alternatives/<alternative_id>', methods=['GET'])
def get_alternative(project_id, alternative_id):
    try:
        controller.load_project(project_id)
        alternative = controller.get_alternative(alternative_id)
        return jsonify(alternative)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/alternatives/<alternative_id>', methods=['DELETE'])
def remove_alternative(project_id, alternative_id):
    try:
        controller.load_project(project_id)
        controller.remove_alternative(alternative_id)
        controller.save_project()
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Routes for criteria
@app.route('/api/projects/<project_id>/criteria', methods=['GET'])
def get_criteria(project_id):
    try:
        controller.load_project(project_id)
        criteria = controller.get_all_criteria()
        return jsonify(criteria)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/criteria', methods=['POST'])
def add_criteria(project_id):
    try:
        print(f"Loading project {project_id}")
        project = controller.load_project(project_id)
        
        if project is None:
            return jsonify({'error': f"Project {project_id} not found"}), 404

        data = request.json
        print(f"Adding criteria: {data}")

        criteria = controller.add_criteria(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description', ''),
            optimization_type=data.get('optimization_type', 'maximize'),
            scale_type=data.get('scale_type', 'quantitative'),
            weight=float(data.get('weight', 1.0)),
            unit=data.get('unit', ''),
            metadata=data.get('metadata')
        )
        
        #controller.save_project()
        
        return jsonify({
            'id': criteria.id,
            'name': criteria.name,
            'description': criteria.description,
            'optimization_type': criteria.optimization_type.value,
            'weight': criteria.weight
        }), 201
    except Exception as e:
        print(f"Error adding criteria: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/criteria/<criteria_id>', methods=['GET'])
def get_criteria_by_id(project_id, criteria_id):
    try:
        controller.load_project(project_id)
        criteria = controller.get_criteria(criteria_id)
        return jsonify(criteria)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/criteria/<criteria_id>', methods=['DELETE'])
def remove_criteria(project_id, criteria_id):
    try:
        controller.load_project(project_id)
        controller.remove_criteria(criteria_id)
        controller.save_project()
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Routes for decision matrix
@app.route('/api/projects/<project_id>/matrix', methods=['GET'])
def get_matrix(project_id):
    try:
        controller.load_project(project_id)
        matrix = controller.get_decision_matrix()
        return jsonify(matrix)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/matrix', methods=['POST'])
def create_matrix(project_id):
    try:
        controller.load_project(project_id)
        
        data = request.json
        matrix = controller.create_decision_matrix(
            name=data.get('name'),
            values=data.get('values')
        )
        
        controller.save_project()
        
        return jsonify(matrix), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/matrix/value', methods=['POST'])
def set_matrix_value(project_id):
    try:
        controller.load_project(project_id)
        
        data = request.json
        controller.set_matrix_value(
            alternative_id=data.get('alternative_id'),
            criteria_id=data.get('criteria_id'),
            value=float(data.get('value', 0.0))
        )
        
        controller.save_project()
        
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes for MCDM methods
@app.route('/api/methods', methods=['GET'])
def get_methods():
    try:
        methods = controller.get_available_methods()
        return jsonify(methods)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/methods/<method_name>/execute', methods=['POST'])
def execute_method(project_id, method_name):
    try:
        controller.load_project(project_id)
        
        data = request.json
        result = controller.execute_method(
            method_name=method_name,
            parameters=data.get('parameters')
        )
        
        controller.save_project()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/methods/execute-all', methods=['POST'])
def execute_all_methods(project_id):
    try:
        controller.load_project(project_id)
        
        data = request.json
        results = controller.execute_all_methods(
            parameters=data.get('parameters')
        )
        
        controller.save_project()
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/methods/compare', methods=['GET'])
def compare_methods(project_id):
    try:
        controller.load_project(project_id)
        
        method_names = request.args.get('methods', '').split(',')
        if method_names == ['']:
            method_names = None
            
        comparison = controller.compare_methods(method_names)
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/sensitivity', methods=['POST'])
def sensitivity_analysis(project_id):
    try:
        controller.load_project(project_id)
        
        data = request.json
        result = controller.perform_sensitivity_analysis(
            method_name=data.get('method_name'),
            criteria_id=data.get('criteria_id'),
            weight_range=(
                float(data.get('min_weight', 0.1)),
                float(data.get('max_weight', 1.0))
            ),
            steps=int(data.get('steps', 10))
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/results', methods=['GET'])
def get_all_results(project_id):
    try:
        controller.load_project(project_id)
        results = controller.get_all_results()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/projects/<project_id>/results/<method_name>', methods=['GET'])
def get_method_result(project_id, method_name):
    try:
        controller.load_project(project_id)
        result = controller.get_result(method_name)
        
        if result is None:
            return jsonify({'error': 'Result not found'}), 404
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Serve frontend application
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# Entry point
if __name__ == '__main__':
    app.run(debug=True)