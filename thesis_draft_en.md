# Undergraduate Thesis Draft

## Thesis Title
Design and Implementation of an AI-Assisted Programming Teaching System (Backend and Database Focus)

## Student Information
- Name: Liu Shiyu
- Student ID: 1220032841
- Supervisor: Tian Jinyu
- School: School of Computer Science and Engineering

---

## Abstract
As programming course enrollment continues to increase, instructors are facing growing pressure in assignment grading and personalized feedback delivery. Although traditional manual grading draws on teaching experience, it is often time-consuming, slow in feedback turnaround, and difficult to keep fully consistent across a large class. Existing automatic grading systems can quickly determine whether code passes test cases, but they usually provide only binary results ("correct/incorrect") and limited guidance for improvement. To address these issues, this thesis designs and implements an AI-assisted teaching system for programming courses, with a primary focus on backend services, database modeling, and workflow implementation.

The system establishes a complete "submission-execution-analysis-grading-feedback" loop. Technically, the backend is built with FastAPI, the database uses PostgreSQL, and deployment is containerized for reproducibility. After a student submits code, the system executes it in a controlled environment, records runtime outputs and errors, performs static analysis, and computes final correctness scores based on hidden test cases. To improve grading fairness, the system separates the final score from the static-analysis score: the final score reflects functional correctness, while the static-analysis score evaluates code quality and implementation reasoning.

For feedback generation, the system introduces a Retrieval-Augmented Generation (RAG) pipeline. Course documents, teaching materials, and assignment context are used as retrieval sources to help the language model produce feedback that is better aligned with course content and less likely to include out-of-scope suggestions. On the instructor side, the system supports class management, student management, assignment score review, submission detail review, and report navigation. In addition, the system supports online deployment and public access, allowing teachers and students to log in, submit, and review results off campus.

Integration and testing results show that the system has reached a practical level for course use: the core pipeline runs stably, grading and feedback are functional, and instructor-side features can support small- to medium-scale teaching scenarios. This work demonstrates that, in undergraduate teaching contexts, integrating automatic grading, rule-based scoring, RAG-based feedback, and teaching management into a unified platform is feasible, and it provides an implementation foundation for future work on feedback quality optimization, academic integrity checks, and multi-language extension.

**Keywords:** Programming education; Automatic grading; RAG; Large language model; Static analysis; Teaching management system

---

## Chapter 1 Introduction

### 1.1 Research Background
Programming courses are core components of computer science education. In actual teaching practice, however, instructors commonly face two practical pressures: increasing student numbers and higher expectations for feedback quality. For programming assignments, numerical scores alone are usually insufficient; students need to know what is wrong, why it is wrong, and how to improve. This is especially true for beginners. Even when code runs successfully, many submissions still require improvement in structure, naming, and readability. Manual grading requires line-by-line review and written comments, which is highly time-consuming and difficult to keep timely, stable, and fine-grained in large classes.

Existing automatic grading systems are already relatively mature and can produce quick results through compilation and test cases. However, their feedback is often limited to pass/fail outcomes or short error messages. For novice learners, such feedback is not always truly helpful: students may know that a submission failed but still not understand the root cause; even if a submission passes all tests, the implementation may still be suboptimal. Therefore, improving feedback quality while retaining automation efficiency has become a key issue in digital programming education.

In recent years, large language models have shown strong performance in code understanding and generation, offering new possibilities for automated, explanatory, and personalized feedback. Yet direct use of general-purpose models in teaching can still lead to problems such as out-of-syllabus suggestions, terminology misalignment with course content, and unstable conclusions. For undergraduate teaching, a system should not only "answer," but answer accurately, consistently, and appropriately. This requires integrating model capabilities with course boundaries, grading rules, and actual teaching workflows.

### 1.2 Research Motivation and Problem Definition
The starting point of this project is a practical teaching contradiction: instructors need timely and high-quality feedback, but manual grading is costly; automated systems are efficient, but often lack depth and pedagogical alignment. Based on this contradiction, this thesis focuses on the following questions:

1. How can a stable automatic grading and feedback pipeline be built to form an end-to-end closed loop from submission to feedback?
2. How can grading balance "result correctness" and "process quality," avoiding over-reliance on either final outcomes or process scoring?
3. How can course documents be integrated into feedback generation to reduce out-of-scope suggestions and improve alignment with course content?
4. How can the instructor side provide a practical management view so that teachers can review not only scores but also submission details, student status, and class-level progress?

This thesis does not aim primarily at algorithmic novelty. Instead, it emphasizes practical deployment and teaching usability by designing and implementing an end-to-end system and iteratively improving it through real usage workflows.

### 1.3 Research Objectives and Main Contributions
The overall objective of this thesis is to design and implement an AI-assisted programming teaching system that supports an integrated workflow of "automatic grading + explanatory feedback + instructor management" in undergraduate course settings. To achieve this goal, this work completes the following:

1. Designs backend services and data models for user identity management, assignment management, submission records, grading results, and feedback storage.
2. Implements core processes including code execution, static analysis, and hidden-test grading to form an automatic post-submission evaluation mechanism.
3. Proposes a layered scoring strategy that separates final correctness scores from static-analysis scores to improve pedagogical interpretability.
4. Introduces an RAG-based feedback generation pipeline so that AI feedback is grounded in course documents and remains context-aligned.
5. Implements key instructor-workbench functions, including class management, student management, assignment score review, student detail review, and report navigation.
6. Completes containerized deployment and public-access adaptation, enabling off-campus usage for both students and instructors.

### 1.4 Features and Practical Value of This Work
Compared with implementations that focus only on isolated scoring modules, this thesis emphasizes system completeness and pedagogical adaptation in three major aspects:

1. End-to-end engineering closure: covering the full chain of submission, execution, grading, feedback, management, and deployment, rather than a single algorithm experiment.
2. Explicit teaching-oriented rules: improving grading consistency through blank-submission detection, template comparison, hidden tests, and separated static-analysis scoring.
3. Practical-use orientation: supporting public deployment and multi-role access under real course usage conditions.

From a practical perspective, the system can reduce instructor workload in repetitive grading tasks, improve feedback timeliness, and provide structured data for subsequent learning analytics (e.g., common error statistics and learning trajectory observation).

---

## Chapter 2 Related Work

### 2.1 Literature Overview and Key Issues
Automatic grading systems have long been used in programming education. Their typical logic is "compilation + test cases + score by pass rate." The advantages are clear: high speed, unified rules, and suitability for batch submissions. In larger classes, this approach indeed reduces repetitive instructor workload.

However, traditional automatic grading also has notable limitations in practical teaching. First, it focuses mainly on functional correctness and provides limited coverage of readability, structural design, and coding standards. Second, feedback is usually brief, often limited to pass/fail outcomes and difficult to interpret. Third, when code has minor syntax errors but demonstrates correct core reasoning, systems may still assign very low scores or zero, which is not always consistent with how instructors evaluate student thinking in manual review. In other words, test-driven scoring is efficient but still leaves room for improvement in pedagogical feedback quality.

**Application of Large Language Models in Code Feedback.**
In recent years, large language models have shown strong performance in code generation, explanation, and error analysis, creating a new path for automated explanatory feedback. Compared with traditional automatic grading, LLMs can produce richer natural-language explanations, such as identifying potential logic issues, explaining compilation errors, and suggesting revisions.

From a modeling and evaluation perspective, the Codex study emphasizes functional correctness as the core target: it evaluates code generation with pass@k, i.e., whether at least one correct solution appears within k samples under unit tests, rather than relying on surface-form similarity alone (Chen et al., 2021). The same work also reports weak correlation between BLEU and true functional correctness. Austin et al. report a similar pattern in program synthesis: larger models generally improve solve rates, while sampling strategy strongly affects outcomes; higher-temperature sampling can be more effective when multiple attempts are allowed (Austin et al., 2021). These observations directly support the design choice in this thesis to prioritize executable evidence (runtime behavior and hidden-test outcomes) over text-level similarity.

Looking at concrete experimental settings, Chen et al. report pass@k under different sampling budgets on HumanEval and emphasize that temperature should be tuned with respect to k rather than fixed globally (Chen et al., 2021). Austin et al. also compare greedy decoding with temperature-based sampling in program synthesis and show that, when multiple attempts are allowed, diverse sampling often finds executable correct programs more reliably than a single highest-probability output (Austin et al., 2021). This is directly relevant to teaching systems: feedback should preserve executable evidence and reproducible outcomes, not depend only on the fluency of one generated response.

However, LLMs are not directly ready for classroom use. During investigation and development, two common issues were observed: suggestions may go beyond current course progress, and responses may be overly generic or inconsistent with course terminology. Therefore, in teaching scenarios, LLMs are better used as a feedback enhancement module rather than a full replacement for instructional grading rules.

**Role of RAG in Teaching Feedback.**
To address the problem of feedback drifting away from course context, Retrieval-Augmented Generation (RAG) provides a feasible approach. The basic process is to retrieve relevant content from course documents first, and then generate feedback using both retrieved materials and submission context. Compared with direct generation, RAG has two key advantages: stronger alignment with course content (fewer out-of-scope suggestions) and improved interpretability through material grounding.

In the original RAG framework, the generator combines parametric memory with non-parametric external memory by conditioning on retrieved documents and marginalizing over top-k candidates during generation (Lewis et al., 2020). The paper further distinguishes RAG-Sequence and RAG-Token, where the token-level variant can switch evidence across tokens. For teaching feedback, this mechanism is important because it keeps responses grounded in editable course materials while still benefiting from the expressive power of large models, reducing hallucination and terminology drift.

In this project, lecture notes and review materials are included in the retrieval corpus. Feedback generation references retrieved passages to keep responses close to classroom context rather than producing generic suggestions.

**Academic Integrity and Fairness.**
In programming courses, an automated system should be not only fast but also fair. Fairness is mainly reflected in two points: applying consistent rules to all students and ensuring scores reflect actual learning effort. If the system cannot detect direct template submissions or disguised blank submissions, unreasonable high scores may occur and undermine fairness. Conversely, if syntax errors always result in immediate failure, submissions with meaningful reasoning may be overly penalized.

To address this, the project adopts a separated final/static scoring strategy and introduces blank-submission detection. This helps balance result correctness and process evaluation, reducing unfairness caused by scoring distortion.

### 2.2 Chapter Summary
Overall, existing studies and engineering practice have built a foundation in efficiency, interpretability, and course alignment, but a fully deployable solution for undergraduate teaching is still limited. This thesis does not focus on introducing a new algorithm; instead, it integrates automatic grading, rule-based scoring, RAG feedback, and instructor management into a deployable, operable, and iterative platform for real course workflows.

---

## Chapter 3 System Requirements and Overall Architecture

### 3.1 Requirements Analysis
The system is designed for day-to-day programming-course teaching and primarily serves students and instructors. Students mainly care about smooth submission, clear feedback, and timely results, while instructors care more about convenient class/assignment management, stable grading behavior, and traceable workflows.

Based on practical usage scenarios, the system objectives can be summarized as follows:

1. Support a complete closed loop from submission to grading feedback.
2. Ensure grading results are interpretable and reviewable.
3. Support continuous instructor-side management of classes, students, and assignments.
4. Support online deployment and off-campus access for home-use scenarios.

**Student-side Functional Requirements.**
Core student requirements include:

1. Account login and student registration.
2. Assignment list viewing and code submission.
3. Result viewing, including runtime output, static-analysis score, final score, and AI feedback.
4. Basic profile maintenance (e.g., name).

**Instructor-side Functional Requirements.**
In addition to score review, instructors require complete management capabilities:

1. Instructor login and role-based authentication.
2. Class management: create, rename, delete, add/remove students.
3. Student management: view student details, review submission records, delete abnormal accounts.
4. Assignment-view dashboard: review student status and scores by assignment.
5. Report viewing: jump directly to detailed submission reports.
6. Grade export: CSV export for offline statistics.

**Non-functional Requirements.**
Besides business functions, the system should satisfy:

1. Stability: maintain service availability under repeated submission scenarios.
2. Security: execute untrusted code in controlled environments rather than host runtime.
3. Consistency: keep scoring rules reproducible and avoid large fluctuations across similar submissions.
4. Scalability: support future expansion to more problems, languages, and finer analysis rules.
5. Deployability: support Docker-based deployment and public-access configuration.

### 3.2 Overall System Architecture
The system adopts a front-end/back-end separated architecture with four layers:

1. Presentation layer: student and instructor interfaces for interaction and result display.
2. Service layer: authentication, submission processing, scoring feedback, and management APIs.
3. Data layer: PostgreSQL persistence for users, assignments, submissions, feedback, and classes.
4. Retrieval/feedback layer: AI feedback generation grounded in course-document retrieval.

At the deployment layer, services are orchestrated by Docker Compose. The frontend uses Nginx to proxy backend APIs, enabling quick startup in local or public environments.

### 3.3 Core Workflow Design

**Submission Workflow.**
After code submission, backend processing follows these steps:

1. Validate assignment and user identity.
2. Store submission version and code content.
3. Execute code via execution service.
4. Generate issue list and static score via static-analysis module.
5. Compute final score via grading module.
6. Generate RAG-based feedback and write it to the database.

This workflow ensures each submission is traceable and reviewable.

**Scoring Workflow.**
A two-track strategy is used:

1. Final score: based mainly on hidden test outcomes, reflecting functional correctness.
2. Static-analysis score: reflecting code quality and implementation process, without replacing the final score.

To prevent inflated scores from template-only submissions, blank-submission detection is applied. If only template content or no effective new code is detected, static-analysis scores are significantly reduced or set to zero, and a warning is shown on the result page.

**Instructor Management Workflow.**
The instructor workbench links class, assignment, and student views. It supports class-based filtering, assignment-based review, and student-level drill-down to detailed submission reports, integrating score review and teaching management in one interface workflow.

---

## Chapter 4 Key Methods and Core Mechanisms

### 4.1 Controlled Execution and Evaluation Pipeline
The key design is not simply running code, but decomposing each submission into a reviewable, traceable, and explainable process. After submission, the backend validates identity and assignment legality, stores submission records, and then performs execution, analysis, grading, and feedback generation in a fixed order to avoid unexplained result fluctuations over time.

At execution level, user code is run in a controlled environment with constraints on runtime duration and resource usage, while outputs are collected systematically. This provides two direct teaching benefits: instructors do not need to maintain multiple local runtime environments, and students receive more consistent execution outcomes, reducing disputes such as "works locally but fails on the platform."

Execution outcomes are stored in structured form, including stdout, stderr, and exit status. These records support both immediate grading and later instructor review, meaning each score is backed by process-level evidence rather than a single final number.

### 4.2 Code Quality Analysis and Fairness Control
Using hidden-test pass rate alone makes it difficult to distinguish between two cases: functionally correct code with poor quality, and conceptually reasonable code with implementation details not yet complete. To address this, the system adopts a dual-track mechanism: final score for functional correctness, and static-analysis score for coding quality, structure, and process quality.

The static-analysis module scans code under rule-based checks, extracts potential issues, and applies corresponding deductions. This score supplements the final score instead of replacing it. As a result, students can understand not only whether a solution is correct, but also where it can be improved; instructors can also identify class-wide patterns more efficiently.

To reduce scoring distortion, the system includes template/blank-submission detection. If submitted code is highly similar to the starter template or lacks effective newly added logic, blank-submission detection is triggered, static-analysis scores are reduced, and warnings are displayed. This mechanism helps prevent inflated scores from superficial submissions and makes grading more aligned with actual student effort.

### 4.3 RAG-Based Feedback and Teaching Alignment
In the feedback stage, student code is not sent directly to a general-purpose model. Instead, relevant course materials are retrieved first, and retrieval outputs are combined with submission context for generation. The purpose is to keep feedback centered on lecture content, course terminology, and assignment objectives, reducing generic or out-of-scope advice.

The process can be summarized as "retrieve first, generate second." The system retrieves relevant teaching fragments based on assignment topic and code features, then combines runtime results, static-analysis conclusions, and grading information to produce structured feedback. Feedback typically includes issue localization, revision suggestions, and actionable next steps.

This design is consistent with findings in prior work: RAG improves factual grounding by making retrieved evidence part of the generation condition, not just an auxiliary reference (Lewis et al., 2020). For code-related outputs, this thesis also prioritizes executable signals (test outcomes and runtime traces) over pure text overlap, matching evidence from Codex and large-scale synthesis studies that functional correctness is a more reliable target than n-gram similarity metrics such as BLEU (Chen et al., 2021; Austin et al., 2021).

To ensure stability in classroom use, a fallback path is preserved: when retrieval is insufficient or model services fluctuate, the system can still return basic rule-based feedback so that page readability and workflow continuity are maintained. In short, RAG improves feedback quality without becoming a single point of failure in the main pipeline.

---

## Chapter 5 Database and API Design

### 5.1 Overall Database Design
The database uses PostgreSQL and follows a teaching-process-oriented modeling principle, forming a traceable data loop over users, assignments, submissions, evaluation, and feedback. In addition to supporting student submission and result query, it supports instructor-side management and statistics by class, assignment, and student dimensions.

Core entities include users, classes, courses, assignments, submissions, execution results, static-analysis results, feedback, and document corpora. These entities are linked through primary and foreign keys. For example, each submission is linked to both student and assignment, and feedback/execution results are one-to-one with submissions. This ensures each score can be traced back to concrete submission context for review and interpretation.

The relational organization is clear:

1. Users and courses are connected through enrollment relations, supporting future multi-course expansion.
2. Course-to-assignment is one-to-many, supporting multiple assignments per course.
3. Student-to-submission is one-to-many, supporting versioned submissions.
4. Submission-to-execution/static/feedback is one-to-one, ensuring unique and direct result query.

This modeling approach balances business readability and implementation maintainability. Future scoring dimensions or analysis modules can be integrated smoothly through extension tables around the main submission chain.

### 5.2 Core Tables and Field Description
In the current implementation, key tables are summarized as follows:

1. User/organization tables: users, class_groups, courses, enrollments (identity, class grouping, course relation).
2. Assignment/rubric tables: assignments, rubrics (assignment metadata and grading configuration).
3. Submission/result tables: submissions, execution_results, static_analysis_results, feedbacks (code versions, runtime outcomes, static issues, final feedback).
4. Retrieval-corpus table: documents (course documents and embeddings for RAG retrieval).

Among these, submissions is the center of the whole pipeline. It stores assignment_id, student_id, language, version, and created_at, clearly representing who submitted which assignment version and when. The associated execution_results, static_analysis_results, and feedbacks tables allow simultaneous presentation of runtime status, code-quality information, and pedagogical feedback, avoiding over-compression into a single output.

To support class-based teaching management, the users table retains class_name, while class_groups maintains class sets. Under current course scale, this design has relatively low implementation cost and short query paths, and it supports direct class-based filtering on the instructor side.

### 5.3 API Design and Access Control
The backend APIs are implemented with FastAPI and organized into five business domains: login, users, assignments, submissions, and analytics. The organization follows a "clear path, single responsibility" principle for easier frontend integration and maintenance.

Main API paths in the current version include:

1. Authentication API: /login/access-token for login and token issuance.
2. User APIs: /users for registration, profile maintenance, class management, and student management.
3. Assignment APIs: /assignments for assignment list retrieval.
4. Submission APIs: /submissions for submission creation, list query, detail query, and bulk deletion.
5. Analytics APIs: /analytics for gradebook, student submission details, and class performance statistics.

Access control is role-based. Students primarily access submission and personal endpoints; instructors access class and student management endpoints; some analytics endpoints require higher-level permissions. This layered control satisfies teaching-management needs while preventing unauthorized student access to others' data.

For data consistency, submission deletions cascade through execution, static-analysis, and feedback records to avoid orphan data. Combined with foreign-key constraints and transactional commits, the system maintains stable integrity under common teaching operations.

---

## Chapter 6 System Implementation and Deployment

### 6.1 Backend Core Implementation
The backend is implemented with FastAPI using an "interface-layer separation + service modularization" organization. Routes are divided into five modules: login, users, assignments, submissions, and analytics, corresponding to authentication, account/class management, assignment retrieval, evaluation pipeline, and instructor statistical views. This modular structure improves responsibility clarity and makes iterative maintenance easier.

In the submission chain, processing follows a fixed order: validate assignment and user, create submission record, execute code, perform static analysis, and generate grading feedback. To ensure traceability, execution outputs, static issues, and final feedback are stored in separate result tables and linked by submission_id. This enables instructors to review full process details instead of only aggregated scores.

The backend also includes startup-time schema compatibility logic (e.g., auto-adding class_name and auto-creating class_groups). This improves usability in legacy database environments and reduces startup failures caused by schema-version mismatch during iterative development.

### 6.2 Frontend Functional Implementation
The frontend is implemented with Vue3 and organized around two major scenarios: student-side and instructor-side usage. Student pages focus on login, assignment viewing, code submission, and result viewing; instructor pages focus on class management, student management, assignment score review, and submission detail drill-down. Interaction paths are intentionally shortened to reduce page-hopping for instructors.

At request level, the frontend uses a unified Axios wrapper for backend API calls, with interceptors for token injection, timeout prompts, and authentication-failure redirection. Since scoring may involve model invocation, API timeout settings are moderately relaxed; timeout messages advise users to retry or refresh the result page, reducing false perceptions of system failure.

During integration, the frontend defaults to /api/v1 as API base path. This supports both local development and online same-origin reverse-proxy deployment, reducing CORS complexity and improving consistency between debugging and production behavior.

### 6.3 Containerization and Online Deployment
Deployment is orchestrated by Docker Compose with three core services: db, backend, and frontend. The database service handles persistence, the backend service handles APIs and evaluation workflows, and the frontend service serves static resources via Nginx while proxying /api to backend. Only port 80 is exposed externally; backend and database are not directly exposed to the public network, improving security controllability.

For image builds, the backend uses Python 3.11 and runs with Uvicorn; the frontend builds with Node and serves static files through Nginx. Online compose files unify configuration for database connection, token parameters, model invocation parameters, and CORS options. Deployment settings are environment-variable-driven for reuse across machines.

In practice, this "three-container + reverse-proxy" structure balances maintainability and reproducibility. The same core architecture works across local demos, intranet tunneling, and public server deployment, reducing environment-related integration variance.

### 6.4 Startup Scripts and Operation Maintenance
To reduce deployment barriers, the project provides one-click PowerShell and batch scripts. Startup scripts automatically check Docker status, validate .env.online configuration, run container startup and migration processes, and output access URLs after local health checks pass. In classroom demos, this significantly reduces command-level operation errors.

For off-campus access, the system supports both direct public-server access and intranet tunneling to local services. In practice, as long as frontend ports are reachable and reverse-proxy paths are consistent, students and instructors can complete login, submission, and result review via one unified entry point.

At operation level, standard commands for container status, log tracing, and service shutdown are retained for rapid issue diagnosis. Overall, the project has established a basic operations loop of "startable, reviewable, recoverable," sufficient for demonstration and small-scale teaching use.

---

## Chapter 7 System Testing and Result Analysis

### 7.1 Testing Objectives and Testing Plan
This chapter evaluates three main questions: whether the system can stably run the core teaching workflow, whether grading and feedback are pedagogically usable, and whether instructor-side functions support daily operation. Accordingly, testing uses a combined strategy of functional integration testing, scenario validation, and deployment validation, rather than isolated endpoint checks.

Testing workflows are designed separately for students and instructors. Student-side tests focus on login, assignment viewing, code submission, and result viewing; instructor-side tests focus on class management, student management, score review, and report navigation. In addition, local deployment and online deployment tests are conducted to confirm consistent front-end/back-end behavior across environments.

### 7.2 Functional Test Results
Integration results indicate that the core workflow has formed a stable closed loop. After student submission, the system completes execution, static analysis, grading, and feedback generation; result pages display runtime outputs, static issues, and final scores. On the instructor side, submission status can be reviewed by class and assignment, with drill-down to single-submission detail pages.

Regarding account and permission boundaries, behavior is largely as expected. Students can access only personal submission data, while instructors can complete management operations through class and student endpoints. For common abnormal operations (e.g., deleting submissions, bulk deletion, querying non-existing records), the system returns clear error messages, with no obvious unauthorized data exposure observed.

For fairness-related scenarios, template and blank-submission detection is specifically validated. Results show that when submissions are highly similar to templates or lack effective new code, warnings are triggered and static-analysis scores are reduced. When submissions contain syntax errors but still show meaningful implementation intent, static-analysis scores are not zeroed unconditionally. This is consistent with the design goal of balancing result correctness and process evaluation.

### 7.3 Stability and Deployment Usability Analysis
In terms of stability, after repeated submission and query rounds, major APIs remained responsive without frequent interruption. Since scoring includes model invocation, single feedback generation latency can exceed ordinary query latency. However, frontend timeout messaging and result-page refresh mechanisms reduce user-perceived risk, and interaction remains acceptable.

In terms of deployment usability, two operational paths are validated: one-click local startup and online containerized deployment. The former is suitable for development and classroom demonstration, while the latter is suitable for off-campus access. During tests, the three-service Docker Compose structure starts reliably, and same-origin reverse proxy avoids extra CORS complexity. Combined with health checks and log tracing, the system has baseline operational observability.

### 7.4 Discussion and Improvement Directions
Although the system has reached a usable baseline for course application, several optimization points remain. First, feedback quality is still influenced by model service status and retrieval quality; in some edge cases, suggestions are not specific enough. Second, current performance testing is mainly conducted at course-scale integration level and does not yet cover higher concurrency and longer continuous runtime.

Future improvements can proceed along two directions: optimizing course corpus and retrieval strategies, and adding automated stress-testing scripts. These improvements are expected to move the system from merely "usable" to "more practical" for long-term real-world teaching.

---

## Chapter 8 Conclusion and Future Work

### 8.1 Overall Summary
This thesis addresses the core issue of improving grading efficiency and feedback quality in programming courses by designing and implementing an AI-assisted teaching system. Unlike approaches focused on isolated algorithms, this project emphasizes an end-to-end engineering workflow in teaching contexts, covering submission, controlled execution, static analysis, scoring feedback, instructor management, and deployment operation.

At implementation level, this work completes backend services, database modeling, API partitioning, and frontend-backend integration, and establishes a reproducible containerized deployment scheme with off-campus access support. Through instructor-side class and student detail functions, the system supports not only scoring but also traceable management views. Test results indicate good usability and stability under course-scale scenarios.

At method level, final scores are separated from static-analysis scores, and template/blank-submission detection is integrated to balance correctness and process evaluation. Meanwhile, RAG is introduced to align feedback with course context and reduce generic or out-of-scope suggestions. Overall, this work shows that integrated deployment of "automatic grading + rule constraints + retrieval-enhanced feedback + teaching management" is feasible in undergraduate teaching settings.

### 8.2 Limitations
Although the system already supports daily teaching demos and small-scale use, several limitations remain. First, feedback quality is affected by model service status and retrieval hit quality, and may still be insufficiently specific in edge cases. Second, current performance evaluation focuses mainly on course-scale integration and does not yet cover higher concurrency and longer continuous operation. Third, instructor-side analytics remain relatively basic, with room to improve metric granularity and visualization depth.

In addition, this thesis focuses mainly on backend and database implementation. Experiments on frontend interaction quality and student learning behavior are not yet sufficiently deep. For example, there is still limited systematic comparative evidence on how different feedback presentation styles affect learning outcomes. These issues provide clear directions for future work.

### 8.3 Future Work
Future development can proceed in three directions. First, continue optimizing the feedback pipeline by expanding course corpora, improving retrieval ranking strategies, and strengthening feedback template constraints to improve output stability and teaching alignment. Second, strengthen engineering robustness by introducing automated regression and stress tests, optimizing long-latency task handling, and improving failure-recovery mechanisms. Third, enrich teaching analytics by adding error-trend statistics, class-level learning trajectory observation, and finer-grained instructor decision-support views.

From an application perspective, the system can be extended to more assignment types and programming languages, and further integrated with course platforms. With iterative updates based on real classroom data, the system has the potential to evolve from an "auxiliary grading tool" into a "teaching decision-support platform component," improving both teaching efficiency and student feedback experience.

---

## Chapter 9 Acknowledgements

From topic selection, proposal, and mid-term progress to final completion, this graduation project went through repeated requirement adjustments, architecture iterations, deployment troubleshooting, and thesis revision. The successful completion of this work would not have been possible without the continuous guidance of my supervisor in both overall direction and detailed improvements. At each key stage, my supervisor provided specific and practical suggestions, helping me transform initial ideas into concrete implementation goals and deepening my understanding of usability and interpretability in real teaching scenarios.

At the same time, course training and laboratory projects in the school provided a strong foundation for this project, enabling me to integrate database design, backend development, API integration, and deployment operations into a fully runnable system. During development and testing, I also benefited from classmates' feedback on usage experience, function behavior, and issue reproduction. Their practical input helped identify and locate many problems that were difficult to discover through self-testing alone.

For me personally, this graduation project is not only an academic requirement, but also a complete engineering practice experience. I learned how to balance feature implementation and system stability under limited time, how to locate problems in a layered manner when facing continuous errors, and how to translate technical implementation into solutions acceptable for real teaching contexts. Finally, I would like to express my sincere gratitude to all teachers and classmates who supported this project.

---
