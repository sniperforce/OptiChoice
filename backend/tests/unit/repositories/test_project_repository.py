import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime
from uuid import uuid4

from infrastructure.persistence.file_project_repository import FileProjectRepository
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from utils.exceptions import RepositoryError

class TestFileProjectRepository:
    
    @pytest.fixture
    def temp_dir(self):
        """Fixture providing a temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def repository(self, temp_dir):
        """Fixture providing a repository instance with temporary directory."""
        return FileProjectRepository(base_dir=temp_dir)
    
    @pytest.fixture
    def sample_project(self):
        """Fixture providing a sample project for testing."""
        project = Project(
            name="Test Project",
            description="Test Description",
            decision_maker="Test User"
        )
        # Add some alternatives and criteria
        project.add_alternative(Alternative(id="alt1", name="Alternative 1"))
        project.add_alternative(Alternative(id="alt2", name="Alternative 2"))
        project.add_criteria(Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE))
        project.add_criteria(Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE))
        return project
    
    def test_repository_initialization(self, temp_dir):
        """Test that repository creates the base directory on initialization."""
        repository = FileProjectRepository(base_dir=temp_dir)
        assert os.path.exists(temp_dir)
    
    def test_repository_initialization_error(self):
        """Test error handling when directory creation fails."""
        # Try to create repository in a non-existent path without write permissions
        invalid_path = "/invalid/path/that/does/not/exist"
        
        with pytest.raises(RepositoryError) as exc_info:
            FileProjectRepository(base_dir=invalid_path)
        
        assert "Error creating repository directory" in str(exc_info.value)
    
    def test_save_project(self, repository, sample_project, temp_dir):
        """Test saving a project to file."""
        saved_project = repository.save(sample_project)
        
        assert saved_project == sample_project
        
        # Verify file was created
        file_path = os.path.join(temp_dir, f"project_{sample_project.id}.json")
        assert os.path.exists(file_path)
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['id'] == sample_project.id
        assert data['name'] == sample_project.name
        assert data['description'] == sample_project.description
        assert len(data['alternatives']) == 2
        assert len(data['criteria']) == 2
    
    def test_save_project_error(self, sample_project):
        """Test error handling when saving fails."""
        # Create repository with invalid path
        repository = FileProjectRepository()
        # Set an invalid base directory to force error
        repository._base_dir = "/invalid/path"
        
        with pytest.raises(RepositoryError) as exc_info:
            repository.save(sample_project)
        
        assert "Error saving project to file" in str(exc_info.value)
    
    def test_get_by_id(self, repository, sample_project):
        """Test retrieving a project by ID."""
        # First save the project
        repository.save(sample_project)
        
        # Then retrieve it
        retrieved_project = repository.get_by_id(sample_project.id)
        
        assert retrieved_project is not None
        assert retrieved_project.id == sample_project.id
        assert retrieved_project.name == sample_project.name
        assert len(retrieved_project.alternatives) == 2
        assert len(retrieved_project.criteria) == 2
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent project."""
        non_existent_id = str(uuid4())
        
        result = repository.get_by_id(non_existent_id)
        
        assert result is None
    
    def test_get_by_id_invalid_json(self, repository, temp_dir):
        """Test error handling when JSON file is corrupted."""
        project_id = str(uuid4())
        file_path = os.path.join(temp_dir, f"project_{project_id}.json")
        
        # Create a corrupted JSON file
        with open(file_path, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(RepositoryError) as exc_info:
            repository.get_by_id(project_id)
        
        assert "Error decoding JSON" in str(exc_info.value)
    
    def test_get_all(self, repository, sample_project):
        """Test retrieving all projects."""
        # Create and save multiple projects
        project1 = sample_project
        project2 = Project(name="Project 2", description="Description 2")
        project3 = Project(name="Project 3", description="Description 3")
        
        repository.save(project1)
        repository.save(project2)
        repository.save(project3)
        
        # Retrieve all projects
        projects = repository.get_all()
        
        assert len(projects) == 3
        project_names = [p.name for p in projects]
        assert "Test Project" in project_names
        assert "Project 2" in project_names
        assert "Project 3" in project_names
    
    def test_get_all_empty_directory(self, repository):
        """Test get_all when directory is empty."""
        projects = repository.get_all()
        assert len(projects) == 0
    
    def test_get_all_with_invalid_files(self, repository, sample_project, temp_dir):
        """Test get_all with some invalid project files."""
        # Save a valid project
        repository.save(sample_project)
        
        # Create an invalid project file
        invalid_id = str(uuid4())
        invalid_file_path = os.path.join(temp_dir, f"project_{invalid_id}.json")
        with open(invalid_file_path, 'w') as f:
            f.write("invalid json content")
        
        # get_all should skip the invalid file and return only valid projects
        projects = repository.get_all()
        assert len(projects) == 1
        assert projects[0].id == sample_project.id
    
    def test_delete(self, repository, sample_project):
        """Test deleting a project."""
        # First save the project
        repository.save(sample_project)
        
        # Verify file exists
        file_path = os.path.join(repository._base_dir, f"project_{sample_project.id}.json")
        assert os.path.exists(file_path)
        
        # Delete the project
        result = repository.delete(sample_project.id)
        
        assert result is True
        assert not os.path.exists(file_path)
    
    def test_delete_non_existent(self, repository):
        """Test deleting a non-existent project."""
        non_existent_id = str(uuid4())
        
        result = repository.delete(non_existent_id)
        
        assert result is False
    
    def test_exists(self, repository, sample_project):
        """Test checking if a project exists."""
        # Project doesn't exist yet
        assert not repository.exists(sample_project.id)
        
        # Save the project
        repository.save(sample_project)
        
        # Now it should exist
        assert repository.exists(sample_project.id)
    
    def test_search(self, repository):
        """Test searching projects by query."""
        # Create projects with different names and descriptions
        project1 = Project(name="Alpha Project", description="First project")
        project2 = Project(name="Beta Test", description="Second project with alpha word")
        project3 = Project(name="Gamma Project", description="Third project")
        
        repository.save(project1)
        repository.save(project2)
        repository.save(project3)
        
        # Search for "alpha"
        results = repository.search("alpha")
        
        assert len(results) == 2
        project_names = [p.name for p in results]
        assert "Alpha Project" in project_names
        assert "Beta Test" in project_names  # Because description contains "alpha"
        
        # Search for "gamma"
        results = repository.search("gamma")
        assert len(results) == 1
        assert results[0].name == "Gamma Project"
    
    def test_search_case_insensitive(self, repository):
        """Test that search is case-insensitive."""
        project = Project(name="Test Project", description="Description")
        repository.save(project)
        
        # Search with different cases
        results_lower = repository.search("test")
        results_upper = repository.search("TEST")
        
        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert results_lower[0].id == results_upper[0].id
    
    def test_backup_all(self, repository, sample_project, temp_dir):
        """Test backing up all projects."""
        # Save some projects
        project1 = sample_project
        project2 = Project(name="Project 2")
        repository.save(project1)
        repository.save(project2)
        
        # Create backup directory
        backup_dir = os.path.join(temp_dir, "backup")
        
        # Perform backup
        count = repository.backup_all(backup_dir)
        
        assert count == 2
        assert os.path.exists(backup_dir)
        
        # Verify backup files exist
        backup_file1 = os.path.join(backup_dir, f"project_{project1.id}.json")
        backup_file2 = os.path.join(backup_dir, f"project_{project2.id}.json")
        assert os.path.exists(backup_file1)
        assert os.path.exists(backup_file2)
    
    def test_restore_from_backup(self, repository, sample_project, temp_dir):
        """Test restoring projects from backup."""
        # Create and save original project
        repository.save(sample_project)
        
        # Create backup
        backup_dir = os.path.join(temp_dir, "backup")
        repository.backup_all(backup_dir)
        
        # Delete original project
        repository.delete(sample_project.id)
        
        # Restore from backup
        restored_count = repository.restore_from_backup(backup_dir, overwrite=True)
        
        assert restored_count == 1
        
        # Verify project was restored
        restored_project = repository.get_by_id(sample_project.id)
        assert restored_project is not None
        assert restored_project.name == sample_project.name
    
    def test_restore_from_backup_no_overwrite(self, repository, sample_project, temp_dir):
        """Test restoring from backup without overwriting existing files."""
        # Save project
        repository.save(sample_project)
        
        # Create backup
        backup_dir = os.path.join(temp_dir, "backup")
        repository.backup_all(backup_dir)
        
        # Try to restore with overwrite=False
        restored_count = repository.restore_from_backup(backup_dir, overwrite=False)
        
        # No files should be restored since they already exist
        assert restored_count == 0
    
    def test_restore_from_invalid_backup_dir(self, repository):
        """Test error handling when backup directory doesn't exist."""
        invalid_backup_dir = "/invalid/backup/dir"
        
        with pytest.raises(RepositoryError) as exc_info:
            repository.restore_from_backup(invalid_backup_dir)
        
        assert "Backup directory does not exist" in str(exc_info.value)
    
    def test_concurrent_operations(self, repository):
        """Test concurrent save and retrieve operations."""
        # Create multiple projects
        projects = [Project(name=f"Project {i}") for i in range(5)]
        
        # Save all projects
        for project in projects:
            repository.save(project)
        
        # Retrieve all projects and verify
        retrieved_projects = repository.get_all()
        assert len(retrieved_projects) == 5
        
        # Delete half of them
        for i in range(0, 5, 2):
            repository.delete(projects[i].id)
        
        # Verify remaining
        remaining_projects = repository.get_all()
        assert len(remaining_projects) == 2