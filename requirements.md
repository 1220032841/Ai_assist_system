# AI-Assisted Teaching System for Programming Courses  
### Backend & Database Requirements Document

---

## 1. System Overview

This project implements the backend and database components of an AI-assisted grading and feedback system for programming courses. The system integrates:

- Sandboxed code execution  
- Static and dynamic program analysis  
- Retrieval-Augmented Generation (RAG) using course materials  
- Curriculum-aware concept constraints  
- Rubric-based automated grading  
- Secure and auditable data storage  

The frontend is developed separately and will interact with the backend through REST APIs.

---

## 2. User Roles

### 2.1 Student
- Submit source code for assignments  
- Receive grades and AI-generated feedback  
- View submission history and improvement suggestions  

### 2.2 Instructor / Teaching Assistant
- Upload rubrics, course documents, and assignment configurations  
- Review and audit grades, feedback, and citations  
- Monitor student performance and class-wide statistics  
- Handle re-evaluation or grading appeals  

### 2.3 System Administrator
- Manage model versions and RAG index  
- Configure sandbox and execution settings  
- Manage user accounts and roles  

---

## 3. Functional Requirements (FR)

### **FR1. Submission Management**
- Provide REST API for uploading submissions.  
- Store submission metadata (student, assignment, timestamp, language).  
- Support submission versioning (each attempt stored as a new version).

### **FR2. Sandboxed Execution**
- Compile and execute student code in isolated containers.  
- Collect runtime data: stdout, stderr, exit code, resource consumption.  
- Enforce CPU, memory, and execution time limits.  
- Prevent unauthorized file access or network access.

### **FR3. Static and Dynamic Analysis**
- Extract cyclomatic complexity.  
- Perform linting/style checking.  
- Measure coverage when applicable.  
- Return structured analysis results to the backend.

### **FR4. RAG-Based Feedback Generation**
- Index course materials into vector embeddings.  
- Retrieve relevant text chunks based on submission context.  
- Provide retrieved chunks + execution results to the LLM.  
- Feedback must include explicit citations to source slides/documents.  
- No feedback may include exact solutions or code that completes the assignment.

### **FR5. Concept-Aware Constraints**
- Maintain a concept graph representing curriculum topics.  
- Each assignment specifies allowed and disallowed concepts.  
- LLM pre-filter: restrict prompt to allowed concepts only.  
- LLM post-filter: remove or rewrite feedback containing out-of-scope concepts.

### **FR6. Rubric-Based Automated Grading**
Rubric is version-controlled and stored in the database.  
Typical rubric categories include:

| Criterion               | Typical Weight |
|------------------------|----------------|
| Functional correctness | 40%            |
| Robustness             | 10%            |
| Code quality/style     | 15%            |
| Efficiency             | 10%            |
| Documentation          | 10%            |
| Test quality           | 10%            |
| Academic integrity     | 5%             |

The backend must combine test results, code analysis, and rubric criteria to produce a final grade.

### **FR7. Feedback Generation**
- AI feedback must be grounded in RAG-retrieved materials.  
- Must avoid hallucinations and unsupported topics.  
- Must provide actionable, constructive guidance.  
- Must avoid revealing assignment solutions.

### **FR8. Analytics and Reporting**
- Display common failure reasons and error clusters.  
- Track student learning progress and concept mastery.  
- Allow instructors to view class-level performance analytics.  
- Support exporting summaries (CSV/JSON).

### **FR9. Authentication & Authorization**
- Token-based authentication (e.g., JWT).  
- Role-Based Access Control (RBAC): Student, Instructor, Admin.  
- Restrict access to sensitive data based on role.

### **FR10. Auditing**
Every request related to grading or feedback must be logged, including:
- Submission version  
- Model version  
- Prompt  
- RAG retrieved chunks  
- Rubric version  
- Final grade & feedback  

---

## 4. Non-Functional Requirements (NFR)

### **NFR1. Performance**
- Support parallel processing of submissions via a worker queue.  
- Target end-to-end evaluation time < 60 seconds.  
- Efficient vector search for RAG retrieval.

### **NFR2. Security**
- Fully isolated sandbox (seccomp, AppArmor, or container-based).  
- No external network access during code execution.  
- Encrypt sensitive information (PII) at rest.  
- Validate API inputs to prevent injection attacks.

### **NFR3. Auditability**
- Provide complete traceability for grading decisions.  
- Store model, prompt, RAG, and rubric versions.  
- Allow instructors to reconstruct how feedback was generated.

### **NFR4. Scalability**
- Support multiple programming languages (C/C++/Java/Python).  
- Support multiple courses and semesters.  
- Allow scaling horizontally via container orchestration.

### **NFR5. Reliability**
- Use message queue for robust execution job handling.  
- Recover gracefully from worker crash or timeout.

### **NFR6. Privacy**
- Minimize stored personal data.  
- Follow FERPA/GDPR-style principles for educational data.

---

## 5. Data Model Requirements

The system must maintain the following core entities:

### **Student**
- Student ID  
- Name (encrypted)  
- Course enrollments  

### **Course / Term**
- Course metadata  
- Instructors  
- Active assignments  

### **Assignment**
- Assignment ID, release date, due date  
- Allowed concepts  
- Associated rubric version  
- Test suite version  

### **Submission**
- Submission ID  
- Student ID  
- Assignment ID  
- Language  
- Timestamp  
- Code snapshot  
- Version number

### **ExecutionRun**
- Compile logs  
- Runtime logs  
- Resource usage  
- Test results  

### **StaticAnalysisRecord**
- Lint warnings  
- Complexity  
- Style violations  

### **Rubric / RubricVersion**
- Weighted grading criteria  
- Version number  
- Description  

### **GradeRecord**
- Final score  
- Breakdown by rubric criteria  
- Feedback items  
- Citation references  

### **Feedback**
- LLM-generated text  
- RAG citations  
- Version of the model used  

### **RAG Documents**
- PDF/Markdown/Slide segments  
- Embeddings  
- Source reference  

### **ConceptGraph**
- Nodes (concepts)  
- Edges (prerequisite relationships)  

### **Plagiarism Signals**
- Fingerprints  
- Similarity scores to other submissions  

---

## 6. System Constraints

- LLM must not output full assignment solutions.  
- LLM feedback must be grounded in retrieved course documents.  
- Concept constraints must prevent out-of-scope guidance.  
- Sandboxed execution must be secure and isolated.  
- All grading operations must be reproducible.  
- Backend is authoritative; frontend is a thin UI layer.

---

## 7. Risks and Mitigation Strategies

| Risk                           | Mitigation                                      |
|--------------------------------|--------------------------------------------------|
| LLM hallucinations             | RAG grounding + validator layer                 |
| Out-of-scope concepts          | Concept-aware constraints                       |
| Sandbox escape                 | Use hardened containers and restricted syscalls |
| Inconsistent grading           | Rubric versioning + calibration                 |
| Model drift                    | Store prompt + model version + citation trace   |
| Privacy violations             | Encrypt PII and limit stored personal data      |

---

## 8. Acceptance Criteria

- System runs end-to-end from submission → execution → grading → feedback.  
- All feedback includes citations from RAG.  
- No feedback contains disallowed concepts or full solutions.  
- All workflows are logged and auditable.  
- Database migrations run without error.  
- Instructor dashboards correctly display aggregated analytics.

---

## 9. Future Extensions

- Adaptive hint generation based on mastery patterns  
- Support for peer feedback  
- Anonymous submission mode for double-blind grading  
- Automated test generation via models  
- Multi-agent grading systems  

---

*End of requirements.md*
