"""
Project Management Module for Collaborative AI Bot
Handles project creation, management, and collaboration workflows
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ProjectTask:
    id: str
    title: str
    description: str
    assigned_agents: List[str]
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[str] = None

@dataclass
class ProjectMilestone:
    id: str
    title: str
    description: str
    due_date: datetime
    status: str  # 'pending', 'completed'
    tasks: List[str]  # List of task IDs

class ProjectManager:
    def __init__(self, storage_path: str = "projects"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.projects: Dict[str, 'Project'] = {}
        self.load_projects()
    
    def create_project(self, user_id: int, name: str, description: str, 
                      selected_agents: List[str], tags: Optional[List[str]] = None) -> 'Project':
        """Create a new collaborative project"""
        project_id = str(uuid.uuid4())
        
        project = Project(
            id=project_id,
            name=name,
            description=description,
            created_by=user_id,
            created_at=datetime.now(),
            status='active',
            ai_agents=selected_agents,
            conversation_history=[],
            tasks=[],
            milestones=[],
            tags=tags or [],
            current_task=None,
            last_updated=datetime.now()
        )
        
        self.projects[project_id] = project
        self.save_project(project)
        return project
    
    def get_project(self, project_id: str) -> Optional['Project']:
        """Get a project by ID"""
        return self.projects.get(project_id)
    
    def get_user_projects(self, user_id: int) -> List['Project']:
        """Get all projects for a user"""
        return [p for p in self.projects.values() if p.created_by == user_id]
    
    def update_project(self, project_id: str, **kwargs) -> bool:
        """Update project properties"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.last_updated = datetime.now()
        self.save_project(project)
        return True
    
    def add_task(self, project_id: str, title: str, description: str, 
                 assigned_agents: List[str]) -> Optional[ProjectTask]:
        """Add a new task to a project"""
        if project_id not in self.projects:
            return None
        
        task = ProjectTask(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            assigned_agents=assigned_agents,
            status='pending',
            created_at=datetime.now()
        )
        
        self.projects[project_id].tasks.append(task)
        self.save_project(self.projects[project_id])
        return task
    
    def complete_task(self, project_id: str, task_id: str, result: str) -> bool:
        """Mark a task as completed"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        for task in project.tasks:
            if task.id == task_id:
                task.status = 'completed'
                task.completed_at = datetime.now()
                task.result = result
                self.save_project(project)
                return True
        
        return False
    
    def add_milestone(self, project_id: str, title: str, description: str, 
                     due_date: datetime) -> Optional[ProjectMilestone]:
        """Add a milestone to a project"""
        if project_id not in self.projects:
            return None
        
        milestone = ProjectMilestone(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            due_date=due_date,
            status='pending',
            tasks=[]
        )
        
        self.projects[project_id].milestones.append(milestone)
        self.save_project(self.projects[project_id])
        return milestone
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get project statistics"""
        if project_id not in self.projects:
            return {}
        
        project = self.projects[project_id]
        
        total_tasks = len(project.tasks)
        completed_tasks = len([t for t in project.tasks if t.status == 'completed'])
        total_messages = len(project.conversation_history)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_messages': total_messages,
            'ai_agents_count': len(project.ai_agents),
            'days_active': (datetime.now() - project.created_at).days
        }
    
    def save_project(self, project: 'Project') -> None:
        """Save project to storage"""
        project_file = self.storage_path / f"{project.id}.json"
        
        # Convert project to dict, handling datetime objects
        project_dict = asdict(project)
        project_dict['created_at'] = project.created_at.isoformat()
        project_dict['last_updated'] = project.last_updated.isoformat() if project.last_updated else None
        
        # Handle tasks
        project_dict['tasks'] = []
        for task in project.tasks:
            task_dict = asdict(task)
            task_dict['created_at'] = task.created_at.isoformat()
            task_dict['completed_at'] = task.completed_at.isoformat() if task.completed_at else None
            project_dict['tasks'].append(task_dict)
        
        # Handle milestones
        project_dict['milestones'] = []
        for milestone in project.milestones:
            milestone_dict = asdict(milestone)
            milestone_dict['due_date'] = milestone.due_date.isoformat()
            project_dict['milestones'].append(milestone_dict)
        
        with open(project_file, 'w') as f:
            json.dump(project_dict, f, indent=2)
    
    def load_projects(self) -> None:
        """Load all projects from storage"""
        for project_file in self.storage_path.glob("*.json"):
            try:
                with open(project_file, 'r') as f:
                    project_dict = json.load(f)
                
                # Convert back to Project object
                project = self._dict_to_project(project_dict)
                self.projects[project.id] = project
            except Exception as e:
                print(f"Error loading project {project_file}: {e}")
    
    def _dict_to_project(self, project_dict: Dict) -> 'Project':
        """Convert dictionary back to Project object"""
        # Convert datetime strings back to datetime objects
        project_dict['created_at'] = datetime.fromisoformat(project_dict['created_at'])
        if project_dict.get('last_updated'):
            project_dict['last_updated'] = datetime.fromisoformat(project_dict['last_updated'])
        
        # Convert tasks
        tasks = []
        for task_dict in project_dict.get('tasks', []):
            task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
            if task_dict.get('completed_at'):
                task_dict['completed_at'] = datetime.fromisoformat(task_dict['completed_at'])
            tasks.append(ProjectTask(**task_dict))
        project_dict['tasks'] = tasks
        
        # Convert milestones
        milestones = []
        for milestone_dict in project_dict.get('milestones', []):
            milestone_dict['due_date'] = datetime.fromisoformat(milestone_dict['due_date'])
            milestones.append(ProjectMilestone(**milestone_dict))
        project_dict['milestones'] = milestones
        
        return Project(**project_dict)

# Update the Project dataclass to include new fields
@dataclass
class Project:
    id: str
    name: str
    description: str
    created_by: int
    created_at: datetime
    status: str  # 'active', 'completed', 'archived'
    ai_agents: List[str]  # List of AI agent names
    conversation_history: List[Dict]
    tasks: List[ProjectTask]
    milestones: List[ProjectMilestone]
    tags: List[str]
    current_task: Optional[str] = None
    last_updated: Optional[datetime] = None

# Global project manager instance
project_manager = ProjectManager()