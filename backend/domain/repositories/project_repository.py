from abc import ABC,abstractmethod
from typing import List, Optional

from domain.entities.project import Project

class ProjectRepository(ABC):
    
    @abstractmethod
    def save(self, project: Project) -> Project:
        pass
    
    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Project]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[Project]:
        pass
    
    @abstractmethod
    def delete(self, project_id: str) -> bool:
        pass
    
    @abstractmethod
    def exists(self, project_id: str) -> bool:
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Project]:
        pass