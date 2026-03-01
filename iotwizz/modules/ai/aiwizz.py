"""
IoTwizz Module: AiWizz - AI Hacking Assistant
An intelligent AI assistant deeply integrated with IoTwizz modules.
Can analyze targets, recommend modules, execute chains of operations,
and provide expert guidance on IoT security testing.
"""

import os
import sys
import json
import time
import re
from typing import Optional, List, Dict, Any
from io import StringIO
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from iotwizz.base_module import BaseModule
from iotwizz.utils.colors import success, error, warning, info, result, console, print_separator, print_table
from iotwizz.module_loader import ModuleLoader


class AiWizz(BaseModule):
    """AI-powered IoT security assistant with deep framework integration."""

    # Module descriptions for AI context
    MODULE_CONTEXT = """
Available IoTwizz modules for IoT security testing:

RECONNAISSANCE:
- uart/baud_rate_finder: Auto-detect UART baud rates for serial communication
- recon/default_creds: Test IoT devices for default credentials (SSH, Telnet, HTTP, FTP)
- wireless/ble_scanner: Discover and enumerate Bluetooth Low Energy devices

FIRMWARE ANALYSIS:
- firmware/binwalk_analyzer: Extract and analyze firmware images, find secrets

HARDWARE HACKING:
- hardware/jtag_swd_scanner: Detect JTAG/SWD debug interfaces on circuit boards
- hardware/spi_flash_dumper: Extract firmware directly from SPI flash chips
- exploit/uboot_breaker: Intercept U-Boot bootloader to gain shell access

PROTOCOL TESTING:
- protocol/mqtt_fuzzer: Fuzz MQTT brokers for vulnerabilities
- protocol/coap_fuzzer: Test CoAP endpoints for parsing issues and DoS

WIRELESS SECURITY:
- wireless/ble_scanner: BLE device discovery and service enumeration
- wireless/zigbee_sniffer: Capture and analyze Zigbee/802.15.4 packets
"""

    def __init__(self):
        super().__init__()
        self.name = "AiWizz - AI Security Assistant"
        self.description = "Intelligent AI assistant for IoT pentesting with framework integration"
        self.author = "IoTwizz Team"
        self.category = "ai"

        # Avoid loading AI modules to prevent recursion
        self.loader = None
        self.modules = None
        self.available_tools = ""
        
        # Session state
        self.conversation_history = []
        self.session_context = {}
        self.executed_modules = []
        self.findings = []

        self.options = {
            "PROVIDER": {
                "value": "gemini",
                "required": True,
                "description": "AI Provider (gemini, openai, claude, ollama, deepseek, minimax)",
            },
            "API_KEY": {
                "value": "",
                "required": False,
                "description": "API Key (or set AIWIZZ_API_KEY env var)",
            },
            "MODEL": {
                "value": "",
                "required": False,
                "description": "Model name (auto-selected if empty)",
            },
            "BASE_URL": {
                "value": "",
                "required": False,
                "description": "Custom API endpoint URL",
            },
            "TEMPERATURE": {
                "value": "0.7",
                "required": False,
                "description": "AI creativity level (0.0-1.0, default: 0.7)",
            },
            "MAX_TOKENS": {
                "value": "4096",
                "required": False,
                "description": "Maximum response length (default: 4096)",
            },
            "SYSTEM_PROMPT": {
                "value": "",
                "required": False,
                "description": "Custom system prompt (uses default if empty)",
            },
        }

    def _get_default_model(self, provider: str) -> str:
        """Get default model for a provider."""
        defaults = {
            "gemini": "gemini-2.0-flash",
            "openai": "gpt-4o",
            "claude": "claude-sonnet-4-20250514",
            "ollama": "llama3",
            "deepseek": "deepseek-chat",
            "minimax": "minimax-m2-100k",
        }
        return defaults.get(provider, "gemini-2.0-flash")

    def _get_module_descriptions(self) -> str:
        """Get detailed module descriptions."""
        if self.available_tools:
            return self.available_tools
            
        modules_info = {}
        modules_dict = self.modules or (self.loader.get_all_modules() if self.loader else {})
        
        for path, mod in modules_dict.items():
            if mod.category == "ai" or mod._is_stub:
                continue

            mod_options = {}
            for opt_name, opt_data in mod.options.items():
                mod_options[opt_name] = {
                    "required": opt_data.get("required", False),
                    "description": opt_data.get("description", ""),
                    "default": opt_data.get("value", ""),
                }

            modules_info[path] = {
                "name": mod.name,
                "description": mod.description,
                "category": mod.category,
                "options": mod_options
            }

        self.available_tools = json.dumps(modules_info, indent=2)
        return self.available_tools

    def _get_system_prompt(self) -> str:
        """Build the system prompt for the AI."""
        custom_prompt = self.get_option("SYSTEM_PROMPT")
        if custom_prompt:
            return custom_prompt

        return f"""You are AiWizz, an elite AI security assistant integrated into the IoTwizz IoT pentesting framework. You are NOT a chatbot — you are an active participant in security testing.

## Your Identity
You are a sophisticated security research AI with deep expertise in:
- IoT device security and embedded systems
- Hardware hacking (UART, JTAG, SPI, firmware extraction)
- Wireless protocols (BLE, Zigbee, MQTT, CoAP)
- Network penetration testing and protocol analysis
- Firmware reverse engineering and vulnerability research

## Your Capabilities
You have DIRECT ACCESS to IoTwizz's security modules. When the user asks you to do something, you can EXECUTE modules on their behalf.

## Tool Execution Format
When you need to run a module, respond with a JSON block like this:
```json
{{
  "action": "run_module",
  "module": "category/module_name",
  "options": {{
    "TARGET": "192.168.1.1",
    "PORT": "22"
  }},
  "reasoning": "Brief explanation of why this module"
}}
```

For complex operations requiring multiple modules:
```json
{{
  "action": "chain_modules",
  "modules": [
    {{
      "module": "recon/default_creds",
      "options": {{"TARGET": "192.168.1.1", "SERVICE": "ssh"}}
    }},
    {{
      "module": "protocol/mqtt_fuzzer",
      "options": {{"HOST": "192.168.1.1", "COUNT": "50"}}
    }}
  ],
  "reasoning": "Testing default creds then fuzzing MQTT"
}}
```

For providing guidance without execution:
```json
{{
  "action": "guide",
  "message": "Your explanation here...",
  "recommended_modules": ["module/path"],
  "next_steps": ["Step 1", "Step 2"]
}}
```

## Available Modules
{self._get_module_descriptions()}

## Your Behavior
1. Be PROACTIVE — if a user mentions a target or device, suggest relevant modules
2. Be INTELLIGENT — analyze results from executed modules and suggest next steps
3. Be PRECISE — use exact module paths and option names
4. Be HELPFUL — explain what you're doing and why
5. Be SECURITY-FOCUSED — always consider the ethical implications

## Context Awareness
- Remember findings from previous module executions
- Build on discovered information
- Suggest logical attack chains
- Track what's been tried and what hasn't

## Response Style
- Be concise but thorough
- Use markdown formatting for clarity
- Show confidence levels when uncertain
- Provide alternative approaches when primary fails
- Celebrate discoveries and flag security issues

## Important Rules
- NEVER make up module names or options
- ALWAYS use valid module paths from the available modules list
- If uncertain about an option, ask the user
- If a module fails, explain why and suggest alternatives
- Always validate that options are correctly formatted
"""

    def _init_client(self, provider: str, api_key: str, model: str, base_url: str):
        """Initialize the AI client for the specified provider."""
        temperature = self.get_option_float("TEMPERATURE", default=0.7)
        
        # Check environment variable for API key
        if not api_key:
            api_key = os.environ.get("AIWIZZ_API_KEY", os.environ.get(f"{provider.upper()}_API_KEY", ""))
        
        if provider == "gemini":
            try:
                import google.generativeai as genai
                if api_key:
                    genai.configure(api_key=api_key)
                
                client = genai.GenerativeModel(
                    model_name=model or self._get_default_model("gemini"),
                    system_instruction=self._get_system_prompt(),
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=self.get_option_int("MAX_TOKENS", default=4096),
                    )
                )
                return client.start_chat(history=[]), "gemini"
            except ImportError:
                error("google-generativeai not installed")
                info("Install with: pip install google-generativeai")
                info("Get your API key from: https://makersuite.google.com/app/apikey")
                return None, None

        elif provider in ["openai", "deepseek", "minimax", "custom"]:
            try:
                from openai import OpenAI
                
                # Set default base URLs
                default_urls = {
                    "deepseek": "https://api.deepseek.com/v1",
                    "minimax": "https://api.minimax.chat/v1",
                    "openai": "https://api.openai.com/v1",
                }
                
                client_args = {"api_key": api_key or "sk-dummy"}
                if base_url:
                    client_args["base_url"] = base_url
                elif provider in default_urls:
                    client_args["base_url"] = default_urls[provider]
                
                client = OpenAI(**client_args)
                return (client, model or self._get_default_model(provider), [{"role": "system", "content": self._get_system_prompt()}]), provider
                
            except ImportError:
                error("openai not installed")
                info("Install with: pip install openai")
                if provider == "openai":
                    info("Get your API key from: https://platform.openai.com/api-keys")
                elif provider == "deepseek":
                    info("Get your API key from: https://platform.deepseek.com")
                elif provider == "minimax":
                    info("Get your API key from: https://api.minimax.chat")
                return None, None

        elif provider == "claude":
            try:
                import anthropic
                
                client = anthropic.Anthropic(api_key=api_key)
                return (client, model or self._get_default_model("claude"), self._get_system_prompt()), "claude"
                
            except ImportError:
                error("anthropic not installed")
                info("Install with: pip install anthropic")
                info("Get your API key from: https://console.anthropic.com")
                return None, None

        elif provider == "ollama":
            try:
                from openai import OpenAI
                
                client = OpenAI(
                    base_url=base_url if base_url else "http://localhost:11434/v1",
                    api_key="ollama",  # Ollama doesn't need a real key
                )
                return (client, model or self._get_default_model("ollama"), [{"role": "system", "content": self._get_system_prompt()}]), "ollama"
                
            except ImportError:
                error("openai not installed for Ollama")
                info("Install with: pip install openai")
                info("Ollama uses OpenAI-compatible API")
                return None, None

        else:
            error(f"Unknown provider: {provider}")
            info("Supported providers: gemini, openai, claude, ollama, deepseek, minimax")
            return None, None

    def _send_message(self, client_data, provider: str, message: str) -> str:
        """Send a message to the AI and get a response."""
        temperature = self.get_option_float("TEMPERATURE", default=0.7)
        max_tokens = self.get_option_int("MAX_TOKENS", default=4096)
        
        try:
            if provider == "gemini":
                client, chat = client_data
                response = chat.send_message(message)
                return response.text

            elif provider == "claude":
                client, model, system = client_data
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text

            else:  # OpenAI-compatible providers
                client, model, messages = client_data
                messages.append({"role": "user", "content": message})
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                reply = response.choices[0].message.content
                messages.append({"role": "assistant", "content": reply})
                return reply

        except Exception as e:
            error(f"AI API error: {e}")
            return ""

    def _parse_ai_response(self, response: str) -> dict:
        """Parse the AI response for actions."""
        response = response.strip()
        
        # Try to find JSON blocks
        json_patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match.strip() if isinstance(match, str) else match)
                    if isinstance(data, dict) and "action" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        
        # No action found - it's a conversational response
        return {"action": "converse", "message": response}

    def _execute_module(self, module_path: str, options: dict) -> str:
        """Execute a module and capture output."""
        if not self.loader:
            return "Error: Module loader not initialized"
        
        module = self.loader.get_module(module_path)
        if not module:
            # Try partial match
            matches = self.loader.search_modules(module_path)
            if len(matches) == 1:
                module_path = list(matches.keys())[0]
                module = matches[module_path]
            else:
                return f"Error: Module '{module_path}' not found"
        
        # Set options
        for key, value in options.items():
            if not module.set_option(key, str(value)):
                return f"Error: Unknown option '{key}' for module '{module_path}'"
        
        # Validate required options
        missing = module.validate()
        if missing:
            return f"Error: Module '{module_path}' missing required options: {', '.join(missing)}"
        
        # Execute and capture output
        console.print()
        console.print("[bold magenta]⚡ AiWizz executing:[/bold magenta] [cyan]" + module_path + "[/cyan]")
        for key, value in options.items():
            console.print(f"   [dim]SET {key} = {value}[/dim]")
        console.print()
        
        # Capture stdout
        output_buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        result_data = {"success": False, "output": "", "error": None}
        
        try:
            module.run()
            result_data["success"] = True
            result_data["output"] = output_buffer.getvalue()
        except KeyboardInterrupt:
            result_data["error"] = "Module interrupted by user"
        except Exception as e:
            result_data["error"] = str(e)
        finally:
            sys.stdout = old_stdout
        
        # Record execution
        self.executed_modules.append({
            "module": module_path,
            "options": options,
            "result": result_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Build result message for AI
        result_msg = f"Module: {module_path}\n"
        result_msg += f"Success: {result_data['success']}\n"
        if result_data["error"]:
            result_msg += f"Error: {result_data['error']}\n"
        result_msg += f"Output:\n{result_data['output'][:4000]}"  # Limit output
        
        return result_msg

    def _execute_chain(self, modules: List[dict]) -> str:
        """Execute a chain of modules."""
        results = []
        for i, mod in enumerate(modules, 1):
            console.print(f"[bold yellow]Chain step {i}/{len(modules)}[/bold yellow]")
            result = self._execute_module(mod["module"], mod.get("options", {}))
            results.append(f"Step {i}: {result}")
            console.print()
        return "\n\n".join(results)

    def run(self):
        """Run the interactive AiWizz session."""
        provider = self.get_option("PROVIDER").lower()
        api_key = self.get_option("API_KEY")
        model = self.get_option("MODEL")
        base_url = self.get_option("BASE_URL")

        # Initialize module loader
        info("Initializing IoTwizz modules...")
        self.loader = ModuleLoader()
        self.modules = {k: v for k, v in self.loader.modules.items() if not k.startswith('ai/')}
        success(f"Loaded {len(self.modules)} modules")

        # Initialize AI client
        info(f"Connecting to [cyan]{provider}[/cyan]...")
        client_data, active_provider = self._init_client(provider, api_key, model, base_url)
        
        if not client_data:
            return

        model_name = model or self._get_default_model(provider)
        success(f"AiWizz connected to [bold]{active_provider}[/bold] ([cyan]{model_name}[/cyan])")
        
        # Display welcome message
        console.print()
        console.print("[bold magenta]╔══════════════════════════════════════════════════════════════╗[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]  [bold white]🤖 AiWizz - AI Security Assistant[/bold white]                              [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]                                                              [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]  [dim]I have full access to IoTwizz modules and can execute[/dim]      [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]  [dim]security tests on your behalf. Just tell me what you[/dim]    [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]  [dim]need - I'll analyze, recommend, and act.[/dim]                  [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]                                                              [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]║[/bold magenta]  [cyan]Type 'help' for commands, 'exit' to quit[/cyan]                   [bold magenta]║[/bold magenta]")
        console.print("[bold magenta]╚══════════════════════════════════════════════════════════════╝[/bold magenta]")
        console.print()

        # Start interactive session
        session = PromptSession(history=InMemoryHistory())
        
        while True:
            try:
                user_input = session.prompt(
                    ANSI("\033[38;5;201mYou\033[0m > ")
                ).strip()
                
                if not user_input:
                    continue
                
                # Handle built-in commands
                if user_input.lower() in ["exit", "quit", "back"]:
                    break
                
                if user_input.lower() == "help":
                    self._show_help()
                    continue
                
                if user_input.lower() == "history":
                    self._show_history()
                    continue
                
                if user_input.lower() == "findings":
                    self._show_findings()
                    continue
                
                if user_input.lower() == "modules":
                    self._show_modules()
                    continue
                
                if user_input.lower().startswith("run "):
                    # Direct module execution
                    parts = user_input[4:].split(maxsplit=1)
                    if parts:
                        module_path = parts[0]
                        options = {}
                        if len(parts) > 1:
                            # Parse options like "TARGET=192.168.1.1 PORT=22"
                            for opt in parts[1].split():
                                if "=" in opt:
                                    k, v = opt.split("=", 1)
                                    options[k.upper()] = v
                        result = self._execute_module(module_path, options)
                        console.print(f"\n[dim]{result[:500]}...[/dim]\n")
                    continue
                
                # Send to AI
                console.print()
                with console.status("[bold magenta]AiWizz thinking...[/bold magenta]"):
                    # Build context message
                    context_msg = user_input
                    if self.executed_modules:
                        context_msg += f"\n\n[Previous executions in this session: {len(self.executed_modules)}]"
                    if self.findings:
                        context_msg += f"\n[Findings so far: {len(self.findings)}]"
                    
                    response = self._send_message(client_data, active_provider, context_msg)
                
                if not response:
                    error("No response from AI")
                    continue
                
                # Parse and execute AI's action
                action = self._parse_ai_response(response)
                
                if action["action"] == "run_module":
                    # Execute a single module
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > I'll run {action['module']} for you...")
                    result = self._execute_module(action["module"], action.get("options", {}))
                    
                    # Feed result back to AI
                    with console.status("[bold magenta]Analyzing results...[/bold magenta]"):
                        follow_up = self._send_message(
                            client_data, active_provider,
                            f"The module completed. Here's the result:\n{result}\n\nWhat should we do next?"
                        )
                    console.print()
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > {follow_up}")
                
                elif action["action"] == "chain_modules":
                    # Execute a chain of modules
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > I'll execute a chain of {len(action['modules'])} modules...")
                    result = self._execute_chain(action["modules"])
                    
                    with console.status("[bold magenta]Analyzing chain results...[/bold magenta]"):
                        follow_up = self._send_message(
                            client_data, active_provider,
                            f"The chain completed. Results:\n{result}\n\nSummarize findings and suggest next steps."
                        )
                    console.print()
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > {follow_up}")
                
                elif action["action"] == "guide":
                    # Just provide guidance
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > {action['message']}")
                
                else:
                    # Conversational response
                    console.print(f"[bold magenta]AiWizz[/bold magenta] > {response}")
                
                console.print()
                
            except KeyboardInterrupt:
                console.print()
                continue
            except EOFError:
                break
            except Exception as e:
                error(f"Error: {e}")
                console.print()

        console.print()
        info("AiWizz session ended. Happy hacking!")

    def _show_help(self):
        """Show AiWizz help."""
        console.print()
        console.print("[bold cyan]AiWizz Commands:[/bold cyan]")
        console.print("  [white]help[/white]      - Show this help message")
        console.print("  [white]modules[/white]   - List available modules")
        console.print("  [white]history[/white]   - Show executed modules in this session")
        console.print("  [white]findings[/white]  - Show discovered findings")
        console.print("  [white]run <module> [options][/white] - Directly execute a module")
        console.print("  [white]exit[/white]      - Exit AiWizz")
        console.print()
        console.print("[bold cyan]Example prompts:[/bold cyan]")
        console.print("  [dim]• Scan 192.168.1.1 for default credentials[/dim]")
        console.print("  [dim]• Help me extract firmware from this device[/dim]")
        console.print("  [dim]• What's the best way to test this MQTT broker?[/dim]")
        console.print("  [dim]• Find the baud rate for /dev/ttyUSB0[/dim]")
        console.print("  [dim]• Analyze the results and suggest next steps[/dim]")
        console.print()

    def _show_history(self):
        """Show execution history."""
        if not self.executed_modules:
            info("No modules executed in this session yet")
            return
        
        console.print()
        console.print(f"[bold cyan]Execution History ({len(self.executed_modules)} modules):[/bold cyan]")
        for i, exec in enumerate(self.executed_modules, 1):
            status = "[green]✓[/green]" if exec["result"]["success"] else "[red]✗[/red]"
            console.print(f"  {i}. {status} [cyan]{exec['module']}[/cyan]")
            for k, v in exec["options"].items():
                console.print(f"       [dim]{k}={v}[/dim]")
        console.print()

    def _show_findings(self):
        """Show discovered findings."""
        if not self.findings:
            info("No findings recorded yet")
            return
        
        console.print()
        console.print(f"[bold cyan]Findings ({len(self.findings)}):[/bold cyan]")
        for i, finding in enumerate(self.findings, 1):
            console.print(f"  {i}. {finding}")
        console.print()

    def _show_modules(self):
        """Show available modules."""
        if not self.modules:
            info("No modules loaded")
            return
        
        console.print()
        columns = [
            ("Module", "cyan"),
            ("Description", "white"),
        ]
        rows = [(path, mod.description[:50]) for path, mod in sorted(self.modules.items())]
        print_table("Available Modules", columns, rows)
