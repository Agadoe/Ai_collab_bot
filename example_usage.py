"""
Example usage of the Collaborative AI Bot system
Demonstrates how to create projects and collaborate with multiple AI agents
"""

import asyncio
import os
from datetime import datetime
from project_manager import project_manager, Project
from ai_collaboration import AICollaborationEngine
from main import initialize_ai_agents, ai_agents

async def example_collaboration():
    """Example of how multiple AIs collaborate on a project"""
    
    print("🤝 Collaborative AI Example")
    print("=" * 40)
    
    # Initialize AI agents
    initialize_ai_agents()
    print(f"✅ Initialized {len(ai_agents)} AI agents")
    
    # Create collaboration engine
    collaboration_engine = AICollaborationEngine(ai_agents, project_manager)
    print("✅ Collaboration engine ready")
    
    # Create a sample project
    user_id = 12345  # Example user ID
    project_name = "Web Application Design"
    project_description = "Design a modern task management web application"
    selected_agents = list(ai_agents.keys())[:3]  # Use first 3 agents
    
    project = project_manager.create_project(
        user_id=user_id,
        name=project_name,
        description=project_description,
        selected_agents=selected_agents,
        tags=["web-design", "task-management", "collaboration"]
    )
    
    print(f"✅ Created project: {project.name}")
    print(f"🤖 AI Agents: {', '.join(project.ai_agents)}")
    
    # Example user request
    user_request = """
    I need to design a task management web application with the following features:
    - User authentication and authorization
    - Task creation, editing, and deletion
    - Task categorization and priority levels
    - Real-time collaboration
    - Mobile-responsive design
    - Integration with calendar systems
    
    Please provide a comprehensive design including:
    1. User interface mockups
    2. Technical architecture
    3. Database schema
    4. API design
    5. Security considerations
    """
    
    print(f"\n📝 User Request: {user_request[:100]}...")
    
    # Start collaboration
    print("\n🚀 Starting AI collaboration...")
    responses = await collaboration_engine.start_collaboration(project.id, user_request)
    
    # Display results
    print("\n" + "=" * 50)
    print("🤝 COLLABORATIVE RESULTS")
    print("=" * 50)
    
    for i, response in enumerate(responses, 1):
        print(f"\n📄 Response {i}:")
        print("-" * 30)
        print(response[:500] + "..." if len(response) > 500 else response)
    
    # Show project statistics
    stats = collaboration_engine.get_collaboration_stats(project.id)
    print(f"\n📊 Collaboration Statistics:")
    print(f"   Total contributions: {stats.get('total_contributions', 0)}")
    print(f"   Unique agents: {stats.get('unique_agents', 0)}")
    print(f"   Collaboration duration: {stats.get('collaboration_duration', 0):.2f} seconds")
    
    # Show project info
    project_stats = project_manager.get_project_stats(project.id)
    print(f"\n📈 Project Statistics:")
    print(f"   Total tasks: {project_stats.get('total_tasks', 0)}")
    print(f"   Completion rate: {project_stats.get('completion_rate', 0):.1f}%")
    print(f"   Total messages: {project_stats.get('total_messages', 0)}")
    print(f"   Days active: {project_stats.get('days_active', 0)}")

def example_project_management():
    """Example of project management features"""
    
    print("\n📋 Project Management Example")
    print("=" * 40)
    
    # Create multiple projects
    user_id = 12345
    
    projects = [
        {
            "name": "AI Research Paper",
            "description": "Write a research paper on AI collaboration",
            "agents": ["openai_gpt4", "deepseek"],
            "tags": ["research", "academic", "ai"]
        },
        {
            "name": "Creative Story",
            "description": "Create an interactive fantasy story",
            "agents": ["groq_llama", "openai_gpt4"],
            "tags": ["creative", "storytelling", "fantasy"]
        },
        {
            "name": "Code Review",
            "description": "Review and improve Python codebase",
            "agents": ["openai_gpt35", "openai_gpt4"],
            "tags": ["code", "review", "python"]
        }
    ]
    
    created_projects = []
    for project_data in projects:
        project = project_manager.create_project(
            user_id=user_id,
            name=project_data["name"],
            description=project_data["description"],
            selected_agents=project_data["agents"],
            tags=project_data["tags"]
        )
        created_projects.append(project)
        print(f"✅ Created: {project.name}")
    
    # Add tasks to first project
    first_project = created_projects[0]
    
    tasks = [
        {
            "title": "Literature Review",
            "description": "Review existing research on AI collaboration",
            "agents": ["deepseek"]
        },
        {
            "title": "Methodology Design",
            "description": "Design research methodology",
            "agents": ["openai_gpt4"]
        },
        {
            "title": "Data Analysis",
            "description": "Analyze research data",
            "agents": ["openai_gpt4", "deepseek"]
        }
    ]
    
    print(f"\n📝 Adding tasks to {first_project.name}:")
    for task_data in tasks:
        task = project_manager.add_task(
            project_id=first_project.id,
            title=task_data["title"],
            description=task_data["description"],
            assigned_agents=task_data["agents"]
        )
        if task:
            print(f"   ✅ Added task: {task.title}")
        else:
            print(f"   ❌ Failed to add task: {task_data['title']}")
    
    # Add milestone
    milestone = project_manager.add_milestone(
        project_id=first_project.id,
        title="Research Phase Complete",
        description="Complete initial research and analysis phase",
        due_date=datetime.now().replace(day=datetime.now().day + 7)  # 1 week from now
    )
    if milestone:
        print(f"   🎯 Added milestone: {milestone.title}")
    else:
        print(f"   ❌ Failed to add milestone")
    
    # Show user's projects
    user_projects = project_manager.get_user_projects(user_id)
    print(f"\n📋 User has {len(user_projects)} projects:")
    for project in user_projects:
        stats = project_manager.get_project_stats(project.id)
        print(f"   📁 {project.name}: {stats.get('total_tasks', 0)} tasks, {stats.get('completion_rate', 0):.1f}% complete")

def example_ai_agent_roles():
    """Example showing different AI agent roles and capabilities"""
    
    print("\n🤖 AI Agent Roles Example")
    print("=" * 40)
    
    initialize_ai_agents()
    
    for agent_name, agent in ai_agents.items():
        print(f"\n🤖 {agent.name}")
        print(f"   Role: {agent.role}")
        print(f"   Description: {agent.description}")
        print(f"   Engine: {agent.engine}")
        print(f"   Model: {agent.model}")
        print(f"   Temperature: {agent.temperature}")
        print(f"   Max Tokens: {agent.max_tokens}")
    
    print(f"\n💡 Each AI agent has a specific role and expertise:")
    print("   • GPT-4: Advanced reasoning and problem-solving")
    print("   • GPT-3.5: Fast code generation and debugging")
    print("   • Llama-3: Creative content generation")
    print("   • DeepSeek: Research and analysis")
    print("   • xAI: Specialized domain expertise")

if __name__ == "__main__":
    print("🚀 Collaborative AI Bot Examples")
    print("=" * 50)
    
    # Run examples
    try:
        # Example 1: AI Agent Roles
        example_ai_agent_roles()
        
        # Example 2: Project Management
        example_project_management()
        
        # Example 3: Collaboration (requires API keys)
        print("\n" + "=" * 50)
        print("⚠️  Note: Collaboration example requires valid API keys")
        print("   Set environment variables to run full collaboration:")
        print("   - OPENAI_API_KEY")
        print("   - GROQ_API_KEY")
        print("   - DEEPSEEK_API_KEY")
        print("   - XAI_API_KEY")
        
        # Check if we have any API keys
        api_keys = [
            os.getenv('OPENAI_API_KEY'),
            os.getenv('GROQ_API_KEY'),
            os.getenv('DEEPSEEK_API_KEY'),
            os.getenv('XAI_API_KEY')
        ]
        
        if any(api_keys):
            print("\n✅ API keys found! Running collaboration example...")
            asyncio.run(example_collaboration())
        else:
            print("\n❌ No API keys found. Skipping collaboration example.")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("   Make sure all dependencies are installed and configured correctly.")
    
    print("\n✅ Examples completed!")
    print("\nTo use the full bot:")
    print("1. Set up your environment variables")
    print("2. Run: python main.py")
    print("3. Send /start to your Telegram bot")