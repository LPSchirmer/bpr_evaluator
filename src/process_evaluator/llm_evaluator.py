# Importing third-party libraries
from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List
import os

# Loading environment variables
load_dotenv()

# Instantiation of gemini client
client_gemini = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            initial_delay=1.0,
            attempts=10,
            http_status_codes=[408, 429, 500, 502, 503, 504]
        ),
        timeout=120 * 1000
    )
)

# Google search tool for research tasks
search_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Year variables
current_year = datetime.now().year
last_year = current_year-1
second_to_last_year = current_year-2
third_to_last_year = current_year-3

# Structuring output of LLM
# For context researcher
class OrganizationalContext(BaseModel):
    industry: str = Field(description="The industry in which the organization operates")
    number_of_employees: str = Field(description=f"The total number of employees in the year {last_year}")
    revenue_per_year: str = Field(description=f"The total revenue in the year {last_year}")
    size: str = Field(description="The size of the organization according to the classification based on the total number of employees and the revenue per year")
    experience_bpr: str = Field(description="The amount of experience this organization has in business process redesign projects")
    
# For semantic evaluation
class ExplanationItemSemantic(BaseModel):
    violated_requirement: str = Field(description="The violated or not fulfilled completeness requirement in keyword format")
    description: str = Field(description="A one-sentence explanation why the completeness requirement is violated or not fulfilled")

class Semantic(BaseModel):
    violations: int = Field(description="Number of violated or not fulfilled completeness requirements (length of explanation list)")
    explanation: List[ExplanationItemSemantic] = Field(description="List of violated or not fulfilled completeness requirements with its one-sentence explanation why it is violated or not fulfilled")

# For compliance evaluation
class ExplanationItemCompliance(BaseModel):
    violated_compliance_rule: str = Field(description="The violated compliance rule in keyword format with the following information in paranthesis: 'Externally researched' if the norm was not explicetely given and 'Internally given' if the norm was explicetely given")
    description: str = Field(description="A one-sentence explanation why the business process violates the rule")

class Compliance(BaseModel):
    violations: int = Field(description="Number of violated compliance rules (length of explanation list)")
    explanation: List[ExplanationItemCompliance] = Field(description="List of violated compliance rules with its one-sentence explanation why the rule is violated")

# For schedule evaluation
class BacklogItemSchedule(BaseModel):
    phase: str = Field(description="The name of the implementation phase")
    days_for_phase: int = Field(description="The number of days required to complete this phase")
    activities: str = Field(description="A very short list of the activities that have to be done in this phase")

class Schedule(BaseModel):
    total_days: int = Field(description="Total number of days required for implementation (sum of the required days per phase)")
    schedule_plan: List[BacklogItemSchedule] = Field(description="List of the implementation phases with its required days and associated activities")

# Mapping of LLM input file types
mime_type_mapping = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".bpmn": "text/xml"
}

# Method for uploading files to LLM
def upload_file_to_llm(file_path: str, file_suffix: str):
    """
    Uploading a given file for adding it to an API call
    """
    uploaded_file = client_gemini.files.upload(
        file = file_path,
        config = {
            "mime_type": mime_type_mapping.get(file_suffix, "text/plain")
        }
    )
    return uploaded_file

# Company size mapping dictionary according to the EU definition
company_size_classification = {
    "Small": {
        "number_of_employess": "< 49",
        "revenue_per_year": "< 10 million €"
    },
    "Medium": {
        "number_of_employess": "50 - 249",
        "revenue_per_year": "10 - 50 million €"
    },
    "Big": {
        "number_of_employess": "> 249",
        "revenue_per_year": "> 50 million €"
    }
}

# System prompts for different API calls
system_prompts = {
    "organizational_context_research": """
        You are a Senior Business Analyst. Research the specified business data for the provided organization and summarize 
        the information found in as few words as possible. Only include information, that can be reliably checked. Do not hallucinate data!""",

    "organizational_context": """
        Output the provided information in the required format wihtout adding or inferring new information.""",

    "semantic_evaluation": """
        Your are an expert in modeling business processes with BPMN and evaluating the 
        semantic quality of business process models against the criterion completeness. 
        You work strictly evidence-based and only evaluate the BPMN model against completeness requirements that are actually given.""",

    "compliance_evaluation_research": """
        You are a Senior Compliance Officer and Business Process Analyst specializing in legal research and BPMN-based audits. 
        You are experienced in researching and interpreting legal, regulatory, and industry-specific norms for business processes.
        You work strictly evidence-based and only include information that is explicitely given or can be reliably researched.""",

    "compliance_evaluation": """
        You are a Senior Process Compliance Analyst within a business process redesign evaluation team.
        Your expertise combines internal audit, regulatory interpretation, and
        process-oriented compliance evaluation. You are experienced in interpreting legal, regulatory,
        and industry-specific norms and mapping their requirements onto concrete process structures.
        You assess both internal governance rules and external compliance obligations
        with equal rigor. You work strictly evidence-based: every evaluation must be
        traceable to explicitly provided process information, documented internal
        policies, and verifiable external norms.""",

    "schedule_evaluation_research": """
        You act as a specialized Business Process Analyst. Present your results in at most 250 words, while providing a concise and fact-based 
        summary that highlights the interconnectedness and potential friction points for the implementation of a redesigned business process alternative. 
        Your analysis must focus exclusively on the implementation effort required 
        after a redesign is finalized, ignoring any prior conceptual or modeling phases.""",

    "schedule_evaluation": """
        You are a senior business process redesign project manager. 
        Your expertise lies in providing lean, conservative time estimations that avoid project 
        inflation by focusing especially on the delta between process versions."""
}