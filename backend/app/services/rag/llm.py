from typing import List
from app.db.models import Document, Submission, ExecutionResult, StaticAnalysisResult

class LLMService:
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
        
        prompt = f"""
        You are an AI teaching assistant. Analyze the student's code submission.
        
        Course Material Context (Reference this if relevant):
        {context_text}
        
        Student Code:
        ```python
        {submission.code_content}
        ```
        
        Execution Output:
        Stdout: {execution_result.stdout}
        Stderr: {execution_result.stderr}
        Exit Code: {execution_result.exit_code}
        
        Static Analysis Issues:
        {static_analysis.issues if static_analysis else 'None'}
        
        Task:
        Provide constructive feedback in the student's preferred language (English or Chinese). Detected from code comments or default to Chinese if unsure.
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
