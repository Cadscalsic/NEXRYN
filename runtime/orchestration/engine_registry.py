# ============================================
# NEXRYN ENGINE REGISTRY
# ============================================

class EngineRegistry:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.engines = {}

    # ========================================
    # REGISTER ENGINE
    # ========================================

    def register(

        self,

        engine_name,

        engine_instance,

        metadata=None
    ):

        if metadata is None:

            metadata = {}

        self.engines[engine_name] = {

            "instance":
            engine_instance,

            "metadata":
            metadata
        }

    # ========================================
    # GET ENGINE
    # ========================================

    def get_engine(

        self,

        engine_name
    ):

        engine = self.engines.get(
            engine_name
        )

        if engine is None:

            return None

        return engine["instance"]

    # ========================================
    # GET METADATA
    # ========================================

    def get_metadata(

        self,

        engine_name
    ):

        engine = self.engines.get(
            engine_name
        )

        if engine is None:

            return {}

        return engine["metadata"]

    # ========================================
    # LIST ENGINES
    # ========================================

    def list_engines(self):

        return list(
            self.engines.keys()
        )

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "registered_engines":

            self.list_engines(),

            "engine_count":

            len(self.engines)
        }