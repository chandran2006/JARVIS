import os
import json
import re
from groq import Groq
from core.registry import SkillRegistry

class JarvisEngine:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = "llama-3.3-70b-versatile"
        
        self.system_instruction = (
            "You are Jarvis, a helpful and precise AI assistant. "
            "Use the provided tools to answer the user's request. "
            "When using tools, output VALID JSON arguments only."
        )

    def run_conversation(self, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.system_instruction},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            tools_schema = self.registry.get_tools_schema()
            # If no tools are loaded, don't pass tools argument (or pass empty? Groq might handle it)
            # Better to pass None if empty to avoid api error if specific models dislike empty tool lists?
            # Actually, let's pass it if it exists.
            
            completion_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 200
            }
            
            if tools_schema:
                completion_kwargs["tools"] = tools_schema
                completion_kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**completion_kwargs)
        except Exception as e:
            # Handle tool_use_failed error from Groq
            error_str = str(e)
            if "tool_use_failed" in error_str and "failed_generation" in error_str:
                try:
                    # Extract failed generation from error message (it's inside the dict string)
                    # We look for <function=NAME{ARGS}</function> pattern
                    match = re.search(r"<function=(\w+)(\{.*?\})<\/function>", error_str)
                    if match:
                        func_name = match.group(1)
                        func_args_str = match.group(2)
                        print(f"DEBUG: Recovered failed tool call: {func_name} with {func_args_str}")
                        
                        # Manually construct a tool call-like object to trigger the execution loop
                        # But wait, the loop expects response.choices[0].message.tool_calls
                        # We can just execute it here and return the result?
                        # Or reconstruct the response object?
                        # Easiest: Execute directly here
                        
                        function_to_call = self.registry.get_function(func_name)
                        if function_to_call:
                            try:
                                args = json.loads(func_args_str)
                                res = function_to_call(**args)
                                return str(res) # Return result directly as if it was the answer
                            except Exception as exec_e:
                                return f"Error executing recovered tool: {exec_e}"
                except Exception as parse_e:
                    print(f"Failed to recover tool call: {parse_e}")

            print(f"Groq API Error: {e}")
            return "I am having trouble connecting to the brain, sir."

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # CASE 1: AI wants to use a tool (Action)
        if tool_calls:
            print("DEBUG: Executing Tool...")
            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.registry.get_function(function_name)
                
                if not function_to_call:
                    res = "Error: Tool not found."
                else:
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        # We need to inspect the function signature or handle generic kwargs?
                        # The functions in existing skills seem to accept explicit args.
                        # Simple way is to just unpack **function_args
                        # Ensure function_args is a dict
                        if function_args is None:
                            function_args = {}
                            
                        res = function_to_call(**function_args)
                    except Exception as e:
                        res = f"Error executing tool: {e}"
                
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(res),
                    }
                )
            
            # Get final spoken response after tool runs
            # Remove tools arg for second call or keep it? Usually keep it in case it needs to chain.
            # But for simplicity let's just complete.
            second_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return second_response.choices[0].message.content
        
        # CASE 2: AI wants to chat
        else:
            return response_message.content
