import asyncio
from engine.fallback import FallbackEngine
from engine.retry import RetryEngine
import json
import re


class Orchestrator:
    def __init__(self, router, dispatcher, agents, emitter, memory, tool_registry):
        self.router = router
        self.dispatcher = dispatcher
        self.agents = agents
        self.retry = RetryEngine()
        self.emitter = emitter
        self.memory = memory
        self.registry = tool_registry
        self.fallback = FallbackEngine(self.agents.get("CHAT"))

    async def _emit_stats(self, task_id):
        stats = self.memory.get_stats()
        await self.emitter.emit(task_id, {
            "event": "stats_update",
            "data": {"stats": stats}
        })

    def _parse_string_tool_call(self, text):
        if not isinstance(text, str):
            return None

        pattern = r"(\w+)\s*\((.*?)\)"
        matches = re.findall(pattern, text, re.DOTALL)

        tool_calls = []

        for fn_name, raw_args in matches:
            args = {}

            arg_matches = re.findall(
                r'(\w+)\s*=\s*["\']?([^"\',\)]+?)["\']?',
                raw_args
            )

            for k, v in arg_matches:
                args[k] = v.strip()

            tool_calls.append({
                "function": {
                    "name": fn_name.strip(),
                    "arguments": json.dumps(args)
                }
            })

        return tool_calls if tool_calls else None

    def _execute_tool(self, fn_name, fn_args):
        """
        HARD TOOL EXECUTION GATE
        """
        try:
            result = self.registry.execute(fn_name, fn_args)

            # TOOL FAILURE CHECK
            if result is None:
                return {
                    "success": False,
                    "error": f"Tool returned None: {fn_name}",
                    "data": None
                }

            # already structured?
            if isinstance(result, dict) and "success" in result:
                return result

            return {
                "success": True,
                "error": None,
                "data": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def run(self, task, task_id):
        try:
            await self._emit_stats(task_id)

            past_context = self.memory.get_context(task)
            recent_history = self.memory.get_recent_history(limit=5)
            active_mem = self.memory.get_active_memory(task)
            learned_rules = active_mem.get("learned_rules", "")

            enriched_task = f"""
### RULES:
{learned_rules}

### HISTORY:
{recent_history}

### CONTEXT:
{past_context}

### TASK:
{task}
"""

            router_output = self.retry.run(
                self.router.run,
                enriched_task,
                tools=self.registry.get_tool_schemas()
            )

            dispatch_result = await self.dispatcher.run(
                router_output,
                enriched_task,
                task_id
            )

            tool_calls = dispatch_result.get("tool_calls")

            if not tool_calls:
                tool_calls = self._parse_string_tool_call(
                    dispatch_result.get("result", "")
                )

            tool_execution_result = None

            if tool_calls:
                for tool_call in tool_calls:
                    fn_name = tool_call["function"]["name"]
                    fn_args = json.loads(tool_call["function"]["arguments"])

                    await self.emitter.emit(task_id, {
                        "event": "thought",
                        "data": {
                            "thought": f"Tool çalıştırılıyor: {fn_name}",
                            "stage": "TOOL_EXECUTION"
                        }
                    })

                    tool_execution_result = self._execute_tool(fn_name, fn_args)

                    # ❌ HARD STOP: TOOL FAIL = NO CONTINUE
                    if not tool_execution_result["success"]:
                        final_answer = f"Tool hatası: {tool_execution_result['error']}"
                        self.memory.save_task_status(task, final_answer, "FAILURE")

                        await self.emitter.emit(task_id, {
                            "event": "final",
                            "data": {"answer": final_answer}
                        })
                        return

                    final_prompt = f"""
USER TASK: {task}

TOOL: {fn_name}
ARGUMENTS: {fn_args}
REAL RESULT: {tool_execution_result["data"]}

RULE:
- Only use REAL RESULT
- Do NOT hallucinate
- If result is empty, say "veri bulunamadı"
"""

                    dispatch_result["result"] = self.retry.run(
                        self.agents["CHAT"].run,
                        final_prompt
                    )

            final_answer = dispatch_result.get("result", "")

            # 🔥 HALÜSİNASYON KORUMASI
            if tool_calls and (
                final_answer is None or
                "requirements.txt" in final_answer and "flask" in final_answer.lower() is False
            ):
                final_answer = str(tool_execution_result.get("data", "Veri yok"))

            self.memory.save_interaction(task, final_answer)

            await self._emit_stats(task_id)

            await self.emitter.emit(task_id, {
                "event": "final",
                "data": {"answer": final_answer}
            })

            return dispatch_result

        except Exception as e:
            self.memory.save_task_status(task, "Hata", "FAILURE", str(e))

            fallback_answer = self.fallback.run(task)

            await self.emitter.emit(task_id, {
                "event": "final",
                "data": {"answer": fallback_answer}
            })

            print(f"[ORCHESTRATOR ERROR] {e}")