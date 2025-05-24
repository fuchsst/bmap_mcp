# examples/complete_workflow_example.py
"""
Complete workflow example demonstrating BMAD MCP Server usage.

This example shows how to use the BMAD MCP Server to implement a complete
project development workflow from initial brief to ready-to-develop stories.
"""

import asyncio
import json
from typing import Dict, Any

# This would be the actual MCP client integration
from crewai_tools import MCPServerAdapter

class BMadWorkflowExample:
    """
    Example demonstrating complete BMAD workflow using MCP Server.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp"):
        self.server_url = server_url
        self.project_state = {}
    
    async def run_complete_workflow(self):
        """Run the complete BMAD workflow example."""
        print("🚀 Starting BMAD Workflow Example")
        print("=" * 50)
        
        # Connect to BMAD MCP Server
        with MCPServerAdapter({"url": self.server_url}) as bmad_tools:
            print(f"📡 Connected to BMAD MCP Server at {self.server_url}")
            
            # Step 1: Create Project Brief
            await self._step_1_create_project_brief(bmad_tools)
            
            # Step 2: Generate PRD
            await self._step_2_generate_prd(bmad_tools)
            
            # Step 3: Validate Requirements
            await self._step_3_validate_requirements(bmad_tools)
            
            # Step 4: Create Architecture
            await self._step_4_create_architecture(bmad_tools)
            
            # Step 5: Create Frontend Architecture
            await self._step_5_create_frontend_architecture(bmad_tools)
            
            # Step 6: Create First Story
            await self._step_6_create_first_story(bmad_tools)
            
            # Step 7: Validate Story
            await self._step_7_validate_story(bmad_tools)
            
        print("\n✅ BMAD Workflow Complete!")
        print("📁 All artifacts generated and validated")
    
    async def _step_1_create_project_brief(self, bmad_tools):
        """Step 1: Create initial project brief."""
        print("\n📋 Step 1: Creating Project Brief")
        print("-" * 30)
        
        # Use the create_project_brief tool
        brief_result = await self._call_tool(bmad_tools, "create_project_brief", {
            "topic": "AI-powered personal finance assistant",
            "target_audience": "young professionals aged 25-35",
            "constraints": [
                "Must be mobile-first",
                "Integration with major banks required",
                "GDPR compliance mandatory"
            ],
            "scope_level": "standard"
        })
        
        brief_result_dict = await self._call_tool(bmad_tools, "create_project_brief", {
            "topic": "AI-powered personal finance assistant",
            "target_audience": "young professionals aged 25-35",
            "constraints": [
                "Must be mobile-first",
                "Integration with major banks required",
                "GDPR compliance mandatory"
            ],
            "scope_level": "standard"
        })
        
        self.project_state["project_brief"] = brief_result_dict["content"]
        print(f"✅ Project brief content generated. Suggested path: {brief_result_dict['suggested_path']}")
        print(f"📄 Brief length: {len(self.project_state['project_brief'])} characters")
        # In a real scenario, the assistant would now prompt the user to save this content.
    
    async def _step_2_generate_prd(self, bmad_tools):
        """Step 2: Generate comprehensive PRD."""
        print("\n📊 Step 2: Generating PRD")
        print("-" * 30)
        
        prd_result_dict = await self._call_tool(bmad_tools, "generate_prd", {
            "project_brief": self.project_state["project_brief"], # Pass the content
            "workflow_mode": "incremental",
            "technical_depth": "standard"
        })
        
        self.project_state["prd"] = prd_result_dict["content"]
        print(f"✅ PRD content generated. Suggested path: {prd_result_dict['suggested_path']}")
        print(f"📄 PRD length: {len(self.project_state['prd'])} characters")
        
        epic_count = self.project_state["prd"].count("Epic ")
        print(f"📈 Generated {epic_count} epics (from content analysis)")
    
    async def _step_3_validate_requirements(self, bmad_tools):
        """Step 3: Validate PRD quality."""
        print("\n🔍 Step 3: Validating Requirements")
        print("-" * 30)
        
        validation_result_dict = await self._call_tool(bmad_tools, "validate_requirements", {
            "prd_content": self.project_state["prd"], # Pass the content
            "checklist_type": "standard" # This should align with actual checklist names, e.g., "pm_checklist"
        })
        
        self.project_state["prd_validation"] = validation_result_dict["content"]
        print(f"✅ Requirements validation report generated. Suggested path: {validation_result_dict['suggested_path']}")
        
        if "EXCELLENT" in self.project_state["prd_validation"] or "GOOD" in self.project_state["prd_validation"]:
            print("🟢 PRD quality looks good based on report.")
        else:
            print("🟡 PRD report suggests areas for improvement.")
    
    async def _step_4_create_architecture(self, bmad_tools):
        """Step 4: Create technical architecture."""
        print("\n🏗️ Step 4: Creating Architecture")
        print("-" * 30)
        
        architecture_result_dict = await self._call_tool(bmad_tools, "create_architecture", {
            "prd_content": self.project_state["prd"], # Pass the content
            "tech_preferences": {
                "backend_framework": "FastAPI",
                "database": "PostgreSQL",
                "cloud_provider": "AWS",
                "api_style": "REST"
            },
            "architecture_type": "microservices"
        })
        
        self.project_state["architecture"] = architecture_result_dict["content"]
        print(f"✅ Architecture content generated. Suggested path: {architecture_result_dict['suggested_path']}")
        print(f"📄 Architecture length: {len(self.project_state['architecture'])} characters")
    
    async def _step_5_create_frontend_architecture(self, bmad_tools):
        """Step 5: Create frontend architecture."""
        print("\n🎨 Step 5: Creating Frontend Architecture")
        print("-" * 30)
        
        frontend_arch_result_dict = await self._call_tool(bmad_tools, "create_frontend_architecture", {
            "main_architecture": self.project_state["architecture"], # Pass the content
            "framework_preference": "React Native"
        })
        
        self.project_state["frontend_architecture"] = frontend_arch_result_dict["content"]
        print(f"✅ Frontend architecture content generated. Suggested path: {frontend_arch_result_dict['suggested_path']}")
        print(f"📄 Frontend arch length: {len(self.project_state['frontend_architecture'])} characters")
    
    async def _step_6_create_first_story(self, bmad_tools):
        """Step 6: Create first development story."""
        print("\n📝 Step 6: Creating First Story")
        print("-" * 30)
        
        story_result_dict = await self._call_tool(bmad_tools, "create_next_story", {
            "prd_content": self.project_state["prd"], # Pass the content
            "architecture_content": self.project_state["architecture"], # Pass the content
            "current_progress": {
                "completed_stories": [],
                "current_epic": 1 # Assuming epic numbers are used
            }
        })
        
        self.project_state["first_story"] = story_result_dict["content"]
        print(f"✅ First story content generated. Suggested path: {story_result_dict['suggested_path']}")
        print(f"📄 Story length: {len(self.project_state['first_story'])} characters")
    
    async def _step_7_validate_story(self, bmad_tools):
        """Step 7: Validate story quality."""
        print("\n✅ Step 7: Validating Story")
        print("-" * 30)
        
        story_validation_result_dict = await self._call_tool(bmad_tools, "validate_story", {
            "story_content": self.project_state["first_story"], # Pass the content
            "checklist_types": ["story_draft_checklist", "story_dod_checklist"] # These should be valid checklist names
        })
        
        self.project_state["story_validation"] = story_validation_result_dict["content"]
        print(f"✅ Story validation report generated. Suggested path: {story_validation_result_dict['suggested_path']}")
        
        if "READY" in self.project_state["story_validation"] or "EXCELLENT" in self.project_state["story_validation"]: # Adjust based on actual report content
            print("🟢 Story appears ready for development based on report.")
        else:
            print("🟡 Story report suggests improvements needed.")
    
    async def _call_tool(self, bmad_tools, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]: # Returns Dict
        """Helper method to call BMAD tools."""
        print(f"🔧 Calling tool: {tool_name} with arguments: {json.dumps(arguments, indent=2, default=lambda o: '<not serializable>')[:200]}...") # Log args carefully
        
        # This would be the actual MCP client call
        # tool_instance = next(t for t in bmad_tools if t.name == tool_name)
        # result_dict = await tool_instance.run(arguments) # Or however the MCPServerAdapter exposes run
        
        # For this example, we'll simulate the tool call and its structured response
        await asyncio.sleep(0.1) # Reduced sleep
        
        # Simulate the structured dictionary response
        return self._simulate_tool_response_dict(tool_name, arguments)
    
    def _simulate_tool_response_dict(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate structured tool responses for example purposes."""
        
        # Generic content generation for simulation
        content = f"# Simulated Content for {tool_name}\n\nArguments received:\n{json.dumps(arguments, indent=2, default=lambda o: '<not serializable>')}"
        suggested_path = f"simulated/{tool_name.replace('_', '-')}-output.md"
        metadata = {"tool_used": tool_name, "simulated_at": asyncio.get_event_loop().time()}
        message = f"Simulated content for {tool_name} generated."

        if tool_name == "create_project_brief":
            content = f"""# Project Brief: {arguments['topic']}
## Introduction / Problem Statement
Young professionals struggle with managing their personal finances effectively due to lack of time, financial literacy, and intuitive tools that understand their specific needs and banking relationships.

## Vision & Goals
- **Vision:** Empower young professionals to take control of their financial future through AI-driven insights and automated financial management.
- **Primary Goals:**
  - Goal 1: Increase user savings rate by 25% within 6 months
  - Goal 2: Automate 80% of routine financial tasks
  - Goal 3: Provide personalized financial insights and recommendations

## Target Audience / Users
Young professionals aged 25-35 who are digitally native, have steady income, and want to optimize their financial management without becoming financial experts.

## Key Features / Scope (High-Level Ideas for MVP)
- Bank account integration and transaction categorization
- AI-powered spending analysis and insights
- Automated savings recommendations
- Bill tracking and payment reminders
- Basic investment guidance

## Technical Constraints
- Must be mobile-first responsive design
- GDPR compliance for EU users
- Integration with major banking APIs
- Real-time transaction processing
- Secure data encryption

## Goal, Objective and Context
Create a mobile-first AI-powered personal finance assistant that helps young professionals manage their finances through automated insights, savings recommendations, and banking integration.

## Epic Overview

### Epic 1: Core Infrastructure Setup
**Goal:** Establish foundational infrastructure for secure, scalable financial data processing.

- Story 1.1: As a developer, I want to set up secure cloud infrastructure, so that we can safely handle financial data.
- Story 1.2: As a developer, I want to implement bank API integration framework, so that we can connect to major financial institutions.

### Epic 2: User Authentication & Onboarding
**Goal:** Enable secure user registration and bank account linking.

- Story 2.1: As a new user, I want to create an account with strong security, so that my financial data is protected.
- Story 2.2: As a user, I want to link my bank accounts securely, so that the app can analyze my transactions.

### Epic 3: Transaction Analysis & Categorization
**Goal:** Automatically categorize and analyze user spending patterns.

- Story 3.1: As a user, I want my transactions automatically categorized, so that I can understand my spending patterns.
- Story 3.2: As a user, I want to see spending insights and trends, so that I can make informed financial decisions.
## Validation Summary
- ✅ Item 1: PASS
- ⚠️ Item 2: NEEDS IMPROVEMENT
(Content similar to original but without the *Generated by* footer)"""
            checklist_name = arguments.get('checklist_type', arguments.get('checklist_types', ['unknown'])[0])
            suggested_path = f"checklists/validation_report_{checklist_name}.md"
            metadata.update({"artifact_type": "validation_report", "checklist": checklist_name})

        elif tool_name == "create_architecture":
            content = """# AI-Powered Personal Finance Assistant Architecture
## Technical Summary
Microservices architecture using FastAPI backend services, PostgreSQL for transactional data, Redis for caching, deployed on AWS with containerized services for scalability and security.

## High-Level Overview
The system follows a microservices architecture pattern with API Gateway, separate services for user management, transaction processing, AI insights, and bank integrations.

## Definitive Tech Stack Selections
- Backend: FastAPI (Python 3.11+)
- Database: PostgreSQL 15+ with encryption
- Cache: Redis 7+
- Message Queue: AWS SQS
- Container: Docker with Kubernetes
- Cloud: AWS (ECS, RDS, ElastiCache)
## Framework & Core Libraries
- React Native 0.72+ for cross-platform mobile development
- TypeScript for type safety
- React Navigation for routing
- Redux Toolkit for state management

## Component Strategy
- Atomic design principles with reusable UI components
- Screen-based organization with shared components
- Secure storage for authentication tokens
## Status: Draft
## Story
As a developer, I want to set up secure cloud infrastructure on AWS, so that we can safely handle financial data with proper encryption and compliance.

## Acceptance Criteria
1. AWS account configured with proper IAM roles and policies
2. VPC setup with private subnets for database access
3. Security groups configured for minimal required access
4. CloudFormation templates for infrastructure as code
5. Monitoring and logging enabled via CloudWatch

## Tasks / Subtasks
- [ ] Create AWS account and configure billing alerts
- [ ] Set up VPC with public/private subnet architecture
- [ ] Configure security groups and NACLs
- [ ] Set up CloudFormation templates for repeatable deployments
- [ ] Enable CloudWatch logging and monitoring

*Generated using BMAD MCP Server*"""

        elif tool_name == "validate_story":
            return """# Story Validation Report

## Validation Summary
- ✅ Goal & Context Clarity: PASS
- ✅ Technical Implementation Guidance: PASS
- ✅ Reference Effectiveness: PASS
- ✅ Self-Containment Assessment: PASS
- ⚠️ Testing Guidance: PARTIAL

## Recommendations
1. Add specific testing criteria for infrastructure validation
2. Include rollback procedures for failed deployments



# examples/simple_tool_usage.py
"""
Simple example showing individual BMAD tool usage.
"""

import asyncio
from crewai_tools import MCPServerAdapter

async def simple_tool_example():
    """Simple example of using BMAD tools individually."""
    
    # Connect to BMAD MCP Server
    server_config = {"url": "http://localhost:8000/mcp"}
    
    with MCPServerAdapter(server_config) as bmad_tools:
        print("🔧 Available BMAD Tools:")
        for tool in bmad_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Example 1: Create a project brief
        print("\n📋 Creating Project Brief...")
        brief_tool = next(tool for tool in bmad_tools if tool.name == "create_project_brief")
        
        brief_result = brief_tool.run({
            "topic": "Smart home automation system",
            "target_audience": "tech-savvy homeowners",
            "scope_level": "minimal"
        })
        
        print("✅ Project brief created!")
        print(f"📄 Length: {len(brief_result)} characters")
        
        # Example 2: Run a checklist
        print("\n✅ Running Quality Checklist...")
        checklist_tool = next(tool for tool in bmad_tools if tool.name == "run_checklist")
        
        validation_result = checklist_tool.run({
            "document_content": brief_result,
            "checklist_name": "pm_checklist",
            "validation_context": {"document_type": "project_brief"}
        })
        
        print("✅ Checklist completed!")
        print("📊 Validation results available")

if __name__ == "__main__":
    asyncio.run(simple_tool_example())


# examples/crewai_integration_example.py
"""
Example showing how to integrate BMAD MCP Server with CrewAI workflows.
"""

from crewai import Agent, Crew, Task, Process
from crewai_tools import MCPServerAdapter

def crewai_bmad_integration():
    """Example of using BMAD tools within CrewAI workflows."""
    
    # Connect to BMAD MCP Server
    with MCPServerAdapter({"url": "http://localhost:8000/mcp"}) as bmad_tools:
        
        # Create agents with access to BMAD tools
        project_manager = Agent(
            role="Senior Product Manager",
            goal="Create comprehensive project documentation using BMAD methodology",
            backstory="You are experienced in agile product management and use BMAD tools to ensure quality.",
            tools=bmad_tools,
            verbose=True
        )
        
        architect = Agent(
            role="Senior Software Architect", 
            goal="Design robust technical architectures based on requirements",
            backstory="You create scalable, maintainable architectures using BMAD best practices.",
            tools=bmad_tools,
            verbose=True
        )
        
        # Create tasks that use BMAD tools
        brief_task = Task(
            description="""
            Create a comprehensive project brief for a "Sustainable Fashion Marketplace" 
            that connects eco-conscious consumers with sustainable fashion brands.
            
            Use the BMAD create_project_brief tool with:
            - Topic: Sustainable Fashion Marketplace
            - Target audience: Eco-conscious millennials and Gen Z
            - Scope level: standard
            """,
            expected_output="Complete project brief following BMAD methodology",
            agent=project_manager
        )
        
        prd_task = Task(
            description="""
            Generate a comprehensive PRD based on the project brief created earlier.
            
            Use the BMAD generate_prd tool with the project brief as input.
            Ensure the PRD includes well-structured epics and user stories.
            """,
            expected_output="Complete PRD with epics and user stories",
            agent=project_manager,
            context=[brief_task]
        )
        
        architecture_task = Task(
            description="""
            Create a technical architecture document based on the PRD requirements.
            
            Use the BMAD create_architecture tool with:
            - The PRD content as input
            - Tech preferences for e-commerce platform
            - Microservices architecture type
            """,
            expected_output="Comprehensive technical architecture document",
            agent=architect,
            context=[prd_task]
        )
        
        validation_task = Task(
            description="""
            Validate the architecture document against BMAD quality standards.
            
            Use the BMAD run_checklist tool with:
            - The architecture document
            - architect_checklist
            """,
            expected_output="Architecture validation report with recommendations",
            agent=architect,
            context=[architecture_task]
        )
        
        # Create and run the crew
        bmad_crew = Crew(
            agents=[project_manager, architect],
            tasks=[brief_task, prd_task, architecture_task, validation_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute the workflow
        result = bmad_crew.kickoff()
        
        print("🎉 BMAD-powered CrewAI workflow completed!")
        print(f"📄 Final result: {result}")

if __name__ == "__main__":
    crewai_bmad_integration()
