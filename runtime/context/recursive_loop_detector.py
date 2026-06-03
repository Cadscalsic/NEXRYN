# ============================================
# NEXRYN RECURSIVE LOOP DETECTOR
# ============================================

from datetime import datetime
import uuid


# ============================================
# RECURSIVE LOOP DETECTOR
# ============================================

class RecursiveLoopDetector:

    # ========================================
    # INITIALIZE DETECTOR
    # ========================================

    def __init__(self):

        # ====================================
        # LOOP MEMORY
        # ====================================

        self.loop_memory = []

        # ====================================
        # DETECTED LOOPS
        # ====================================

        self.detected_loops = []

        # ====================================
        # DETECTOR STATE
        # ====================================

        self.detector_state = {

            "detector_mode":
            "adaptive_recursive_loop_detection",

            "pattern_tracking":
            True,

            "recursive_analysis":
            True,

            "cycle_detection":
            True,

            "runtime_stability":
            "stable",

            "detection_cycles":
            0
        }

        # ====================================
        # LOOP LIMITS
        # ====================================

        self.loop_limits = {

            "reasoning":
            4,

            "planning":
            3,

            "reflection":
            3,

            "meta":
            2,

            "execution":
            5
        }

    # ========================================
    # NORMALIZE DOMAIN
    # ========================================

    def normalize_domain(

        self,

        domain
    ):

        if domain is None:

            domain = "reasoning"

        if not isinstance(
            domain,
            str
        ):

            domain = str(domain)

        return domain.lower()

    # ========================================
    # REGISTER TRACE
    # ========================================

    def register_trace(

        self,

        domain,

        operation
    ):

        domain = self.normalize_domain(
            domain
        )

        trace = {

            "trace_id":
            str(uuid.uuid4()),

            "domain":
            domain,

            "operation":
            operation,

            "timestamp":
            str(datetime.utcnow())
        }

        self.loop_memory.append(
            trace
        )

        # ====================================
        # MEMORY LIMIT
        # ====================================

        if len(self.loop_memory) > 200:

            self.loop_memory = (
                self.loop_memory[-200:]
            )

        return trace

    # ========================================
    # GET DOMAIN TRACES
    # ========================================

    def get_domain_traces(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        traces = []

        for trace in self.loop_memory:

            if trace.get(
                "domain"
            ) == domain:

                traces.append(trace)

        return traces

    # ========================================
    # DETECT LOOP
    # ========================================

    def detect_loop(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        traces = self.get_domain_traces(
            domain
        )

        operations = []

        for trace in traces:

            operations.append(

                trace.get(
                    "operation"
                )
            )

        # ====================================
        # LOOP COUNT
        # ====================================

        repeated_operations = {}

        for operation in operations:

            repeated_operations[
                operation
            ] = repeated_operations.get(
                operation,
                0
            ) + 1

        # ====================================
        # DETECT REPETITION
        # ====================================

        for operation, count in (

            repeated_operations.items()
        ):

            limit = self.loop_limits.get(
                domain,
                3
            )

            if count >= limit:

                loop_event = {

                    "loop_id":
                    str(uuid.uuid4()),

                    "domain":
                    domain,

                    "operation":
                    operation,

                    "repeat_count":
                    count,

                    "loop_limit":
                    limit,

                    "loop_state":
                    "detected",

                    "timestamp":
                    str(datetime.utcnow())
                }

                self.detected_loops.append(
                    loop_event
                )

                return {

                    "loop_detected":
                    True,

                    "loop_event":
                    loop_event
                }

        return {

            "loop_detected":
            False
        }

    # ========================================
    # CLEAR DOMAIN MEMORY
    # ========================================

    def clear_domain_memory(

        self,

        domain
    ):

        domain = self.normalize_domain(
            domain
        )

        retained_memory = []

        for trace in self.loop_memory:

            if trace.get(
                "domain"
            ) != domain:

                retained_memory.append(
                    trace
                )

        self.loop_memory = retained_memory

        return True

    # ========================================
    # COMPUTE LOOP PRESSURE
    # ========================================

    def compute_loop_pressure(self):

        loop_count = len(
            self.detected_loops
        )

        if loop_count <= 2:

            pressure = "low"

        elif loop_count <= 5:

            pressure = "moderate"

        else:

            pressure = "high"

        return {

            "loop_count":
            loop_count,

            "pressure":
            pressure
        }

    # ========================================
    # RUN DETECTION CYCLE
    # ========================================

    def run_detection_cycle(

        self,

        domain,

        operation
    ):

        # ====================================
        # REGISTER TRACE
        # ====================================

        trace = self.register_trace(

            domain,

            operation
        )

        # ====================================
        # DETECT LOOP
        # ====================================

        detection = self.detect_loop(
            domain
        )

        # ====================================
        # UPDATE STATE
        # ====================================

        self.detector_state[
            "detection_cycles"
        ] += 1

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "trace":
            trace,

            "detection":
            detection,

            "loop_pressure":

            self.compute_loop_pressure(),

            "detector_state":
            self.detector_state,

            "timestamp":
            str(datetime.utcnow())
        }

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "detector_state":
            self.detector_state,

            "loop_memory":

            len(
                self.loop_memory
            ),

            "detected_loops":

            len(
                self.detected_loops
            ),

            "loop_pressure":

            self.compute_loop_pressure(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL RECURSIVE LOOP DETECTOR
# ============================================

recursive_loop_detector = (
    RecursiveLoopDetector()
)