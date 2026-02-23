"""
IoTwizz Module: AI Wizz Mode
An AI-powered interactive hacking assistant that can execute IoTwizz modules autonomously.
"""

import sys
import json
from io import StringIO
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import ANSI

from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, console, print_table
from iotwizz.module_loader import ModuleLoader


class AiWizz(BaseModule):
    """AI-powered interactive pentesting assistant."""

    def __init__(self):
        super().__init__()
        self.name = "AI Wizz Mode (Hacking Assistant)"
        self.description = "Interactive AI pentesting assistant that can run IoTwizz modules"
        self.author = "IoTwizz Team"
        self.category = "ai"
        
        # We will load these later during run() to prevent infinite RecursionError 
        # since ModuleLoader tries to instantiate AiWizz which instantiates ModuleLoader...
        self.loader = None
        self.available_tools = ""

        self.options = {
            "PROVIDER": {
                "value": "gemini",
                "required": True,
                "description": "AI Provider (gemini, openai, claude, ollama)",
            },
            "API_KEY": {
                "value": "",
                "required": False,
                "description": "API Key (leave blank for ollama or if using environment variables)",
            },
            "MODEL": {
                "value": "gemini-2.5-flash",
                "required": True,
                "description": "Model name (e.g., gemini-2.5-flash, gpt-4o, claude-3-5-sonnet-20241022)",
            },
            "OLLAMA_URL": {
                "value": "http://localhost:11434",
                "required": False,
                "description": "Ollama API URL (if provider is ollama)",
            },
        }

    def _get_module_descriptions(self) -> str:
        """Get a JSON string describing all available non-ai modules and their options."""
        modules_info = {}
        for path, mod in self.loader.get_all_modules().items():
            if mod.category == "ai" or mod._is_stub:
                continue
                
            mod_options = {}
            for opt_name, opt_data in mod.options.items():
                mod_options[opt_name] = {
                    "required": opt_data.get("required", False),
                    "description": opt_data.get("description", "")
                }
                
            modules_info[path] = {
                "name": mod.name,
                "description": mod.description,
                "options": mod_options
            }
        return json.dumps(modules_info, indent=2)

    def _get_system_prompt(self) -> str:
        return f"""You are AiWizz, an elite IoT pentesting assistant integrated directly into the IoTwizz framework.
Your goal is to help the user hack, analyze, and secure IoT devices (hardware, firmware, and protocols).

You have direct access to internal IoTwizz modules. If you determine that running a module would help the user, you MUST respond using the following strict JSON format:
```json
{{
  "thought": "Your reasoning for running the tool",
  "tool_call": {{
    "module_path": "category/module_name",
    "options": {{
      "PORT": "/dev/ttyUSB0",
      "TIMEOUT": "5"
    }}
  }}
}}
```

If you just want to talk to the user, respond with normal text.
If you use a tool_call, NEVER write anything outside of the JSON block.

Here are the modules you can run, along with their paths and required options:
{self.available_tools}

When the user asks you to do something, THINK if one of these modules applies. If so, return the JSON. I (the framework) will intercept your JSON, run the module in the background, capture its terminal output, and hand the output back to you so you can analyze the results for the user.
"""

    def _init_ai_client(self, provider, api_key, model, ollama_url):
        """Initialize the requested AI provider."""
        if provider == "gemini":
            try:
                import google.generativeai as genai
                if api_key:
                    genai.configure(api_key=api_key)
                # Create a chat session with the system prompt
                client = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=self._get_system_prompt()
                )
                return client.start_chat(history=[]), "gemini"
            except ImportError:
                error("google-generativeai not installed. Run: pip install google-generativeai")
                return None, None
                
        elif provider == "openai":
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                messages = [{"role": "system", "content": self._get_system_prompt()}]
                return (client, model, messages), "openai"
            except ImportError:
                error("openai not installed. Run: pip install openai")
                return None, None
                
        elif provider == "claude":
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                messages = []
                system_prompt = self._get_system_prompt()
                return (client, model, messages, system_prompt), "claude"
            except ImportError:
                error("anthropic not installed. Run: pip install anthropic")
                return None, None
                
        elif provider == "ollama":
            try:
                import requests
                # Just verify connection
                r = requests.get(f"{ollama_url}/api/version", timeout=2)
                r.raise_for_status()
                messages = [{"role": "system", "content": self._get_system_prompt()}]
                return (ollama_url, model, messages), "ollama"
            except (ImportError, requests.RequestException) as e:
                error(f"Failed to connect to Ollama at {ollama_url}: {e}")
                return None, None
                
        else:
            error(f"Unknown provider: {provider}")
            return None, None

    def _get_ai_response(self, client_data, provider, user_input) -> str:
        """Send message to AI and get response string."""
        try:
            if provider == "gemini":
                chat = client_data
                response = chat.send_message(user_input)
                return response.text
                
            elif provider == "openai":
                client, model, messages = client_data
                messages.append({"role": "user", "content": user_input})
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                )
                reply = response.choices[0].message.content
                messages.append({"role": "assistant", "content": reply})
                return reply
                
            elif provider == "claude":
                client, model, messages, system_prompt = client_data
                messages.append({"role": "user", "content": user_input})
                response = client.messages.create(
                    model=model,
                    system=system_prompt,
                    messages=messages,
                    max_tokens=4096
                )
                reply = response.content[0].text
                messages.append({"role": "assistant", "content": reply})
                return reply
                
            elif provider == "ollama":
                ollama_url, model, messages = client_data
                import requests
                messages.append({"role": "user", "content": user_input})
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False
                }
                r = requests.post(f"{ollama_url}/api/chat", json=payload)
                reply = r.json()["message"]["content"]
                messages.append({"role": "assistant", "content": reply})
                return reply
                
        except Exception as e:
            error(f"AI API Error: {e}")
            return None

    def _execute_tool(self, tool_call: dict) -> str:
        """Execute an IoTwizz module and capture its output."""
        module_path = tool_call.get("module_path")
        options = tool_call.get("options", {})
        
        module = self.loader.get_module(module_path)
        if not module:
            return f"Error: Module '{module_path}' not found."
            
        # Set options
        for k, v in options.items():
            module.set_option(k, str(v))
            
        # Validate
        missing = module.validate()
        if missing:
            return f"Error: Module '{module_path}' missing required options: {', '.join(missing)}"
            
        console.print(f"\n[bold magenta]⚡ AiWizz is running module:[/bold magenta] [cyan]{module_path}[/cyan]")
        for k, v in options.items():
            console.print(f"   [dim]SET {k} = {v}[/dim]")
            
        # Capture stdout using sys.stdout redirection (Rich handles this well enough usually, 
        # but to be safe we'll use a string buffer for standard prints inside the module)
        output_buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        # Try to run
        try:
            module.run()
            output = output_buffer.getvalue()
        except Exception as e:
            output = f"Module execution threw an error: {str(e)}"
        finally:
            sys.stdout = old_stdout
            
        # Print the output to the user too so they see what happened
        console.print("\n[bold magenta]⚡ AiWizz Tool Output:[/bold magenta]")
        console.print(output)
        
        return f"Tool Execution Output:\n{output}"

    def _parse_ai_action(self, text: str) -> dict:
        """Attempt to parse the AI output as a JSON tool execution block."""
        text = text.strip()
        
        # Try to extract JSON from markdown blocks
        if text.startswith("```json") and text.endswith("```"):
            text = text[7:-3].strip()
        elif text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()
            
        try:
            parsed = json.loads(text)
            if "tool_call" in parsed and "module_path" in parsed["tool_call"]:
                return parsed
        except json.JSONDecodeError:
            pass
            
        return None

    def run(self):
        """Start the interactive AI Wizz session."""
        provider = self.get_option("PROVIDER").lower()
        api_key = self.get_option("API_KEY")
        model = self.get_option("MODEL")
        ollama_url = self.get_option("OLLAMA_URL")
        
        if provider != "ollama" and not api_key:
            warning(f"No API key provided for {provider}. Checking environment variables...")

        info("Initializing AI Wizz Mode...")

        # Late binding to avoid recursion
        self.loader = ModuleLoader()
        self.available_tools = self._get_module_descriptions()

        client_data, active_provider = self._init_ai_client(provider, api_key, model, ollama_url)
        
        if not client_data:
            return

        success(f"AiWizz connected to [bold]{active_provider}[/bold] using model [cyan]{model}[/cyan]")
        console.print("\n[bold magenta]🤖 AiWizz Chat Started[/bold magenta]")
        console.print("[dim]Type 'exit' to leave Wizz Mode, or ask me anything about IoT pentesting.[/dim]\n")

        session = PromptSession(history=InMemoryHistory())
        
        while True:
            try:
                user_msg = session.prompt(ANSI("\033[38;5;201mYou\033[0m > ")).strip()
                if not user_msg:
                    continue
                    
                if user_msg.lower() in ["exit", "quit", "back"]:
                    break
                    
                console.print("[dim]thinking...[/dim]", end="\r")
                
                # Send to AI
                ai_reply = self._get_ai_response(client_data, active_provider, user_msg)
                
                if not ai_reply:
                    continue
                    
                # Clear thinking text
                print(" " * 20, end="\r")
                
                # Check if AI wants to run a tool
                action = self._parse_ai_action(ai_reply)
                
                if action:
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > [dim]{action.get('thought', 'Decided to run a tool.')}[/dim]")
                    # Execute tool
                    tool_output = self._execute_tool(action["tool_call"])
                    
                    # Feed results back to AI immediately without user input
                    console.print("[dim]analyzing results...[/dim]", end="\r")
                    feedback_msg = f"The tool successfully completed. Analyze the following tool output and inform the user of what it means:\n\n{tool_output}"
                    
                    final_reply = self._get_ai_response(client_data, active_provider, feedback_msg)
                    print(" " * 20, end="\r")
                    if final_reply:
                        console.print(f"[bold magenta]AiWizz[/bold magenta] > {final_reply}\n")
                else:
                    # Normal conversational response
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > {ai_reply}\n")

            except KeyboardInterrupt:
                console.print()
                break
            except EOFError:
                break
                
        info("Exiting AI Wizz Mode")
