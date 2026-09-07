FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY challenge-4/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY challenge-4/workflow_orchestrator.py .
COPY challenge-4/api_server.py .
COPY challenge-6/validation_workflow.py .

# Add challenge-2 agents for OCR agent
RUN mkdir -p /app/challenge-2/agents
COPY challenge-2/agents/ocr_agent.py /app/challenge-2/agents/

# Add coverage validation agents
RUN mkdir -p /app/agents
COPY challenge-6/agents/policy_matching_agent.py /app/agents/
COPY challenge-6/agents/coverage_validation_agent.py /app/agents/

# Run as a non-root user
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

# Expose API port
EXPOSE 8080

# Run API server
CMD ["python", "api_server.py"]
