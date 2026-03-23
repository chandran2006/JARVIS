import os
import json
import re
import time
from typing import List, Dict, Any, Optional
from groq import Groq
from core.registry import SkillRegistry

class ConversationManager:
    """Manages conversation history with context window management."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]
    
    def get_messages(self, system_prompt: str) -> List[Dict[str, str]]:
        return [{"role": "system", "content": system_prompt}] + self.history
    
    def clear(self):
        self.history.clear()
        self.context.clear()

class EnhancedJarvisEngine:
    """Advanced AI engine with streaming, caching, and intelligent tool execution."""
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = "llama-3.3-70b-versatile"
        self.conversation = ConversationManager()
        self.response_cache: Dict[str, str] = {}
        self.last_tool_results: Dict[str, Any] = {}
        
        self.system_instruction = (
            "You are JARVIS, an advanced AI assistant inspired by Tony Stark's AI. "
            "You are intelligent, efficient, witty, and proactive. "
            "Use available tools to accomplish tasks. Be concise but informative. "
            "When using tools, provide natural responses that incorporate the results. "
            "Remember context from previous interactions. "
            "If a task fails, suggest alternatives or troubleshooting steps."
        )
    
    def run_conversation(self, user_prompt: str, stream: bool = False) -> str:
        """Execute conversation with optional streaming support."""
        
        # Check cache for repeated queries
        cache_key = user_prompt.lower().strip()
        if cache_key in self.response_cache:
            cached_time = time.time() - self.response_cache.get(f"{cache_key}_time", 0)
            if cached_time < 300:  # 5 minute cache
                return self.response_cache[cache_key]
        
        # Add user message to history
        self.conversation.add_message("user", user_prompt)
        
        messages = self.conversation.get_messages(self.system_instruction)
        
        try:
            response = self._execute_with_tools(messages)
            
            # Cache response
            self.response_cache[cache_key] = response
            self.response_cache[f"{cache_key}_time"] = time.time()
            
            # Add assistant response to history
            self.conversation.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = self._handle_error(e, user_prompt)
            self.conversation.add_message("assistant", error_msg)
            return error_msg
    
    def _execute_with_tools(self, messages: List[Dict[str, str]], max_iterations: int = 3) -> str:
        """Execute conversation with tool calling support and iteration limit."""
        
        tools_schema = self.registry.get_tools_schema()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            completion_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            if tools_schema:
                completion_kwargs["tools"] = tools_schema
                completion_kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**completion_kwargs)
            response_message = response.choices[0].message
            
            # No tool calls - return response
            if not response_message.tool_calls:
                return response_message.content
            
            # Execute tool calls
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.registry.get_function(function_name)
                
                if not function_to_call:
                    result = json.dumps({"error": "Tool not found", "tool": function_name})
                else:
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        result = function_to_call(**function_args)
                        
                        # Store tool results for context
                        self.last_tool_results[function_name] = {
                            "args": function_args,
                            "result": result,
                            "timestamp": time.time()
                        }
                        
                    except Exception as e:
                        result = json.dumps({"error": str(e), "tool": function_name})
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(result)
                })
        
        # Max iterations reached - get final response
        final_response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=300
        )
        return final_response.choices[0].message.content
    
    def _handle_error(self, error: Exception, user_prompt: str) -> str:
        """Intelligent error handling with recovery suggestions."""
        
        error_str = str(error)
        
        # Handle specific error types
        if "tool_use_failed" in error_str:
            return self._recover_from_tool_error(error_str, user_prompt)
        elif "rate_limit" in error_str.lower():
            return "I'm experiencing high demand right now. Please try again in a moment."
        elif "connection" in error_str.lower():
            return "I'm having trouble connecting to my neural network. Please check your internet connection."
        else:
            return f"I encountered an unexpected issue: {error_str[:100]}. Let me try a different approach."
    
    def _recover_from_tool_error(self, error_str: str, user_prompt: str) -> str:
        """Attempt to recover from malformed tool calls."""
        
        try:
            match = re.search(r"<function=(\w+)(?:.*?)(?=\{)(\{.*?\})</function>", error_str)
            if match:
                func_name = match.group(1)
                func_args_str = match.group(2)
                function_to_call = self.registry.get_function(func_name)
                
                if function_to_call:
                    args = json.loads(func_args_str)
                    result = function_to_call(**args)
                    return f"Task completed: {result}"
        except:
            pass
        
        return "I had trouble executing that command. Could you rephrase your request?"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation.clear()
        self.response_cache.clear()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        return {
            "history_length": len(self.conversation.history),
            "last_tools": list(self.last_tool_results.keys()),
            "cache_size": len(self.response_cache)
        }
