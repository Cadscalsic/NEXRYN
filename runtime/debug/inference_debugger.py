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

        inference_report,

        transformation_concept_discovery_report=None
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

        if transformation_concept_discovery_report:

            print("\nTRANSFORMATION CONCEPT DISCOVERY:\n")

            print(transformation_concept_discovery_report)

        print("\nSEMANTIC ABSTRACTIONS:\n")

        for abstraction in semantic_abstractions:

            print(abstraction)

        print("\nSEMANTIC GRAPH:\n")

        print(semantic_graph)

        transformation_causal_graph = {}

        if isinstance(
            semantic_graph,
            dict
        ):

            transformation_causal_graph = semantic_graph.get(
                "transformation_causal_graph",
                {}
            )

        if transformation_causal_graph:

            print("\nTRANSFORMATION CAUSAL GRAPH:\n")

            print(transformation_causal_graph)

            print("\nCAUSAL CHAINS:\n")

            for chain in transformation_causal_graph.get(
                "causal_chains",
                []
            ):

                print(chain)

            print("\nCAUSAL RELATIONS:\n")

            for relation in transformation_causal_graph.get(
                "edges",
                []
            ):

                print(relation)

        print("\nSEARCH RESULT:\n")

        print(search_result)

        print("\nSYNTHESIZED PROGRAM:\n")

        print(synthesized_program)

        print("\nEXECUTION PLAN:\n")

        print(execution_plan)

        print("\nINFERENCE REPORT:\n")

        print(inference_report)
