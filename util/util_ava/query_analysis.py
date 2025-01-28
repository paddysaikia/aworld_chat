import os
import logging

class QueryAnalyzer:
    def __init__(self, ai_interface):
        """
        Initialize the class with AI interface, tasks, knowledge base, and input placeholders.

        :param ai_interface: Interface for AI interactions
        """
        self.ai_interface = ai_interface

        # Get project root and resolve base path
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        base_path = os.path.join(project_root, 'resources', 'data', 'ava', 'knowledge', 'aworld')

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Project root: {project_root}")
        self.logger.info(f"Base path set to: {base_path}")

        # Define tasks
        self.tasks = {
            1: "Analyze Query Intent",
            2: "Check Relevance to A World",
            3: "Identify Relevant Knowledge Sources",
            4: "Evaluate Ethical Constraints",
            5: "Perform Query Expansion",
            6: "Cross-Validate with Vision and Mission",
            7: "Check Core Principles Alignment",
            8: "Consult Governance Guidelines",
            9: "Apply Economic Model Considerations",
            10: "Incorporate Product and Service Insights",
            11: "Assess Sustainability Relevance",
            12: "Integrate AVA Core Values",
            13: "Maintain Ethical Depth and Traits",
            14: "Include Broader Context",
            15: "Generate Preliminary True/False Statements",
            16: "Filter and Prioritize Tasks",
            17: "Generate Response",
            18: "Feedback Loop",
        }

        # Define knowledge base paths
        self.knowledge_base = {
            "01_Vision_and_Mission": os.path.join(base_path, "01_Vision_and_Mission.txt"),
            "02_Core_Principles": os.path.join(base_path, "02_Core_Principles.txt"),
            "03_Governance_and_Community_Structure": os.path.join(base_path, "03_Governance_and_Community_Structure.txt"),
            "04_Economic_Model_and_A_Credits": os.path.join(base_path, "04_Economic_Model_and_A_Credits.txt"),
            "05_Products_and_Services": os.path.join(base_path, "05_Products_and_Services.txt"),
            "06_Sustainability_Practices": os.path.join(base_path, "06_Sustainability_Practices.txt"),
            "07_AVA_Core_Values_and_Traits": os.path.join(base_path, "07_AVA_Core_Values_and_Traits.txt"),
            "08_AVA_Depth_and_Ethics": os.path.join(base_path, "08_AVA_Depth_and_Ethics.txt"),
            "09_Ethical_Constraints_and_Deviation_Control": os.path.join(base_path, "09_Ethical_Constraints_and_Deviation_Control.txt"),
            "10_Broader_Context_Beyond_A_World": os.path.join(base_path, "10_Broader_Context_Beyond_A_World.txt"),
        }

        # Load knowledge base files into memory
        self.knowledge_data = {}
        for file_key, file_path in self.knowledge_base.items():
            normalized_path = os.path.abspath(file_path)
            if os.path.exists(normalized_path):
                with open(normalized_path, 'r', encoding='utf-8') as f:
                    self.knowledge_data[file_key] = f.read()
            else:
                self.logger.warning(f"Knowledge base file not found - {file_key}: {normalized_path}")
                self.knowledge_data[file_key] = None  # Optional fallback

        # Raise error if critical files are missing
        mandatory_files = ["01_Vision_and_Mission", "02_Core_Principles"]
        for file_key in mandatory_files:
            if not self.knowledge_data.get(file_key):
                raise FileNotFoundError(f"Critical knowledge base file missing: {file_key}")

        # Initialize inputs
        self.inputs = {
            "last_conversations": "",
            "user_profile": "",
        }



    def analyze_query(self, user_name, query, last_n_conversations, user_profile):
        # Step 1: Prepare initial payload
        initial_payload = {
            "query": query,
            "tasks": {task: False for task in self.tasks.keys()},
            "sources": {source: False for source in self.knowledge_base.keys()},
            "inputs": {input_key: False for input_key in self.inputs.keys()},
        }

        print("Sending initial query with payload:", initial_payload)

        # Step 2: Get the initial query response
        response = self.ai_interface.send_initial_query(initial_payload)
        if "error" in response:
            print("Error in initial query response:", response["error"])
            return "Invalid initial query response from AI."

        # Step 3: Extract relevant data
        relevant_tasks = response.get("relevant_tasks", {})
        relevant_sources = response.get("relevant_sources", {})
        relevant_inputs = response.get("relevant_inputs", {})

        print("Relevant tasks:", relevant_tasks)
        print("Relevant sources:", relevant_sources)
        print("Relevant inputs:", relevant_inputs)

        # Step 4: Create refined payload
        refined_payload = {
            "user_name": user_name,
            "query": query,
            "tasks": relevant_tasks,
            "sources": relevant_sources,
            "last_conversations": last_n_conversations if relevant_inputs.get("last_conversations") else None,
            "user_profile": user_profile if relevant_inputs.get("user_profile") else None,
        }

        print("Sending refined query with payload:", refined_payload)

        # Step 5: Get the refined query response
        final_response = self.ai_interface.send_refined_query(refined_payload)
        if not isinstance(final_response, dict) or "response" not in final_response:
            print("Invalid final response from AI.")
            return "The AI system did not provide a valid response."

        return final_response.get("response", "No answer available.")
