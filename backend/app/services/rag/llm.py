from typing import List
from app.db.models import Document, Submission, ExecutionResult, StaticAnalysisResult

class LLMService:
    def _is_trivial_success_case(
        self,
        submission: Submission,
        execution_result: ExecutionResult,
        static_analysis: StaticAnalysisResult,
    ) -> bool:
        assignment = submission.assignment
        assignment_text = (
            f"{assignment.title if assignment else ''} "
            f"{assignment.description if assignment and assignment.description else ''}"
        ).lower()
        code_text = submission.code_content or ""
        non_empty_lines = [line for line in code_text.splitlines() if line.strip()]

        issue_payload = static_analysis.issues if static_analysis else None
        if isinstance(issue_payload, dict):
            issue_items = issue_payload.get("issues", [])
            error_count = int(issue_payload.get("error_count", 0) or 0)
            warning_count = int(issue_payload.get("warning_count", 0) or 0)
            convention_count = int(issue_payload.get("convention_count", 0) or 0)
        else:
            issue_items = issue_payload if isinstance(issue_payload, list) else []
            error_count = 0
            warning_count = 0
            convention_count = 0

        beginner_keywords = [
            "hello world",
            "hello",
            "first program",
            "print",
            "输出",
            "入门",
            "第一个",
        ]
        has_beginner_signal = any(keyword in assignment_text for keyword in beginner_keywords)
        has_clean_run = execution_result.exit_code == 0 and not (execution_result.stderr or "").strip()
        has_issue_items = isinstance(issue_items, list) and any(isinstance(item, dict) for item in issue_items)
        has_no_real_static_issue = not has_issue_items and error_count == 0 and warning_count == 0 and convention_count == 0

        return has_clean_run and has_no_real_static_issue and (
            has_beginner_signal or len(non_empty_lines) <= 10
        )

    async def generate_feedback(
        self, 
        submission: Submission, 
        execution_result: ExecutionResult, 
        static_analysis: StaticAnalysisResult,
        retrieved_docs: List[Document]
    ) -> str:
        """
        Generates feedback using LLM + RAG context.
        """
        if len(retrieved_docs) == 0:
            context_text = "No relevant course material found."
        else:
            context_text = "\n\n".join([f"Source: {doc.title}\n{doc.content}" for doc in retrieved_docs])

        assignment = submission.assignment
        submission_language = (submission.language or "cpp").lower()
        assignment_language = ((getattr(assignment, "language", None) or submission_language) if assignment else submission_language).lower()
        code_fence_language = "cpp" if submission_language == "cpp" else submission_language
        is_trivial_success_case = self._is_trivial_success_case(
            submission,
            execution_result,
            static_analysis,
        )
        feedback_policy = (
            "This is a very simple beginner exercise or a short correct program. "
            "Do not be overly strict or nitpicky. If the code is correct, clearly say it is correct first. "
            "Do not criticize large-project style conventions such as avoiding using namespace std, adding comments everywhere, architecture, extensibility, or performance tuning unless the assignment explicitly requires them or they cause a real problem. "
            "If the code is correct and simple, do not provide improvement suggestions at all. Just give brief positive confirmation. "
            "Only provide a suggestion when there is a concrete, user-visible problem in the code or execution result."
            if is_trivial_success_case
            else "Focus on concrete issues that are supported by the code, execution result, static analysis, or course context. If there are no clear problems, say so directly instead of inventing generic style criticism."
        )
        
        prompt = f"""
        You are an AI teaching assistant. Analyze the student's code submission.

        Assignment Title:
        {assignment.title if assignment else 'Unknown assignment'}

        Assignment Description:
        {assignment.description if assignment and assignment.description else 'No description provided.'}

        Expected Programming Language:
        {assignment_language}

        Student Submitted Language:
        {submission_language}
        
        Course Material Context (Reference this if relevant):
        {context_text}
        
        Student Code:
        ```{code_fence_language}
        {submission.code_content}
        ```
        
        Execution Output:
        Stdout: {execution_result.stdout}
        Stderr: {execution_result.stderr}
        Exit Code: {execution_result.exit_code}
        
        Static Analysis Issues:
        {static_analysis.issues if static_analysis else 'None'}

        Feedback Policy:
        {feedback_policy}
        
        Task:
        Provide constructive feedback in the student's preferred language (English or Chinese). Detected from code comments or default to Chinese if unsure.
        Treat the assignment's expected programming language as authoritative. Do not claim a language mismatch unless the student's submitted language differs from the expected language.
        Only mention problems that are actually supported by the provided evidence.
        1. Point out errors or bad practices. / 指出错误或不良实践。
        2. Cite the course material context where applicable. / 在适用的情况下引用课程材料上下文。
        3. Do NOT give the full solution. / 不要给出完整的解决方案。
        4. Be encouraging. / 保持鼓励的态度。
        
        Format the response in Markdown.
        """
        
        # Call LLM here
        from app.services.rag.service import rag_service
        if not rag_service.client:
               return "AI feedback service is unavailable: LLM_API_KEY is missing. Please set LLM_API_KEY in .env.online and restart backend."

        try:
            models_to_try = [rag_service.chat_model]
            if rag_service.fallback_chat_model and rag_service.fallback_chat_model not in models_to_try:
                models_to_try.append(rag_service.fallback_chat_model)

            last_error = None
            for model_name in models_to_try:
                try:
                    response = await rag_service.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "You are a helpful teaching assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7
                    )
                    return response.choices[0].message.content
                except Exception as model_error:
                    last_error = model_error

            return f"Error generating feedback: {str(last_error)}"
        except Exception as e:
            return f"Error generating feedback: {str(e)}"

llm_service = LLMService()
