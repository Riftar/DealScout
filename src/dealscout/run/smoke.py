"""Setup check: each configured model can call a tool, and the calls reach neatlogs.

Run with `uv run python -m dealscout.run.smoke`.
"""

import os
import sys
import time

import neatlogs
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def price_per_m2(price_rp: int, land_m2: float) -> float:
    """Asking price per square metre of land."""
    return price_rp / land_m2


def check_model(model_name: str, handler) -> bool:
    model = ChatOpenAI(
        model=model_name,
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        temperature=0,
        timeout=120,
    ).bind_tools([price_per_m2])
    started = time.perf_counter()
    reply = model.invoke(
        "A house is listed at Rp 1,500,000,000 on 100 m2 of land. "
        "Use the tool to get the price per m2.",
        config={"callbacks": [handler]},
    )
    seconds = time.perf_counter() - started
    calls = reply.tool_calls
    ok = bool(calls) and calls[0]["name"] == "price_per_m2"
    print(f"{model_name}: tool call {'ok' if ok else 'MISSING'} in {seconds:.1f}s {calls[0]['args'] if ok else ''}")
    return ok


def main() -> int:
    load_dotenv(".env")
    neatlogs.init(api_key=os.environ["NEATLOGS_API_KEY"], workflow_name="dealscout-smoke")
    handler = neatlogs.langchain_handler()
    results = []
    with neatlogs.trace("smoke", kind="WORKFLOW"):
        for name in dict.fromkeys([os.environ["LLM_MODEL_FAST"], os.environ["LLM_MODEL_STRONG"]]):
            try:
                results.append(check_model(name, handler))
            except Exception as error:  # report every model, then fail
                print(f"{name}: FAILED {type(error).__name__}: {error}")
                results.append(False)
    print("neatlogs flush:", "ok" if neatlogs.flush() else "FAILED")
    neatlogs.shutdown()
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
