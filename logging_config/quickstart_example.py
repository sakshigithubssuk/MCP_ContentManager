"""
Quick Start Example - Using the Journey Logger

This example demonstrates the REAL, CORRECT flow
using a hardcoded query and hardcoded response.

There is NO simulated error here.
If this works, your main() will work.
"""

import time
from journey_logger import get_journey_logger
from logger_utils import LogAnalyzer


def example_journey_simulation():
    """
    Simulate a complete successful query journey.
    """

    print("\n" + "=" * 80)
    print("JOURNEY LOGGER - QUICK START EXAMPLE (SUCCESS FLOW)")
    print("=" * 80 + "\n")

    logger = get_journey_logger()

    # Hardcoded user query
    user_query = "Show me all active leave policies for Q1 2026"

    # ----------------------------
    # START JOURNEY
    # ----------------------------
    journey_id = logger.start_journey(user_query)
    time.sleep(0.5)

    # ----------------------------
    # STAGE 1: INTENT DETECTION
    # ----------------------------
    print("⏳ Intent detection...")
    time.sleep(0.5)

    intent = "SEARCH"
    logger.log_intent_detection(
        journey_id=journey_id,
        intent=intent,
        confidence=0.95
    )

    # ----------------------------
    # STAGE 2: RAG RETRIEVAL
    # ----------------------------
    print("⏳ RAG retrieval...")
    time.sleep(0.5)

    retrieved_docs = [
        "Leave_Policy_Q1_2026.pdf",
        "HR_Guidelines_Active.md",
        "Employee_Benefits.txt"
    ]

    logger.log_rag_retrieval(
        journey_id=journey_id,
        query=user_query,
        retrieved_docs=retrieved_docs,
        retrieval_time=0.834
    )

    # ----------------------------
    # STAGE 3: ACTION PLAN
    # ----------------------------
    print("⏳ Action plan generation...")
    time.sleep(0.5)

    action_plan = {
        "path": "Record/",
        "method": "GET",
        "parameters": {
            "q": "active leave policies Q1 2026",
            "format": "json",
            "properties": "NameString"
        },
        "operation": "SEARCH"
    }

    logger.log_action_plan(
        journey_id=journey_id,
        action_plan=action_plan,
        generation_time=1.234
    )

    # ----------------------------
    # STAGE 4: TOOL EXECUTION
    # ----------------------------
    print("⏳ Tool execution...")
    time.sleep(0.5)

    logger.log_tool_execution_start(
        journey_id=journey_id,
        tool_name="search_records",
        arguments={"action_plan": action_plan}
    )

    time.sleep(1.5)

    search_results = {
        "records_found": 3,
        "records": [
            {"id": "REC-001", "title": "Q1 Leave Policy 2026"},
            {"id": "REC-002", "title": "Q1 Updated Guidelines"},
            {"id": "REC-003", "title": "Q1 Holiday Calendar"}
        ]
    }

    logger.log_tool_execution_result(
        journey_id=journey_id,
        tool_name="search_records",
        result=search_results,
        execution_time=1.523,
        success=True
    )

    # ----------------------------
    # STAGE 5: JOURNEY COMPLETION
    # ----------------------------
    print("⏳ Journey completion...")
    time.sleep(0.5)

    final_response = {
        "message": "Found 3 active leave policies for Q1 2026",
        "data": search_results
    }

    logger.log_journey_completion(
        journey_id=journey_id,
        final_response=final_response,
        total_time=5.0,
        success=True
    )

    print("\n" + "=" * 80)
    print("JOURNEY COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"✅ Journey ID: {journey_id}")
    print("📁 Check logs/ directory\n")

    return journey_id


def example_view_logs():
    """
    View and analyze logs.
    """

    print("\n" + "=" * 80)
    print("VIEWING LOGS")
    print("=" * 80 + "\n")

    analyzer = LogAnalyzer()
    analyzer.print_journey_summary(limit=5)

    journeys = analyzer.get_all_journeys()
    if journeys:
        analyzer.print_journey_details(journeys[0]["journey_id"])


def main():
    journey_id = example_journey_simulation()
    example_view_logs()

    print("\n" + "=" * 80)
    print("QUICK START COMPLETE!")
    print("=" * 80)
    print(f"View journey:\npython logger_utils.py show {journey_id}\n")


if __name__ == "__main__":
    main()
