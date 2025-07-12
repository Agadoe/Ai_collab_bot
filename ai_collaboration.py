"""
AI Collaboration Engine for Multi-Agent Coordination
Handles collaborative workflows, agent communication, and task distribution
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class CollaborationTask:
    id: str
    title: str
    description: str
    assigned_agents: List[str]
    dependencies: List[str]  # List of task IDs this task depends on
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    priority: int  # 1-5, where 5 is highest priority
    estimated_duration: int  # in minutes
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    agent_results: Optional[Dict[str, str]] = None  # agent_name -> result

@dataclass
class AgentContribution:
    agent_name: str
    role: str
    contribution: str
    confidence: float  # 0.0-1.0
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AICollaborationEngine:
    def __init__(self, ai_agents: Dict[str, Any], project_manager):
        self.ai_agents = ai_agents
        self.project_manager = project_manager
        self.active_collaborations: Dict[str, List[CollaborationTask]] = {}
        self.agent_contributions: Dict[str, List[AgentContribution]] = {}
    
    async def start_collaboration(self, project_id: str, user_request: str) -> List[str]:
        """Start a collaborative session with multiple AI agents"""
        if project_id not in self.project_manager.projects:
            return ["Error: Project not found"]
        
        project = self.project_manager.get_project(project_id)
        if not project:
            return ["Error: Project not found"]
        
        # Create collaboration tasks based on the request
        tasks = await self._create_collaboration_tasks(project, user_request)
        self.active_collaborations[project_id] = tasks
        
        # Execute tasks in parallel where possible
        responses = await self._execute_collaboration_tasks(project_id, tasks)
        
        # Generate final collaborative response
        final_response = await self._synthesize_collaborative_response(project_id, responses)
        
        return [final_response]
    
    async def _create_collaboration_tasks(self, project: Any, user_request: str) -> List[CollaborationTask]:
        """Create tasks for different AI agents based on their roles"""
        tasks = []
        
        # Analyze the request and create role-specific tasks
        for agent_name in project.ai_agents:
            if agent_name in self.ai_agents:
                agent = self.ai_agents[agent_name]
                
                # Create task based on agent role
                task = CollaborationTask(
                    id=f"task_{len(tasks)}",
                    title=f"{agent.name} Analysis",
                    description=f"Analyze the request from the perspective of {agent.role}",
                    assigned_agents=[agent_name],
                    dependencies=[],
                    status='pending',
                    priority=3,
                    estimated_duration=2,
                    created_at=datetime.now(),
                    agent_results={}
                )
                tasks.append(task)
        
        # Add a synthesis task that depends on all other tasks
        synthesis_task = CollaborationTask(
            id=f"task_{len(tasks)}",
            title="Collaborative Synthesis",
            description="Combine all agent contributions into a unified response",
            assigned_agents=project.ai_agents,
            dependencies=[task.id for task in tasks],
            status='pending',
            priority=5,
            estimated_duration=3,
            created_at=datetime.now(),
            agent_results={}
        )
        tasks.append(synthesis_task)
        
        return tasks
    
    async def _execute_collaboration_tasks(self, project_id: str, tasks: List[CollaborationTask]) -> Dict[str, str]:
        """Execute collaboration tasks with proper dependency management"""
        results = {}
        
        # Execute independent tasks first
        independent_tasks = [task for task in tasks if not task.dependencies]
        dependent_tasks = [task for task in tasks if task.dependencies]
        
        # Execute independent tasks in parallel
        if independent_tasks:
            independent_results = await asyncio.gather(
                *[self._execute_task(project_id, task) for task in independent_tasks]
            )
            for task, result in zip(independent_tasks, independent_results):
                results[task.id] = result
                task.status = 'completed'
                task.result = result
        
        # Execute dependent tasks
        for task in dependent_tasks:
            # Check if all dependencies are completed
            if all(dep_id in results for dep_id in task.dependencies):
                result = await self._execute_task(project_id, task)
                results[task.id] = result
                task.status = 'completed'
                task.result = result
        
        return results
    
    async def _execute_task(self, project_id: str, task: CollaborationTask) -> str:
        """Execute a single collaboration task"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return "Error: Project not found"
        
        # Get project context
        context = self._get_project_context(project)
        
        # Execute task with each assigned agent
        agent_results = {}
        for agent_name in task.assigned_agents:
            if agent_name in self.ai_agents:
                agent = self.ai_agents[agent_name]
                
                # Create role-specific prompt
                prompt = self._create_task_prompt(task, agent, context)
                
                # Query the agent
                result = await self._query_agent(agent_name, prompt, context)
                agent_results[agent_name] = result
                
                # Record contribution
                contribution = AgentContribution(
                    agent_name=agent_name,
                    role=agent.role,
                    contribution=result,
                    confidence=0.8,  # Default confidence
                    timestamp=datetime.now()
                )
                
                if project_id not in self.agent_contributions:
                    self.agent_contributions[project_id] = []
                self.agent_contributions[project_id].append(contribution)
        
        # Combine results if multiple agents
        if len(agent_results) == 1:
            return list(agent_results.values())[0]
        else:
            return self._combine_agent_results(agent_results, task)
    
    def _create_task_prompt(self, task: CollaborationTask, agent: Any, context: str) -> str:
        """Create a prompt specific to the task and agent role"""
        return f"""
Context: {context}

Task: {task.title}
Description: {task.description}

As {agent.name} ({agent.role}), please provide your expertise and analysis for this task.
Consider your specific role: {agent.description}

Please provide a comprehensive response that leverages your unique capabilities.
"""
    
    async def _query_agent(self, agent_name: str, prompt: str, context: str) -> str:
        """Query a specific AI agent"""
        # This would integrate with the main AI query system
        # For now, return a placeholder
        return f"Response from {agent_name}: {prompt[:50]}..."
    
    def _combine_agent_results(self, agent_results: Dict[str, str], task: CollaborationTask) -> str:
        """Combine results from multiple agents"""
        combined = f"🤝 Collaborative Results for: {task.title}\n\n"
        
        for agent_name, result in agent_results.items():
            combined += f"**{agent_name}**:\n{result}\n\n"
        
        combined += "---\n"
        combined += "**Synthesis**: This collaborative effort combines multiple perspectives "
        combined += "to provide a comprehensive solution."
        
        return combined
    
    def _get_project_context(self, project: Any) -> str:
        """Get context from project history"""
        recent_messages = project.conversation_history[-5:] if project.conversation_history else []
        
        context = f"Project: {project.name}\nDescription: {project.description}\n\n"
        context += "Recent conversation:\n"
        
        for msg in recent_messages:
            context += f"{msg.get('sender', 'Unknown')}: {msg.get('content', '')[:100]}...\n"
        
        return context
    
    async def _synthesize_collaborative_response(self, project_id: str, task_results: Dict[str, str]) -> str:
        """Create a final synthesized response from all agent contributions"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return "Error: Project not found"
        
        # Get all contributions for this project
        contributions = self.agent_contributions.get(project_id, [])
        
        if not contributions:
            return "No agent contributions found"
        
        # Create synthesis prompt
        synthesis_prompt = f"""
Project: {project.name}
User Request: {project.conversation_history[-1]['content'] if project.conversation_history else 'Unknown'}

Agent Contributions:
"""
        
        for contrib in contributions:
            synthesis_prompt += f"\n{contrib.agent_name} ({contrib.role}):\n{contrib.contribution}\n"
        
        synthesis_prompt += "\nPlease synthesize these contributions into a coherent, comprehensive response."
        
        # Use the most capable agent for synthesis (GPT-4 if available)
        synthesis_agent = None
        for agent_name in ['openai_gpt4', 'openai_gpt35']:
            if agent_name in self.ai_agents:
                synthesis_agent = agent_name
                break
        
        if synthesis_agent:
            return await self._query_agent(synthesis_agent, synthesis_prompt, "")
        else:
            # Fallback: simple concatenation
            return self._simple_synthesis(contributions)
    
    def _simple_synthesis(self, contributions: List[AgentContribution]) -> str:
        """Simple synthesis when no synthesis agent is available"""
        synthesis = "🤝 Collaborative AI Response\n\n"
        
        for contrib in contributions:
            synthesis += f"**{contrib.agent_name}** ({contrib.role}):\n{contrib.contribution}\n\n"
        
        synthesis += "---\n"
        synthesis += "This response combines insights from multiple AI agents, each contributing "
        synthesis += "their unique expertise and perspective to provide a comprehensive solution."
        
        return synthesis
    
    def get_collaboration_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics about the collaboration"""
        contributions = self.agent_contributions.get(project_id, [])
        
        if not contributions:
            return {}
        
        agent_stats = {}
        for contrib in contributions:
            if contrib.agent_name not in agent_stats:
                agent_stats[contrib.agent_name] = {
                    'contributions': 0,
                    'total_confidence': 0.0,
                    'roles': set()
                }
            
            agent_stats[contrib.agent_name]['contributions'] += 1
            agent_stats[contrib.agent_name]['total_confidence'] += contrib.confidence
            agent_stats[contrib.agent_name]['roles'].add(contrib.role)
        
        # Calculate averages
        for agent_name, stats in agent_stats.items():
            stats['avg_confidence'] = stats['total_confidence'] / stats['contributions']
            stats['roles'] = list(stats['roles'])
        
        return {
            'total_contributions': len(contributions),
            'unique_agents': len(agent_stats),
            'agent_stats': agent_stats,
            'collaboration_duration': (contributions[-1].timestamp - contributions[0].timestamp).total_seconds() if len(contributions) > 1 else 0
        }