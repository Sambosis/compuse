from openai import OpenAI
# load the API key from the environment
import os
from dotenv import load_dotenv
from icecream import ic
import difflib
import pandas as pd
from typing import Optional, Literal, TypedDict
from enum import StrEnum
from .base import CLIResult, ToolError, ToolResult, BaseAnthropicTool
load_dotenv()

import os


class GetExpertOpinionTool(BaseAnthropicTool):
    """
    A tool takes a detailed description of the problem and everything that has been tried so far, and returns an expert opinion on the problem.
    """

    name: Literal["Opinion"] = "opinion"
    api_type: Literal["custom"] = "custom"
    description: str = "A tool takes a detailed description of the problem and everything that has been tried so far, and returns an expert opinion on the problem."



    def to_params(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.api_type,
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["get_opinion"],
                        "description": "The command to get an expert opinion."
                    },
                    "problem_description": {
                        "type": "string",
                        "description": "A detailed description of the problem and everything that has been tried so far."
                    }
                },
                "required": ["command", "problem_description"]
            }
        }
        
    async def __call__(     
        self,
        *,
        command: Literal["get_opinion"],
        problem_description: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Executes the specified command.
        """
       
        if command == "get_opinion":
            ic()
            return await self.get_opinion(problem_description=problem_description)
        if command == "get_plan":
            ic()
            return await self.get_plan(problem_description=problem_description)
        else:
            ic()
            raise ToolError(
                f"Unrecognized command '{command}'. Allowed commands: 'list_reports', 'run_report'."
            )

    async def get_plan(self, problem_description) -> ToolResult:
        prompt = f"""
        Objective:
You are a Task Decomposition Specialist. Your goal is to meticulously break down any given computer-based task into the smallest reasonable steps. Each step should be clear, actionable, and independently verifiable for completion by someone without prior knowledge of the task or access to the execution environment.
Instructions:
For each step (and sub-step, if necessary), provide the following:
Step [Number]:
Action: A detailed and specific description of the action to be performed.
Expected Result: A description of what should occur or be produced after the action is completed.
Verification Method: A precise method to confirm that the step has been completed, which should:
Be executable by someone who has not seen the previous steps.
Not require access to the environment where the task was performed.
Focus on confirming the completion of the action, not the accuracy of the result (unless completion inherently requires accuracy).
Guidelines:
Clarity and Specificity:
Use clear, unambiguous language.
Include specific details such as file names, URLs, commands, or search queries where applicable.
Step Structure:
Main Steps: Numbered sequentially (e.g., Step 1, Step 2, Step 3).
Sub-Steps: If a step requires multiple actions, break it down into sub-steps (e.g., Sub-Step 1.1, Sub-Step 1.2).
Formatting Requirements:
Use bold headings for Action, Expected Result, and Verification Method for clarity.
Present information in a structured and organized manner.
Independent Verification:
Ensure each verification method can be performed independently of other steps.
Verification should rely only on the outputs or artifacts produced by that specific step.
Verification Methods:
Should be objective, measurable, and specific.
May include:
Checking the existence or properties of a file or document.
Viewing metadata, timestamps, or file contents.
Confirming the presence of specific data, entries, or outputs.
Reviewing screenshots or exported logs.
No Assumptions:
Do not assume the verifier has any prior knowledge of the task or access to previous results.
Do not require the verifier to access the execution environment or external systems beyond what is produced in the step.
Example Format:
Step 1:
Action: Create a new folder named Elevator_Project on your desktop.
Expected Result: A folder named Elevator_Project exists on the desktop.
Verification Method: Check the desktop for the presence of the Elevator_Project folder.
Sub-Step 1.1:
Action: Inside the Elevator_Project folder, create an Excel file named elevator_data.xlsx with two sheets labeled Company_Info and Models.
Expected Result: An Excel file elevator_data.xlsx with two sheets named Company_Info and Models exists in the Elevator_Project folder.
Verification Method: Open elevator_data.xlsx and confirm the sheets Company_Info and Models are present.
Sub-Step 1.2:
Action: In the Company_Info sheet, add column headers in the first row: Manufacturer, Public/Private, Number of Employees, Years in Business.
Expected Result: The Company_Info sheet has the specified headers correctly labeled in the first row.
Verification Method: Open the Company_Info sheet and verify the headers are present and correctly labeled.
Your Task:
{problem_description}
Apply the above guidelines and format to break down the provided task:
Instructions for Completion:
Identify Main Steps:
Start by outlining the major components required to complete the task.
Decompose into Sub-Steps:
Break down each main step into smaller, actionable sub-steps as necessary.
Detail Each Step:
For every step and sub-step, provide the Action, Expected Result, and Verification Method as per the guidelines.
Ensure Independent Verification:
Make sure that each verification method allows someone to confirm completion without prior knowledge or access to the execution environment.
Maintain Clarity and Organization:
Use the specified formatting for consistency and ease of understanding.
Begin your detailed task breakdown below:
        """
        return ToolResult(output=prompt)

    async def get_opinion(self, problem_description) -> ToolResult:
        """
        Lists all available reports.
        """
        try:
            ic()
            client = OpenAI()
            ic(client)
            prompt = f"""
           The user would like your expert opinion on the following problem:
           {problem_description}
            """
            response = client.chat.completions.create(
                model="o1-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                        ],
                    }
                ]
            )
            ic(response)
            ex_opinion = response.choices[0].message.content
            return ToolResult(output=ex_opinion)
        except Exception as e:
            ic()
            raise ToolError(f"Failed to generate opinion: {str(e)}")







