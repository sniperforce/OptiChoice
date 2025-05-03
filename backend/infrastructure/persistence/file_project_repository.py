"""
Module that implements a file-based project repository.

This repository allows saving and retrieving projects using JSON files as
the persistence mechanism.
"""
import os
import json
import glob
from typing import Dict, List, Optional, Any
import re

from domain.repositories.project_repository import ProjectRepository
from domain.entities.project import Project
from utils.exceptions import RepositoryError


class FileProjectRepository(ProjectRepository):
    
    def __init__(self, base_dir: str = "data/projects"):
        self._base_dir = base_dir
        
        try:
            os.makedirs(self._base_dir, exist_ok=True)
        except Exception as e:
            raise RepositoryError(
                message=f"Error creating repository directory: {str(e)}",
                cause=e
            )
    
    def save(self, project: Project) -> Project:
        try:
            project_dict = project.to_dict()
            
            file_path = os.path.join(self._base_dir, f"project_{project.id}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_dict, f, indent=2, ensure_ascii=False)
            
            return project
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error saving project to file: {str(e)}",
                cause=e
            )
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        try:
            file_path = os.path.join(self._base_dir, f"project_{project_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                project_dict = json.load(f)
            
            return Project.from_dict(project_dict)
            
        except json.JSONDecodeError as e:
            raise RepositoryError(
                message=f"Error decoding JSON for project {project_id}: {str(e)}",
                cause=e
            )
        except Exception as e:
            raise RepositoryError(
                message=f"Error retrieving project {project_id}: {str(e)}",
                cause=e
            )
        
    def get_all(self) -> List[Project]:
        try:
            projects = []
            
            pattern = os.path.join(self._base_dir, "project_*.json")
            for file_path in glob.glob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_dict = json.load(f)
                    
                    project = Project.from_dict(project_dict)
                    projects.append(project)
                    
                except Exception as e:
                    print(f"Error loading project from {file_path}: {str(e)}")
            
            return projects
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error retrieving all projects: {str(e)}",
                cause=e
            )
    
    def delete(self, project_id: str) -> bool:
        try:
            file_path = os.path.join(self._base_dir, f"project_{project_id}.json")
            
            if not os.path.exists(file_path):
                return False
            
            os.remove(file_path)
            
            return True
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error deleting project {project_id}: {str(e)}",
                cause=e
            )
    
    def exists(self, project_id: str) -> bool:
        try:
            file_path = os.path.join(self._base_dir, f"project_{project_id}.json")
            
            return os.path.exists(file_path)
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error checking existence of project {project_id}: {str(e)}",
                cause=e
            )
    
    def search(self, query: str) -> List[Project]:
        try:
            query_lower = query.lower()
            results = []
            
            all_projects = self.get_all()
            
            for project in all_projects:
                if (query_lower in project.name.lower() or 
                    query_lower in project.description.lower()):
                    results.append(project)
            
            return results
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error searching projects: {str(e)}",
                cause=e
            )
    
    def backup_all(self, backup_dir: str) -> int:
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            pattern = os.path.join(self._base_dir, "project_*.json")
            file_paths = glob.glob(pattern)
            
            for src_path in file_paths:
                file_name = os.path.basename(src_path)
                dst_path = os.path.join(backup_dir, file_name)
                
                with open(src_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                
                with open(dst_path, 'w', encoding='utf-8') as dst_file:
                    dst_file.write(content)
            
            return len(file_paths)
            
        except Exception as e:
            raise RepositoryError(
                message=f"Error creating backup: {str(e)}",
                cause=e
            )
    
    def restore_from_backup(self, backup_dir: str, overwrite: bool = False) -> int:
        try:
            if not os.path.isdir(backup_dir):
                raise RepositoryError(
                    message=f"Backup directory does not exist: {backup_dir}"
                )
            
            pattern = os.path.join(backup_dir, "project_*.json")
            file_paths = glob.glob(pattern)
            
            restored_count = 0
            
            for src_path in file_paths:
                file_name = os.path.basename(src_path)
                dst_path = os.path.join(self._base_dir, file_name)
                
                if os.path.exists(dst_path) and not overwrite:
                    continue
                
                with open(src_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                
                with open(dst_path, 'w', encoding='utf-8') as dst_file:
                    dst_file.write(content)
                
                restored_count += 1
            
            return restored_count
            
        except RepositoryError as e:
            raise e
        except Exception as e:
            raise RepositoryError(
                message=f"Error restoring from backup: {str(e)}",
                cause=e
            )