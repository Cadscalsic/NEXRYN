# ============================================
# NEXRYN INFERENCE DEBUGGER
# ============================================

class InferenceDebugger:

    # ============================================
    # DISPLAY RESULTS
    # ============================================

    def display(

        self,

        hypotheses,

        control_state,

        recursive_report,

        arbitration_report,

        semantic_abstractions,

        semantic_graph,

        search_result,

        synthesized_program,

        execution_plan,

        inference_report
    ):

        print("\nINFERENCE HYPOTHESES:\n")

        for hypothesis in hypotheses:

            print(hypothesis)

        print("\nMETA CONTROLLER:\n")

        print(control_state)

        print("\nRECURSIVE REPORT:\n")

        print(recursive_report)

        print("\nGOAL ARBITRATION:\n")

        print(arbitration_report)

        print("\nSEMANTIC ABSTRACTIONS:\n")

        for abstraction in semantic_abstractions:

            print(abstraction)

        print("\nSEMANTIC GRAPH:\n")

        print(semantic_graph)

        print("\nSEARCH RESULT:\n")

        print(search_result)

        print("\nSYNTHESIZED PROGRAM:\n")

        print(synthesized_program)

        print("\nEXECUTION PLAN:\n")

        print(execution_plan)

        print("\nINFERENCE REPORT:\n")

        print(inference_report)