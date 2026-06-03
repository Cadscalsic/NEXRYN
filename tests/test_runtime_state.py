from runtime.state.runtime_state import RuntimeState

state = RuntimeState()

print(

    RuntimeState.update_context
    .__code__.co_varnames
)

state.start()

state.set_stage(
    "pattern_analysis"
)

state.set_active_engine(
    "pattern_engine"
)

state.update_context(

    "test",

    {},

    priority="high"
)

print(state.summary())