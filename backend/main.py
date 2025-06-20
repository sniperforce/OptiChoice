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
        print(f"Creating project with data: {data}")
        
        project = controller.new_project(
            name=data.get('name', 'New Project'),
            description=data.get('description', ''),
            decision_maker=data.get('decision_maker', '')
        )
        print(f"Project created with ID: {project.id}")
        
        # Save directly to ensure it exists
        file_path = os.path.join(repository._base_dir, f"project_{project.id}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"Project saved to: {file_path}")
        
        return jsonify({
            'id': project.id, 
            'name': project.name,
            'description': project.description,
            'decision_maker': project.decision_maker
        }), 201
        
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        import traceback
        traceback.print_exc()
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

@app.route('/api/projects/<project_id>/save-complete', methods=['POST'])
def save_project_complete(project_id):
    """Save a complete project with alternatives and criteria from frontend"""
    try:
        # Load the project
        project = controller.load_project(project_id)
        if project is None:
            return jsonify({'error': f"Project {project_id} not found"}), 404
        
        # Get data from request safely
        data = {}
        try:
            if request.is_json:
                data = request.json or {}
        except Exception:
            data = {}
        
        # If alternatives and criteria are provided, update the project
        if 'alternatives' in data:
            # Remove existing alternatives first
            for alt in list(project.alternatives):
                controller.remove_alternative(alt.id)
            
            # Add new alternatives
            for alt_data in data['alternatives']:
                controller.add_alternative(
                    id=alt_data['id'],
                    name=alt_data['name'],
                    description=alt_data.get('description', ''),
                    metadata=alt_data.get('metadata', {})
                )
        
        if 'criteria' in data:
            # Remove existing criteria first
            for crit in list(project.criteria):
                controller.remove_criteria(crit.id)
            
            # Add new criteria
            for crit_data in data['criteria']:
                controller.add_criteria(
                    id=crit_data['id'],
                    name=crit_data['name'],
                    description=crit_data.get('description', ''),
                    optimization_type=crit_data.get('optimization_type', 'maximize'),
                    scale_type=crit_data.get('scale_type', 'quantitative'),
                    weight=float(crit_data.get('weight', 1.0)),
                    unit=crit_data.get('unit', ''),
                    metadata=crit_data.get('metadata', {})
                )
        
        # Try to save the project
        try:
            controller.save_project()
            return jsonify({'success': True, 'message': 'Project saved successfully'}), 200
        except Exception as save_error:
            # If validation fails, try direct save
            print(f"Validation failed, trying direct save: {save_error}")
            
            # Direct save to disk bypassing validation
            file_path = os.path.join(repository._base_dir, f"project_{project_id}.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)
            
            return jsonify({'success': True, 'message': 'Project saved (direct mode)'}), 200
            
    except Exception as e:
        print(f"Error in save_project_complete: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    try:
        project = controller.load_project(project_id)
        
        if project is None:
            return jsonify({'error': f"Project {project_id} not found"}), 404
        
        data = request.json
        
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'decision_maker' in data:
            project.decision_maker = data['decision_maker']

        if 'alternatives' in data:

            for alt in list(project.alternatives):
                controller.remove_alternative(alt.id)

            for alt_data in data['alternatives']:
                controller.add_alternative(
                    id=alt_data['id'],
                    name=alt_data['name'],
                    description=alt_data.get('description', ''),
                    metadata=alt_data.get('metadata', {})
                )

        if 'criteria' in data:

            for crit in list(project.criteria):
                controller.remove_criteria(crit.id)

            for crit_data in data['criteria']:
                controller.add_criteria(
                    id=crit_data['id'],
                    name=crit_data['name'],
                    description=crit_data.get('description', ''),
                    optimization_type=crit_data.get('optimization_type', 'maximize'),
                    scale_type=crit_data.get('scale_type', 'quantitative'),
                    weight=float(crit_data.get('weight', 1.0)),
                    unit=crit_data.get('unit', ''),
                    metadata=crit_data.get('metadata', {})
                )             
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'decision_maker': project.decision_maker,
            'n_alternatives': len(project.alternatives),
            'n_criteria': len(project.criteria)
        }), 200
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

@app.route('/api/projects/<project_id>/alternatives', methods=['GET'])
def get_alternatives(project_id):
    try:
        controller.load_project(project_id)
        alternatives = controller.get_all_alternatives()
        return jsonify(alternatives)
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

@app.route('/api/projects/<project_id>/criteria/<criteria_id>', methods=['GET'])
def get_criteria_by_id(project_id, criteria_id):
    try:
        controller.load_project(project_id)
        criteria = controller.get_criteria(criteria_id)
        return jsonify(criteria)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Routes for decision matrix
@app.route('/api/projects/<project_id>/matrix', methods=['GET'])
def get_decision_matrix(project_id):
    """Get the decision matrix for a project"""
    try:
        controller.load_project(project_id)
        
        # Usar el método corregido que incluye la configuración
        matrix_data = controller.get_decision_matrix()
        
        # Log para debug
        print(f"Returning matrix data with config: {matrix_data.get('criteria_config', {})}")
        
        return jsonify(matrix_data)
        
    except Exception as e:
        print(f"Error getting decision matrix: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/matrix/create', methods=['POST'])
def create_decision_matrix(project_id):
    """Create a new decision matrix for a project"""
    try:
        controller.load_project(project_id)
        
        # Usar el método sin parámetros
        controller.create_decision_matrix()
        
        # Guardar inmediatamente
        controller.save_project()
        
        return jsonify({
            'success': True,
            'message': 'Matrix created successfully'
        }), 201
        
    except Exception as e:
        print(f"Error creating decision matrix: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/matrix', methods=['POST'])
def save_decision_matrix(project_id):
    """Save the decision matrix for a project"""
    try:
        controller.load_project(project_id)
        
        data = request.json if request.json else {}
        
        # Log para debug
        print(f"Saving matrix for project {project_id}")
        print(f"Matrix data keys: {list(data.get('matrix_data', {}).keys())[:5]}")
        print(f"Criteria config: {data.get('criteria_config', {})}")
        
        # Save matrix data
        success = controller.save_decision_matrix(
            matrix_data=data.get('matrix_data', {}),
            criteria_config=data.get('criteria_config', {})
        )
        
        if success:
            # Forzar guardado inmediato
            controller.save_project()
            
            # Esperar un momento para asegurar persistencia
            import time
            time.sleep(0.1)
            
            return jsonify({'success': True, 'message': 'Matrix saved successfully'}), 200
        else:
            return jsonify({'error': 'Failed to save matrix'}), 500
            
    except Exception as e:
        print(f"Error saving decision matrix: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/matrix/values', methods=['PUT'])
def update_matrix_values(project_id):
    """Update specific values in the decision matrix"""
    try:
        controller.load_project(project_id)
        
        data = request.json if request.json else {}
        
        # Create matrix if it doesn't exist
        try:
            controller.get_decision_matrix()
        except ValueError:
            # Matrix doesn't exist, create it
            controller.create_decision_matrix()
        
        # Update individual matrix values
        for update in data.get('updates', []):
            controller.set_matrix_value(
                alternative_id=update.get('alternative_id'),
                criteria_id=update.get('criteria_id'),
                value=float(update.get('value', 0.0))
            )
        
        controller.save_project()
        
        return jsonify({'success': True, 'message': 'Matrix values updated'}), 200
        
    except Exception as e:
        print(f"Error updating matrix values: {str(e)}")
        import traceback
        traceback.print_exc()
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