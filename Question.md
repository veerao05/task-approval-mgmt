# DLL Python developer assignment
Task Approval Workflow API
Design a FastAPI service with clean architecture that handles approval workflows for different task types.
Focus on project structure and design patterns—functionality can be scaffolded/mocked.
1. Implement 3 polymorphic task types (DataAccessTask, ResourceProvisionTask,
ConfigChangeTask) using Pydantic discriminated unions with type-specific validation rules
2. Create layered architecture with routers (thin HTTP layer) → controllers (business
logic/validation) → repository (in-memory storage with async interface)—demonstrate clear
separation of concerns
3. Build 4 REST endpoints: POST /tasks, GET /tasks/{id}, PATCH /tasks/{id}/approve, PATCH
/tasks/{id}/reject with proper status transitions (PENDING → APPROVED/REJECTED)
4. Write 3-5 async tests covering task creation, approval flow, and validation errors using FastAPI
TestClient
5. Document architecture decisions in README: explain your layer separation, polymorphism
approach, file/folder organization rationale, and what would change for production (caching,
persistence, auth)
What we're evaluating: Project structure, code organization, design patterns, type safety, architectural
thinking—not feature completeness.
Submission: Send a public GitHub repository with above committed code changes or a zip file to [hiring
email]. Include all source code and README.